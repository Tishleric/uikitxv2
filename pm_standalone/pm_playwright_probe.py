from __future__ import annotations

import datetime
import logging
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd
from playwright.sync_api import sync_playwright, BrowserContext, Page, Browser


PM_URL = "https://pricingmonkey.com/b/ed392083-bb6d-4d8e-a664-206cb82b041c"
PROFILE_DIR = Path(__file__).parent / ".edge_profile"
LOGS_DIR = Path(__file__).parent / "logs"
MAX_DATA_WAIT_SEC = 240
POLL_INTERVAL_SEC = 0.5
KEY_PAUSE_SEC = 0.10
AFTER_SELECT_WAIT_SEC = 5.0

HEADERS = [
    "Bid",
    "Ask",
    "Price",
    "Trade Description",
    "Implied Vol (Daily BP)",
    "Bloomberg",
    "Strike",
    "Trade Amount",
    "DV01",
    "Underlying",
    "Biz Days",
    "Contract Notional",
    "Expiry Date",
    "NPV",
    "DV01 Gamma",
    "Theta",
    "% Delta",
    "Vega",
    "Underlying",
    "Sticky Delta Hedge Amount",
    "Underlying",
    "Atm Vol (Daily BP)",
    "Price in Basis Points",
    "Days",
    "Strike",
    "Gamma",
    "Delta Hedge Amount",
    "Implied Vol",
    "Trade Amount",
    "Expiry Breakeven",
    "Option Price - Intrinsic Price",
    "Vega P&L",
    "Vega (Daily BP)",
    "Intrinsic Price (Strike - Underlying * 32)",
    "Trade Price",
    "Implied Vol",
    "Atm Vol",
    "Bloomberg",
]


def setup_logger() -> logging.Logger:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")
    log_path = LOGS_DIR / f"playwright_diag_{ts}.log"
    logger = logging.getLogger("pm_playwright_diag")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    if not logger.handlers:
        logger.addHandler(fh)
    # Also log minimal info to stdout for operator feedback
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(sh)
    logger.info(f"Diagnostics log: {log_path}")
    return logger


def launch_edge_context(logger: logging.Logger) -> BrowserContext:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Launching Edge (persistent context) with dedicated profile …")
    p = sync_playwright().start()
    try:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            channel="msedge",
            headless=False,
            viewport={"width": 1400, "height": 900},
            args=["--disable-infobars"],
        )
        # Attach playwright object for cleanup later
        context._playwright = p  # type: ignore[attr-defined]
        return context
    except Exception:
        p.stop()
        raise


def safe_close_context(context: BrowserContext) -> None:
    p = getattr(context, "_playwright", None)
    try:
        context.close()
    finally:
        if p is not None:
            p.stop()


def connect_running_edge_context(logger: logging.Logger) -> Optional[BrowserContext]:
    """Attempt to connect to a running Edge with remote debugging enabled (port 9222).

    Returns a BrowserContext if successful, else None.
    """
    endpoints = ["http://localhost:9222", "http://127.0.0.1:9222"]
    for endpoint in endpoints:
        logger.info(f"Trying to connect to existing Edge via CDP ({endpoint})…")
        p = sync_playwright().start()
        try:
            browser: Browser = p.chromium.connect_over_cdp(endpoint)
            contexts = browser.contexts
            if not contexts:
                logger.warning("No contexts found on the connected Edge instance.")
                try:
                    page = browser.new_page()
                    page.close()
                    contexts = browser.contexts
                except Exception:
                    pass
            if contexts:
                context = contexts[0]
                context._playwright = p  # type: ignore[attr-defined]
                context._connected_browser = browser  # type: ignore[attr-defined]
                logger.info("Connected to existing Edge instance.")
                return context
            browser.close()
            p.stop()
        except Exception as exc:
            logger.warning(f"CDP connect failed at {endpoint}: {exc}")
            try:
                p.stop()
            except Exception:
                pass
    return None


def open_pm_and_screenshot(context: BrowserContext, logger: logging.Logger, label: str) -> Page:
    page = context.new_page()
    logger.info(f"Navigating to PM URL … ({label})")
    page.goto(PM_URL, wait_until="load")
    time.sleep(2)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")
    shot = LOGS_DIR / f"pm_page_{label}_{ts}.png"
    try:
        page.screenshot(path=str(shot), full_page=True)
        logger.info(f"Saved screenshot: {shot}")
    except Exception as exc:
        logger.warning(f"Screenshot failed (likely due to navigation): {exc}")
    return page


def try_dom_text_dump(page: Page, logger: logging.Logger) -> Path:
    logger.info("Attempting DOM text dump (document.body.innerText) …")
    ts = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")
    out_txt = LOGS_DIR / f"dom_text_{ts}.txt"
    try:
        body_text = page.evaluate("() => (document && document.body && document.body.innerText) || ''")
        out_txt.write_text(body_text, encoding="utf-8")
        logger.info(f"Wrote DOM text to {out_txt} (len={len(body_text)})")
    except Exception as exc:
        logger.warning(f"DOM text dump failed: {exc}")
    return out_txt

def wait_for_data_ready(page: Page, logger: logging.Logger) -> None:
    start = time.time()
    deadline = start + MAX_DATA_WAIT_SEC
    logger.info("Waiting for data to populate (no 'Loading...' tokens)…")
    while time.time() < deadline:
        try:
            body_text = page.evaluate("() => (document && document.body && document.body.innerText) || ''")
        except Exception:
            body_text = ""
        if "Loading..." not in body_text:
            elapsed = time.time() - start
            logger.info(f"Data ready after {elapsed:.1f}s")
            return
        time.sleep(POLL_INTERVAL_SEC)
    logger.warning("Proceeding despite 'Loading...' still present after max wait")


def try_page_scoped_selection_copy(page: Page, logger: logging.Logger) -> tuple[Optional[str], Path]:
    logger.info("Attempting page-scoped keyboard selection and clipboard read …")
    ts = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")
    sel_txt = LOGS_DIR / f"selection_text_{ts}.txt"
    copied: Optional[str] = None

    # Focus the document body (ignore errors if not focusable)
    try:
        page.focus("body")
    except Exception:
        pass
    # Recreate our navigation steps within the page/tab only
    for _ in range(7):
        page.keyboard.press("Tab")
        time.sleep(KEY_PAUSE_SEC)
    page.keyboard.press("ArrowDown")
    time.sleep(KEY_PAUSE_SEC)

    # Select to end of visible block with Ctrl+Shift (tab-scoped)
    page.keyboard.down("Shift")
    page.keyboard.down("Control")
    page.keyboard.press("ArrowDown")
    time.sleep(KEY_PAUSE_SEC)
    page.keyboard.press("ArrowRight")
    time.sleep(KEY_PAUSE_SEC)
    page.keyboard.up("Control")
    page.keyboard.up("Shift")
    time.sleep(AFTER_SELECT_WAIT_SEC)

    # Try selection text
    try:
        selected = page.evaluate("() => (window.getSelection && window.getSelection().toString()) || ''")
        if selected:
            copied = selected
            sel_txt.write_text(copied, encoding="utf-8")
            logger.info(f"Captured selection via window.getSelection (len={len(copied)}) → {sel_txt}")
    except Exception as exc:
        logger.warning(f"window.getSelection failed: {exc}")

    # Try navigator.clipboard.readText with permissions (page-scoped clipboard)
    if not copied:
        try:
            page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=PM_URL)
            page.keyboard.press("Control+C")
            time.sleep(0.3)
            clipboard_text = page.evaluate("async () => await navigator.clipboard.readText().catch(() => '')")
            if clipboard_text:
                copied = clipboard_text
                sel_txt.write_text(copied, encoding="utf-8")
                logger.info(f"Captured via navigator.clipboard (len={len(copied)}) → {sel_txt}")
        except Exception as exc:
            logger.warning(f"navigator.clipboard read failed: {exc}")

    if not copied:
        logger.warning("Page-scoped selection/clipboard capture returned empty text.")
    return copied, sel_txt


def try_parse_to_csv(text: Optional[str], logger: logging.Logger) -> Optional[Path]:
    if not text:
        logger.warning("No text provided to parse; skipping CSV creation.")
        return None
    rows = [r for r in text.splitlines() if r.strip()]
    # Filter out visual headers like "#1st Call/Put#" if present in top lines
    if rows and rows[0].startswith("#") and rows[0].endswith("#"):
        rows = rows[1:]
    # Best-effort split: if tabs present, use tab; else split on multiple spaces
    if any("\t" in r for r in rows):
        data = [r.split("\t") for r in rows]
    else:
        data = [r.split() for r in rows]
    max_cols = max((len(r) for r in data), default=0)
    # Pad rows to same length
    data = [r + ([""] * (max_cols - len(r))) for r in data]
    df = pd.DataFrame(data)
    if df.shape[1] == len(HEADERS):
        df.columns = HEADERS
    else:
        logger.warning(f"Header length mismatch: parsed {df.shape[1]} cols, headers {len(HEADERS)}; keeping numeric headers")
    ts = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")
    csv_path = LOGS_DIR / f"diag_extract_{ts}.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Wrote diagnostic CSV → {csv_path} (shape={df.shape})")
    return csv_path


def wait_for_user_login(logger: logging.Logger) -> None:
    logger.info("If login is required, complete it in the opened Edge window.")
    logger.info("When finished, return to this console and press Enter to continue …")
    try:
        input("")
    except Exception:
        time.sleep(20)


def main() -> int:
    logger = setup_logger()
    logger.info("=== Playwright Diagnostics Start ===")
    # Simplify: always launch a dedicated Edge context (more reliable than CDP attach)
    context = launch_edge_context(logger)
    try:
        page = open_pm_and_screenshot(context, logger, label="first")
        # Wait for user login if needed, then ensure data is populated
        wait_for_user_login(logger)
        wait_for_data_ready(page, logger)

        logger.info("Step 3: Attempt DOM text extraction (best-effort)")
        try_dom_text_dump(page, logger)

        logger.info("Step 4: Page-scoped keyboard selection and copy (non-OS keystrokes)")
        logger.info("You may switch to the other machine; this uses tab-scoped events only.")
        copied_text, sel_path = try_page_scoped_selection_copy(page, logger)

        logger.info("Step 5: Parse captured text (if any) and write CSV with headers")
        try_parse_to_csv(copied_text, logger)

        logger.info("=== Diagnostics Complete ===")
        return 0
    except Exception:
        logger.exception("Diagnostics encountered an unexpected error")
        return 1
    finally:
        logger.info("Leaving Edge window open (no explicit close) to preserve session.")


if __name__ == "__main__":
    sys.exit(main())

