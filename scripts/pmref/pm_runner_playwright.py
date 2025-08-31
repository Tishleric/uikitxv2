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
OUTPUT_ROOT = Path(r"Z:\Hanyu\FiveMinuteMonkey")

# Timing (development)
MAX_DATA_WAIT_SEC = 240.0
POLL_INTERVAL_SEC = 0.15
KEY_PAUSE_SEC = 0.03
AFTER_SELECT_WAIT_SEC = 5.0  # legacy; not used as fixed sleep anymore
SLEEP_BETWEEN_RUNS_SEC = 2
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
            args=[
                "--disable-infobars",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
            ],
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


def is_loading(page: Page) -> bool:
    try:
        body_text = page.evaluate("() => (document && document.body && document.body.innerText) || ''")
    except Exception:
        return False
    return "Loading..." in body_text


def get_visibility(page: Page) -> tuple[bool, str]:
    try:
        hidden = bool(page.evaluate("() => document.hidden === true"))
    except Exception:
        hidden = False
    try:
        state = str(page.evaluate("() => document.visibilityState || ''"))
    except Exception:
        state = ""
    return hidden, state


def minimize_edge_window(page: Page, logger: logging.Logger) -> None:
    try:
        client = page.context.new_cdp_session(page)
        info = client.send("Browser.getWindowForTarget")
        window_id = int(info.get("windowId", 0))
        if window_id:
            client.send("Browser.setWindowBounds", {"windowId": window_id, "bounds": {"windowState": "minimized"}})
            logger.info("Minimized Edge via CDP.")
            return
    except Exception as exc:
        logger.warning(f"CDP minimize failed: {exc}")
    # Fallback PowerShell minimize (best-effort)
    try:
        import subprocess
        ps = (
            "$md='[System.Runtime.InteropServices.DllImport(\"user32.dll\")] public static extern bool ShowWindowAsync(System.IntPtr hWnd, int nCmdShow);'; "
            "Add-Type -Name Win32Show -Namespace Native -MemberDefinition $md; "
            "Get-Process msedge -ErrorAction SilentlyContinue | ForEach-Object { $_.MainWindowHandle } | "
            "Where-Object { $_ -ne 0 } | ForEach-Object { [Native.Win32Show]::ShowWindowAsync($_,6) }"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=False)
        logger.info("Issued minimize via PowerShell (best-effort).")
    except Exception as exc:
        logger.warning(f"PowerShell minimize failed: {exc}")


def select_and_copy(page: Page, logger: logging.Logger, allow_bring_to_front: bool = False) -> Optional[str]:
    # Reset focus
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass
    try:
        page.focus("body")
    except Exception:
        pass
    if allow_bring_to_front:
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

    # Page-scoped clipboard read (Ctrl+C)
    try:
        page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=PM_URL)
    except Exception:
        pass

    try:
        # Attempt up to 3 quick retries with short backoffs
        text: Optional[str] = None
        for attempt in range(3):
            page.keyboard.press("Control+C")
            time.sleep(0.15)
            text = page.evaluate("async () => await navigator.clipboard.readText().catch(() => '')")
            if text and ("Loading" not in text):
                break
            # Re-issue selection (keep focus) for the next try
            page.keyboard.down("Control")
            page.keyboard.down("Shift")
            page.keyboard.press("ArrowDown")
            time.sleep(KEY_PAUSE_SEC)
            page.keyboard.press("ArrowRight")
            time.sleep(KEY_PAUSE_SEC)
            page.keyboard.up("Shift")
            page.keyboard.up("Control")
            time.sleep(0.12)
            # If still loading on second attempt, give readiness a chance
            if attempt == 1 and is_loading(page):
                wait_for_data_ready(page, logger)
        if text and ("Loading" not in text):
            logger.info(f"Copied selection ({len(text)} chars) after {attempt+1} attempt(s).")
            return text
        # Final fallback: selection string
        fallback = page.evaluate("() => (window.getSelection && window.getSelection().toString()) || ''")
        if fallback:
            logger.info(f"Using selection string fallback ({len(fallback)} chars).")
            return fallback
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
        first_run = True
        while True:
            cycle_start = time.perf_counter()
            # Ensure data readiness: quick check first, only wait when needed
            if is_loading(page):
                wait_for_data_ready(page, logger)
            # Keep window visible until first successful pull; no pre-iteration minimize
            text = select_and_copy(page, logger, allow_bring_to_front=first_run)
            if text:
                parse_to_csv(text, logger)
                # After first successful pull, minimize and lock in background mode
                if first_run:
                    hidden, _ = get_visibility(page)
                    if not hidden:
                        minimize_edge_window(page, logger)
                    first_run = False
            else:
                logger.warning("Empty selection; will retry next cycle.")

            elapsed = time.perf_counter() - cycle_start
            remainder = max(0.0, SLEEP_BETWEEN_RUNS_SEC - elapsed)
            logger.info(f"Cycle took {elapsed:.2f}s; sleeping {remainder:.2f}s to target {SLEEP_BETWEEN_RUNS_SEC}s cadence…")
            time.sleep(remainder)
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

