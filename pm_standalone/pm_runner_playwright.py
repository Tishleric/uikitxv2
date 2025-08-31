from __future__ import annotations

import datetime
import io
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
OUTPUT_ROOT = Path(r"Z:\Hanyu\FiveMinuteMonkey")

# Timing (development)
MAX_DATA_WAIT_SEC = 240.0
POLL_INTERVAL_SEC = 0.5
KEY_PAUSE_SEC = 0.10
AFTER_SELECT_WAIT_SEC = 5.0
SLEEP_BETWEEN_RUNS_SEC = 300
SELECT_DOWN_COUNT = 50  # number of rows to extend selection downward

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
    log_path = LOGS_DIR / f"pm_runner_{ts}.log"
    logger = logging.getLogger("pm_playwright_runner")
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
            args=["--disable-infobars"],
        )
        ctx._playwright = p  # type: ignore[attr-defined]
        logger.info("Launched Edge with persistent profile.")
        return ctx
    except Exception:
        p.stop()
        raise


def safe_close_context(ctx: BrowserContext) -> None:
    p = getattr(ctx, "_playwright", None)
    try:
        # Intentionally do NOT close the context to keep window open during development.
        pass
    finally:
        if p is not None:
            # Do not stop playwright to keep session; runner exits only on Ctrl+C.
            pass


def wait_for_user_login(logger: logging.Logger) -> None:
    logger.info("If login is required, complete it in the opened Edge window.")
    logger.info("Press Enter to continue …")
    try:
        input("")
    except Exception:
        time.sleep(20)


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
    stable_count = 0
    while time.time() < deadline:
        try:
            body_text = page.evaluate("() => (document && document.body && document.body.innerText) || ''")
        except Exception:
            body_text = ""
        # Heuristic: no 'Loading...' and presence of domain text like 'Comdty'
        if ("Loading..." not in body_text) and (body_text.count("Comdty") >= 3):
            # Require two consecutive stable snapshots
            if last_text is not None and body_text == last_text:
                stable_count += 1
            else:
                stable_count = 0
                last_text = body_text
            if stable_count >= 1:  # two consecutive equal snapshots
                logger.info(f"Data ready after {time.time() - start:.1f}s")
                return
        # Give the network a brief chance to settle
        try:
            page.wait_for_load_state("networkidle", timeout=int(POLL_INTERVAL_SEC * 1000))
        except Exception:
            pass
        time.sleep(POLL_INTERVAL_SEC)
    logger.warning("Proceeding despite 'Loading...' still present after max wait")


def select_and_copy(page: Page, logger: logging.Logger) -> Optional[str]:
    # Reset focus
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass
    try:
        page.focus("body")
    except Exception:
        pass
    try:
        page.bring_to_front()
    except Exception:
        pass

    # Navigate to first cell: TAB×5 (Edge), then DOWN
    for _ in range(5):
        page.keyboard.press("Tab")
        time.sleep(KEY_PAUSE_SEC)
    page.keyboard.press("ArrowDown")
    time.sleep(KEY_PAUSE_SEC)

    # Exact selection sequence: Ctrl+Shift+ArrowDown, then Ctrl+Shift+ArrowRight
    page.keyboard.down("Control")
    page.keyboard.down("Shift")
    page.keyboard.press("ArrowDown")
    time.sleep(KEY_PAUSE_SEC)
    page.keyboard.press("ArrowRight")
    time.sleep(KEY_PAUSE_SEC)
    page.keyboard.up("Shift")
    page.keyboard.up("Control")
    time.sleep(AFTER_SELECT_WAIT_SEC)

    # Page-scoped clipboard read (Ctrl+C)
    try:
        page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=PM_URL)
    except Exception:
        pass

    try:
        page.keyboard.press("Control+C")
        time.sleep(1.0)
        text = page.evaluate("async () => await navigator.clipboard.readText().catch(() => '')")
        if text:
            logger.info(f"Copied selection ({len(text)} chars).")
            return text
        # Retry once if empty or looks like loading
        logger.warning("Empty clipboard after copy; retrying selection once…")
        # Re-run nav + selection quickly
        for _ in range(7):
            page.keyboard.press("Tab")
            time.sleep(KEY_PAUSE_SEC)
        page.keyboard.press("ArrowDown")
        time.sleep(KEY_PAUSE_SEC)
        page.keyboard.down("Control")
        page.keyboard.down("Shift")
        page.keyboard.press("ArrowDown")
        time.sleep(KEY_PAUSE_SEC)
        page.keyboard.press("ArrowRight")
        time.sleep(KEY_PAUSE_SEC)
        page.keyboard.up("Shift")
        page.keyboard.up("Control")
        time.sleep(AFTER_SELECT_WAIT_SEC)
        page.keyboard.press("Control+C")
        time.sleep(1.0)
        text = page.evaluate("async () => await navigator.clipboard.readText().catch(() => '')")
        if text:
            logger.info(f"Copied selection on retry ({len(text)} chars).")
            return text
    except Exception as exc:
        logger.warning(f"Clipboard read failed: {exc}")
    return None


def parse_to_csv(text: str, logger: logging.Logger) -> Optional[Path]:
    rows = [r for r in text.splitlines() if r.strip()]
    if rows and rows[0].startswith("#") and rows[0].endswith("#"):
        rows = rows[1:]
    if not rows:
        logger.warning("No non-empty rows found; skipping CSV save.")
        return None
    # Split on tabs if present, else whitespace
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
    out_dir = OUTPUT_ROOT / now.strftime("%m-%d-%Y")
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
        wait_for_user_login(logger)
        while True:
            wait_for_data_ready(page, logger)
            text = select_and_copy(page, logger)
            if text:
                parse_to_csv(text, logger)
            else:
                logger.warning("Empty selection; will retry next cycle.")

            logger.info(f"Sleeping {SLEEP_BETWEEN_RUNS_SEC}s before next run…")
            time.sleep(SLEEP_BETWEEN_RUNS_SEC)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received; exiting runner.")
        return 0
    except Exception:
        logger.exception("Unexpected error in runner")
        return 1
    finally:
        # Keep window open during development; no explicit context close.
        safe_close_context(ctx)


if __name__ == "__main__":
    sys.exit(main())

