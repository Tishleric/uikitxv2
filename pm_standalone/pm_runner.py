from __future__ import annotations

import datetime
import io
import logging
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import pandas as pd
import pyperclip
from pywinauto.keyboard import send_keys


URL = "https://pricingmonkey.com/b/ed392083-bb6d-4d8e-a664-206cb82b041c"
WAIT_OPEN_SEC = 3.0
KEY_PAUSE = 0.05
WAIT_CLIPBOARD_SEC = 1.0
WAIT_AFTER_SELECT_SEC = 20.0
OUTPUT_ROOT = Path(r"Z:\Hanyu\FiveMinuteMonkey")

# Explicit header names provided by user, must match selected column count
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


def _setup_logger() -> logging.Logger:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")
    log_dir = Path.cwd() / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # fallback to cwd if cannot create
        log_dir = Path.cwd()
    log_path = log_dir / f"pm_run_{ts}.log"
    logger = logging.getLogger("pm_runner")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    if not logger.handlers:
        logger.addHandler(fh)
    return logger


def _open_in_edge(url: str, logger: logging.Logger) -> None:
    try:
        subprocess.run(["cmd", "/c", "start", "", f"microsoft-edge:{url}"], check=False)
    except Exception as exc:
        logger.warning(f"Edge protocol launch failed: {exc}; trying msedge")
        try:
            subprocess.run(["cmd", "/c", "start", "", "msedge", url], check=False)
        except Exception as exc2:  # fallback to default browser
            logger.warning(f"msedge launch failed: {exc2}; falling back to default browser")
            webbrowser.open(url, new=2)
    time.sleep(WAIT_OPEN_SEC)


def _copy_from_pm(logger: logging.Logger) -> str:
    pyperclip.copy("")
    send_keys("{TAB 7}", pause=KEY_PAUSE, with_spaces=True)
    send_keys("{DOWN}", pause=KEY_PAUSE)
    send_keys("^+{DOWN}", pause=KEY_PAUSE)
    send_keys("^+{RIGHT}", pause=KEY_PAUSE)
    time.sleep(WAIT_AFTER_SELECT_SEC)
    send_keys("^c", pause=KEY_PAUSE)
    time.sleep(WAIT_CLIPBOARD_SEC)
    text = pyperclip.paste()
    send_keys("^w", pause=KEY_PAUSE)
    logger.info(f"Copied {len(text)} chars from clipboard")
    return text


def _parse_and_save(text: str, logger: logging.Logger) -> Path:
    # Treat clipboard as data-only (no header row copied by selection)
    df = pd.read_csv(io.StringIO(text), sep="\t", header=None)
    # Apply explicit headers when the column count matches; otherwise keep numeric headers
    if df.shape[1] == len(HEADERS):
        df.columns = HEADERS
    else:
        logging.getLogger("pm_runner").warning(
            "Header length mismatch: data has %d cols, headers list has %d; leaving numeric headers",
            df.shape[1], len(HEADERS)
        )
    now = datetime.datetime.now()
    out_dir = OUTPUT_ROOT / now.strftime("%m-%d-%Y")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"pmonkey_{now.strftime('%m%d%Y_%H-%M-%S')}.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"Saved CSV to {out_path}")
    return out_path


def main() -> int:
    logger = _setup_logger()
    try:
        logger.info("Opening Pricing Monkey in Edge and copying grid…")
        _open_in_edge(URL, logger)
        text = _copy_from_pm(logger)
        if not text.strip():
            logger.error("Clipboard was empty; no CSV written")
            return 0
        _parse_and_save(text, logger)
    except Exception:
        logger.exception("Unexpected error during run")
    return 0


if __name__ == "__main__":
    sys.exit(main())

