from __future__ import annotations

import datetime
import logging
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd
from playwright.sync_api import sync_playwright, BrowserContext, Page

PM_URL = "https://pricingmonkey.com/b/ed392083-bb6d-4d8e-a664-206cb82b041c"
PROFILE_DIR = Path(__file__).parent / ".edge_profile"
LOGS_DIR = Path(__file__).parent / "logs"
TEST_OUTPUT_ROOT = Path(__file__).parent / "test_output"

MAX_DATA_WAIT_SEC = 240.0
POLL_INTERVAL_SEC = 0.5
KEY_PAUSE_SEC = 0.10
AFTER_SELECT_WAIT_SEC = 5.0
SLEEP_BETWEEN_RUNS_SEC = 1
QUICK_KEY_PAUSE_SEC = 0.02
QUICK_AFTER_SELECT_WAIT_SEC = 0.2

HEADERS = [
    "Bid", "Ask", "Price", "Trade Description", "Implied Vol (Daily BP)", "Bloomberg",
    "Strike", "Trade Amount", "DV01", "Underlying", "Biz Days", "Contract Notional",
    "Expiry Date", "NPV", "DV01 Gamma", "Theta", "% Delta", "Vega", "Underlying",
    "Sticky Delta Hedge Amount", "Underlying", "Atm Vol (Daily BP)", "Price in Basis Points",
    "Days", "Strike", "Gamma", "Delta Hedge Amount", "Implied Vol", "Trade Amount",
    "Expiry Breakeven", "Option Price - Intrinsic Price", "Vega P&L", "Vega (Daily BP)",
    "Intrinsic Price (Strike - Underlying * 32)", "Trade Price", "Implied Vol", "Atm Vol",
    "Bloomberg",
]


def setup_logger() -> logging.Logger:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")
    log_path = LOGS_DIR / f"pm_runner_1hz_{ts}.log"
    logger = logging.getLogger("pm_playwright_runner_1hz")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    if not logger.handlers:
        logger.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(sh)
    logger.info(f"Runner log: {log_path}")
    return logger


def launch_context(logger: logging.Logger) -> BrowserContext:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    p = sync_playwright().start()
    try:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            channel="msedge",
            headless=False,
            viewport={"width": 1400, "height": 900},
            args=[
                "--disable-infobars",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
                "--disable-features=CalculateNativeWinOcclusion",
            ],
        )
        ctx._playwright = p  # type: ignore[attr-defined]
        logger.info("Launched Edge with anti-throttling flags.")
        return ctx
    except Exception:
        p.stop()
        raise


def open_board(ctx: BrowserContext, logger: logging.Logger) -> Page:
    page = ctx.new_page()
    page.goto(PM_URL, wait_until="load")
    time.sleep(2)
    return page


def wait_for_data_ready(page: Page, logger: logging.Logger) -> None:
    start = time.time()
    deadline = start + MAX_DATA_WAIT_SEC
    logger.info("Waiting for data to populate (no 'Loading...' tokens)…")
    last_text: Optional[str] = None
    stable = 0
    while time.time() < deadline:
        try:
            body_text = page.evaluate("() => (document && document.body && document.body.innerText) || ''")
        except Exception:
            body_text = ""
        if ("Loading..." not in body_text) and (body_text.count("Comdty") >= 3):
            if last_text is not None and body_text == last_text:
                stable += 1
            else:
                stable = 0
                last_text = body_text
            if stable >= 1:
                logger.info(f"Data ready after {time.time() - start:.1f}s")
                return
        try:
            page.wait_for_load_state("networkidle", timeout=int(POLL_INTERVAL_SEC * 1000))
        except Exception:
            pass
        time.sleep(POLL_INTERVAL_SEC)
    logger.warning("Proceeding despite 'Loading...' still present after max wait")


def select_and_copy(page: Page, logger: logging.Logger) -> Optional[str]:
    # Full selection + copy (used on first cycle or fallback)
    try:
        page.keyboard.press("Escape")
        try:
            page.focus("body")
        except Exception:
            pass
        for _ in range(5):
            page.keyboard.press("Tab")
            time.sleep(KEY_PAUSE_SEC)
        page.keyboard.press("ArrowDown")
        time.sleep(KEY_PAUSE_SEC)
        page.keyboard.down("Control"); page.keyboard.down("Shift")
        page.keyboard.press("ArrowDown"); time.sleep(KEY_PAUSE_SEC)
        page.keyboard.press("ArrowRight"); time.sleep(KEY_PAUSE_SEC)
        page.keyboard.up("Shift"); page.keyboard.up("Control")
        time.sleep(AFTER_SELECT_WAIT_SEC)

        try:
            page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=PM_URL)
        except Exception:
            pass
        page.keyboard.press("Control+C")
        time.sleep(0.5)
        text = page.evaluate("async () => await navigator.clipboard.readText().catch(() => '')")
        if text:
            logger.info(f"Copied selection ({len(text)} chars).")
            return text
    except Exception as exc:
        logger.warning(f"Full select/copy failed: {exc}")
    return None


def quick_copy(page: Page, logger: logging.Logger) -> Optional[str]:
    # Only Ctrl+C and read clipboard; do not reselect or change focus.
    try:
        page.keyboard.press("Control+C")
        time.sleep(0.2)
        text = page.evaluate("async () => await navigator.clipboard.readText().catch(() => '')")
        if text:
            return text
    except Exception as exc:
        logger.warning(f"Quick copy failed: {exc}")
    return None


def parse_to_csv(text: str, logger: logging.Logger) -> Optional[Path]:
    rows = [r for r in text.splitlines() if r.strip()]
    if rows and rows[0].startswith("#") and rows[0].endswith("#"):
        rows = rows[1:]
    if not rows:
        logger.warning("No non-empty rows found; skipping CSV save.")
        return None
    if any("\t" in r for r in rows):
        data = [r.split("\t") for r in rows]
    else:
        data = [r.split() for r in rows]
    max_cols = max((len(r) for r in data), default=0)
    data = [r + ([""] * (max_cols - len(r))) for r in data]
    df = pd.DataFrame(data)
    if df.shape[1] == len(HEADERS):
        df.columns = HEADERS
    else:
        logger.warning(f"Header mismatch: parsed {df.shape[1]} cols vs expected {len(HEADERS)}; keeping numeric headers")

    now = datetime.datetime.now()
    out_dir = TEST_OUTPUT_ROOT / now.strftime("%m-%d-%Y")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"pmonkey_{now.strftime('%m%d%Y_%H-%M-%S')}.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"Saved CSV → {out_path} (rows={len(df)})")
    return out_path


def main() -> int:
    logger = setup_logger()
    ctx = launch_context(logger)
    try:
        page = open_board(ctx, logger)
        logger.info("If login is required, complete it in Edge and press Enter to continue…")
        try:
            input("")
        except Exception:
            time.sleep(10)
        cycle = 0
        quick_mode = False
        while True:
            cycle += 1
            t0 = time.time()
            logger.info(f"Cycle {cycle} start…")
            fell_back = False
            copied_len = 0
            if not quick_mode:
                wait_for_data_ready(page, logger)
                text = select_and_copy(page, logger)
                if text:
                    copied_len = len(text)
                    parse_to_csv(text, logger)
                    quick_mode = True
                else:
                    logger.warning("Full selection failed; will retry next cycle.")
            else:
                # Quick readiness probe (no networkidle)
                try:
                    body_text = page.evaluate("() => (document && document.body && document.body.innerText) || ''")
                except Exception:
                    body_text = ""
                if "Loading..." in body_text:
                    fell_back = True
                    wait_for_data_ready(page, logger)
                    text = select_and_copy(page, logger)
                else:
                    text = quick_copy(page, logger)
                    if not text:
                        fell_back = True
                        text = select_and_copy(page, logger)
                if text:
                    copied_len = len(text)
                    parse_to_csv(text, logger)
                else:
                    logger.warning("Quick+fallback copy failed; skipping this cycle.")
            elapsed = time.time() - t0
            logger.info(f"Cycle {cycle} done (quick_mode={quick_mode}, fell_back={fell_back}, copied={copied_len} chars, elapsed={elapsed*1000:.0f}ms)")
            # Maintain ~1 Hz cadence
            sleep_left = SLEEP_BETWEEN_RUNS_SEC - elapsed
            if sleep_left > 0:
                time.sleep(sleep_left)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received; exiting 1Hz runner.")
        return 0
    except Exception:
        logger.exception("Unexpected error in 1Hz runner")
        return 1
    finally:
        # keep window open for inspection
        pass


if __name__ == "__main__":
    sys.exit(main())