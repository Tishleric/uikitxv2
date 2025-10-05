from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional, Tuple
import threading
import queue
import hashlib

import pandas as pd
from playwright.sync_api import BrowserContext, Page, sync_playwright
import psutil
try:
	import redis as _redis  # type: ignore
except Exception:
	_redis = None  # type: ignore


PM_BASIC_URL = "https://pricingmonkey.com/b/cbe072b5-ba2c-4a5b-bf7c-66c3ba83513d"
PROFILE_DIR = Path(__file__).parent / ".edge_profile_basic"
EXPECTED_COLS = 17

# Key navigation counts
TABS_TO_PRESS = 5
DOWNS_TO_PRESS = 3

# Waits
POLL_INTERVAL_SEC = 0.15
MAX_DATA_WAIT_SEC = 60.0
KEY_PAUSE_SEC = 0.03
INITIAL_POST_NAV_DELAY_SEC = 1.5
TABLE_RENDER_MAX_WAIT_SEC = 20.0
MINIMIZE_DURING_RUN = False
# When True, the Edge window will be closed after copy; keep False while debugging
CLOSE_WINDOW_AT_END = False
# Minimize the reader window after initial load (session mode)
MINIMIZE_READER_ON_START = False
# Window handling delays (seconds)
WINDOW_NORMALIZE_DELAY_SEC = 0.05
WINDOW_BACKGROUND_PUSH_DELAY_SEC = 0.10
WINDOW_MINIMIZE_DELAY_SEC = 0.05
# Writer settle timings
WRITER_PASTE_SETTLE_SEC = 0.005
WRITER_FINAL_SETTLE_SEC = 0.10

# Writer click mapping (AG Grid indices)
# Excel rows: 20, 54, 88, 122, 156, 190 → AG Grid row-index is Excel-1
GRID_OPTION_ROWS = {1: 19, 2: 53, 3: 87, 4: 121, 5: 155, 6: 189}
GRID_COL_DESC = 4  # Column C
GRID_COL_QTY = 5   # Column D
PASTE_COMMIT_WITH_ENTER = False

# Diagnostics toggle for DOM anchoring
ENABLE_FOCUS_DIAGNOSTICS = False


def _setup_logger() -> logging.Logger:
	logger = logging.getLogger("pm_playwright_basic")
	logger.setLevel(logging.INFO)
	if not logger.handlers:
		sh = logging.StreamHandler(sys.stdout)
		sh.setLevel(logging.INFO)
		sh.setFormatter(logging.Formatter("%(message)s"))
		logger.addHandler(sh)
	return logger


def _resolve_profile_dir(use_default_profile: bool) -> Path:
	env_dir = os.environ.get("PM_PROFILE_DIR")
	if env_dir:
		pth = Path(env_dir)
		if pth.exists():
			return pth
	if use_default_profile:
		local = os.environ.get("LOCALAPPDATA", "")
		if local:
			return Path(local) / "Microsoft" / "Edge" / "User Data"
	return PROFILE_DIR



def _is_edge_running() -> bool:
	for proc in psutil.process_iter(attrs=["name"]):
		name = proc.info.get("name") or ""
		if name.lower().startswith("msedge"):
			return True
	return False


def _launch_context(
	logger: logging.Logger,
	user_data_dir: Path,
	profile_directory_arg: Optional[str] = None,
	require_profile_idle: bool = False,
) -> BrowserContext:
	user_data_dir.mkdir(parents=True, exist_ok=True)
	if require_profile_idle and _is_edge_running():
		raise RuntimeError(
			"Edge appears to be running. Close all Edge windows before using the default profile, "
			"or run with --dedicated-profile."
		)
	p = sync_playwright().start()
	try:
		args_list: list[str] = []
		if profile_directory_arg:
			args_list.append(f"--profile-directory={profile_directory_arg}")
		ctx = p.chromium.launch_persistent_context(
			user_data_dir=str(user_data_dir),
			channel="msedge",
			headless=False,
			viewport={"width": 1400, "height": 1200},
			args=args_list,
			timeout=60000,
		)
		ctx._playwright = p  # type: ignore[attr-defined]
		logger.info(
			f"Launched Edge (basic runner) with profile: {user_data_dir}"
		)
		return ctx
	except Exception:
		p.stop()
		raise


def _safe_close_context(ctx: BrowserContext) -> None:
	p = getattr(ctx, "_playwright", None)
	try:
		# Ensure the Playwright driver is stopped to release resources.
		if p is not None:
			try:
				ctx.close()
			except Exception:
				pass
	finally:
		if p is not None:
			try:
				p.stop()
			except Exception:
				pass


def _wait_for_ready(page: Page) -> None:
	start = time.time()
	deadline = start + MAX_DATA_WAIT_SEC
	last_text: Optional[str] = None
	stable_count = 0
	while time.time() < deadline:
		try:
			body_text = page.evaluate("() => (document && document.body && document.body.innerText) || ''")
		except Exception:
			body_text = ""
		if "Loading..." not in body_text:
			if last_text is not None and body_text == last_text:
				stable_count += 1
			else:
				stable_count = 0
				last_text = body_text
			if stable_count >= 1:
				return
		try:
			page.wait_for_load_state("networkidle", timeout=int(POLL_INTERVAL_SEC * 1000))
		except Exception:
			pass
		time.sleep(POLL_INTERVAL_SEC)


def _wait_for_table_rendered(page: Page) -> None:
	start = time.time()
	deadline = start + TABLE_RENDER_MAX_WAIT_SEC
	selectors = [
		"div[role=grid]",
		"table",
		"div.ag-root",
		"div.ag-center-cols-viewport",
		"div.euiDataGrid",
		"div[role=rowgroup]",
	]
	js = (
		"(sels) => {"
		"for (const s of sels) {"
			"const el = document.querySelector(s);"
			"if (el) { const r = el.getBoundingClientRect(); if (r && r.width > 0 && r.height > 0) return true; }"
		"} return false; }"
	)
	while time.time() < deadline:
		try:
			ok = bool(page.evaluate(js, selectors))
			if ok:
				return
		except Exception:
			pass
		try:
			page.wait_for_load_state("domcontentloaded", timeout=int(POLL_INTERVAL_SEC * 1000))
		except Exception:
			pass
		time.sleep(POLL_INTERVAL_SEC)


def _wait_for_grid_stable(page: Page, logger: logging.Logger) -> None:
	"""Wait until the grid/table has no 'Loading...' tokens and stabilizes.

	We check the innerText of a likely grid container and require:
	- zero occurrences of 'Loading...'
	- two consecutive identical text-length snapshots
	"""
	start = time.time()
	deadline = start + MAX_DATA_WAIT_SEC
	selectors = [
		"div[role=grid]",
		"div.ag-center-cols-viewport",
		"div.euiDataGrid",
		"table",
	]
	js = (
		"(sels) => {for (const s of sels){const el=document.querySelector(s); if(el){return el.innerText||'';}} return ''; }"
	)
	prev_len: Optional[int] = None
	stable_hits = 0
	while time.time() < deadline:
		try:
			text = str(page.evaluate(js, selectors))
		except Exception:
			text = ""
		loading = text.count("Loading...")
		if loading == 0:
			cur_len = len(text)
			if prev_len is not None and cur_len == prev_len:
				stable_hits += 1
			else:
				stable_hits = 0
				prev_len = cur_len
			if stable_hits >= 1:  # two equal snapshots
				logger.info("Grid stabilized and no 'Loading...' present.")
				return
		try:
			page.wait_for_load_state("networkidle", timeout=int(POLL_INTERVAL_SEC * 1000))
		except Exception:
			pass
		time.sleep(POLL_INTERVAL_SEC)
	logger.info("Proceeding after max wait; grid may still be updating.")


def _minimize_edge_window(page: Page, logger: logging.Logger) -> None:
	"""Attempt to minimize the Edge window via CDP, fallback to PowerShell.

	This keeps the UI out of the way during automation.
	"""
	try:
		client = page.context.new_cdp_session(page)
		info = client.send("Browser.getWindowForTarget")
		window_id = int(info.get("windowId", 0))
		if window_id:
			client.send("Browser.setWindowBounds", {"windowId": window_id, "bounds": {"windowState": "minimized"}})
			logger.info("Minimized Edge via CDP.")
			return
	except Exception as exc:
		logger.debug(f"CDP minimize failed: {exc}")
	# Fallback PowerShell minimize (best-effort)
	try:
		import subprocess  # local import to avoid linter import-order noise
		ps = (
			"$md='[System.Runtime.InteropServices.DllImport(\"user32.dll\")] public static extern bool ShowWindowAsync(System.IntPtr hWnd, int nCmdShow);'; "
			"Add-Type -Name Win32Show -Namespace Native -MemberDefinition $md; "
			"Get-Process msedge -ErrorAction SilentlyContinue | ForEach-Object { $_.MainWindowHandle } | "
			"Where-Object { $_ -ne 0 } | ForEach-Object { [Native.Win32Show]::ShowWindowAsync($_,6) }"
		)
		subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=False)
		logger.info("Issued minimize via PowerShell (best-effort).")
	except Exception as exc:
		logger.debug(f"PowerShell minimize failed: {exc}")


def _get_window_state(page: Page) -> Optional[str]:
	"""Return current windowState via CDP (e.g., 'normal', 'minimized')."""
	try:
		client = page.context.new_cdp_session(page)
		info = client.send("Browser.getWindowForTarget")
		window_id = int(info.get("windowId", 0))
		if not window_id:
			return None
		bounds = client.send("Browser.getWindowBounds", {"windowId": window_id})
		return bounds.get("windowState")
	except Exception:
		return None


def _set_window_state(page: Page, state: str, logger: logging.Logger) -> None:
	"""Set window state via CDP (state: 'normal'|'minimized'). Best-effort."""
	try:
		client = page.context.new_cdp_session(page)
		info = client.send("Browser.getWindowForTarget")
		window_id = int(info.get("windowId", 0))
		if window_id:
			client.send("Browser.setWindowBounds", {"windowId": window_id, "bounds": {"windowState": state}})
			logger.info(f"Set window state to {state} via CDP.")
	except Exception as exc:
		logger.debug(f"set_window_state({state}) failed: {exc}")


def _push_window_to_background(logger: logging.Logger) -> None:
	"""Best-effort push Edge windows behind others (Windows-only).

	Uses user32.SetWindowPos to move all msedge top-level windows to bottom without activation.
	"""
	try:
		import subprocess
		ps = r"""
$code = @"
using System;
using System.Runtime.InteropServices;
public static class NativeWin32 {
    [DllImport("user32.dll")]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
}
"@;
try { Add-Type -TypeDefinition $code -Language CSharp -ErrorAction Stop; } catch {}
$SWP_NOACTIVATE = 0x0010; $SWP_NOMOVE = 0x0002; $SWP_NOSIZE = 0x0001;
$flags = $SWP_NOACTIVATE -bor $SWP_NOMOVE -bor $SWP_NOSIZE;
$HWND_BOTTOM = [IntPtr]1;
Get-Process msedge -ErrorAction SilentlyContinue | ForEach-Object {
  $hwnd = $_.MainWindowHandle;
  if ($hwnd -ne 0) { [NativeWin32]::SetWindowPos($hwnd, $HWND_BOTTOM, 0,0,0,0, $flags) | Out-Null }
}
"""
		subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=False)
		logger.info("Pushed Edge window(s) to background (best-effort).")
	except Exception as exc:
		logger.debug(f"push_to_background failed: {exc}")


def _close_window(page: Page, logger: logging.Logger) -> None:
	"""Close the browser window hosting this page.

	Tries context.close() first, then CDP Browser.close(), then Ctrl+W as a last resort.
	"""
	try:
		page.context.close()
		logger.info("Closed window via context.close().")
		return
	except Exception as exc:
		logger.debug(f"context.close() failed: {exc}")
	try:
		client = page.context.new_cdp_session(page)
		client.send("Browser.close")
		logger.info("Closed window via CDP Browser.close().")
		return
	except Exception as exc:
		logger.debug(f"CDP Browser.close failed: {exc}")
	try:
		page.keyboard.press("Control+W")
		time.sleep(0.2)
		logger.info("Issued Ctrl+W to close window (fallback).")
	except Exception:
		pass


def _select_copy(page: Page, logger: logging.Logger) -> Optional[str]:
	# Reset focus
	try:
		page.keyboard.press("Escape")
	except Exception:
		pass
	try:
		page.focus("body")
	except Exception:
		pass

	# Prefer DOM-driven anchoring to the top-left data cell (AG Grid)
	used_dom = False
	try:
		used_dom = _focus_top_left_cell(page, logger)
	except Exception:
		used_dom = False
	if not used_dom:
		# Fallback: keyboard homing (Tab×N, Down×M)
		for _ in range(TABS_TO_PRESS):
			page.keyboard.press("Tab")
			time.sleep(KEY_PAUSE_SEC)
		for _ in range(DOWNS_TO_PRESS):
			page.keyboard.press("ArrowDown")
			time.sleep(KEY_PAUSE_SEC)

	# Ctrl+Shift+Down then Ctrl+Shift+Right
	page.keyboard.down("Control")
	page.keyboard.down("Shift")
	page.keyboard.press("ArrowDown")
	time.sleep(KEY_PAUSE_SEC)
	page.keyboard.up("Shift")
	page.keyboard.up("Control")
	page.keyboard.down("Control")
	page.keyboard.down("Shift")
	page.keyboard.press("ArrowRight")
	time.sleep(KEY_PAUSE_SEC)
	page.keyboard.up("Shift")
	page.keyboard.up("Control")

	# Horizontal extension: Ctrl+Shift+ArrowRight
	page.keyboard.down("Control")
	page.keyboard.down("Shift")
	try:
		page.keyboard.press("ArrowRight")
		time.sleep(KEY_PAUSE_SEC)
	except Exception:
		pass
	page.keyboard.up("Shift")
	page.keyboard.up("Control")

	# Ensure all Loading... cleared before copy – grid-level stabilization
	_wait_for_grid_stable(page, logger)

	# Clipboard permissions and copy
	try:
		page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=PM_BASIC_URL)
	except Exception:
		pass
	text: Optional[str] = None
	# Try up to 3 times in case cells are still painting
	for _ in range(3):
		try:
			page.keyboard.press("Control+C")
			time.sleep(0.2)
			text = page.evaluate("async () => await navigator.clipboard.readText().catch(() => '')")
			if text and ("Loading..." not in text):
				break
		except Exception:
			text = None
		# brief re-wait before retry
		_wait_for_grid_stable(page, logger)
	if text:
		return text
	# Final fallback: selection string
	try:
		fallback = page.evaluate("() => (window.getSelection && window.getSelection().toString()) || ''")
		return fallback or None
	except Exception:
		return None


def _reanchor_and_select(page: Page) -> None:
	"""Move selection to top-left then expand to full region."""
	try:
		page.keyboard.press("Escape")
		page.focus("body")
		page.keyboard.press("Control+ArrowUp")
		time.sleep(KEY_PAUSE_SEC)
		page.keyboard.press("Control+ArrowLeft")
		time.sleep(KEY_PAUSE_SEC)
		for _ in range(3):
			page.keyboard.press("ArrowDown")
			time.sleep(KEY_PAUSE_SEC)
		page.keyboard.down("Control"); page.keyboard.down("Shift"); page.keyboard.press("ArrowDown"); time.sleep(KEY_PAUSE_SEC); page.keyboard.up("Shift"); page.keyboard.up("Control")
		page.keyboard.down("Control"); page.keyboard.down("Shift"); page.keyboard.press("ArrowRight"); time.sleep(KEY_PAUSE_SEC); page.keyboard.up("Shift"); page.keyboard.up("Control")
	except Exception:
		pass


def _focus_grid(page: Page, logger: logging.Logger) -> bool:
	selectors = [
		"div[role=grid]",
		"div.ag-center-cols-viewport",
		"div.euiDataGrid",
		"table",
	]
	try:
		pt = page.evaluate(
			"(sels) => {\n"
			" for (const s of sels){ const el = document.querySelector(s); if (el){ const r = el.getBoundingClientRect(); if(r && r.width>0 && r.height>0){ return {x: r.left + Math.min(30, r.width/2), y: r.top + Math.min(30, r.height/2)}; } } } return null; }",
			selectors,
		)
		if pt and isinstance(pt, dict) and "x" in pt and "y" in pt:
			page.mouse.click(float(pt["x"]), float(pt["y"]))
			return True
		# Fallback: focus body and Tab
		try:
			page.focus("body")
		except Exception:
			pass
		for _ in range(5):
			page.keyboard.press("Tab")
			time.sleep(KEY_PAUSE_SEC)
		return True
	except Exception as exc:
		logger.debug(f"focus_grid failed: {exc}")
		return False


def _focus_top_left_cell(page: Page, logger: logging.Logger, timeout_ms: int = 4000) -> bool:
	"""Anchor to the top-left AG Grid data cell via DOM click; support iframes.

	Returns True if activeElement is a data cell (not header); False otherwise.
	"""
	# First, attempt to scroll relevant viewports to the top-left so row 0 is visible
	try:
		page.evaluate(
			"""
			() => {
			  const vp = document.querySelector('div.ag-center-cols-viewport');
			  if (vp) { vp.scrollTop = 0; vp.scrollLeft = 0; }
			  const pl = document.querySelector('div.ag-pinned-left-cols-viewport');
			  if (pl) { pl.scrollTop = 0; }
			  const root = document.querySelector('.ag-root') || document.querySelector('.ag-root-wrapper');
			  if (root) { root.scrollTop = 0; }
			  return true;
			}
			"""
		)
	except Exception:
		pass

	# Prefer explicit row 0 / col 2 in the center container to avoid pinned-left; then fall back
	selectors = [
		"div.ag-center-cols-container div[row-index='0'] .ag-cell[aria-colindex='2']",
		"div.ag-center-cols-container div[row-index='0'] .ag-cell[aria-colindex='1']",
		"div[role='row'][aria-rowindex='1'] .ag-cell[aria-colindex='2']",
		"div[role='row'][aria-rowindex='1'] .ag-cell[aria-colindex='1']",
		".ag-root .ag-body-viewport .ag-center-cols-container .ag-row .ag-cell",
		".ag-root-wrapper .ag-body-viewport .ag-center-cols-container .ag-row .ag-cell",
		# Pinned-left only as last resort
		".ag-root .ag-body-viewport .ag-pinned-left-cols-container .ag-row .ag-cell",
		".ag-root-wrapper .ag-body-viewport .ag-pinned-left-cols-container .ag-row .ag-cell",
		".ag-body-viewport .ag-row .ag-cell",
	]

	def _try_ctx(ctx, ctx_name: str) -> bool:
		# Ensure this context is scrolled to top-left as well
		try:
			ctx.evaluate(
				"""
				() => {
				  const vp = document.querySelector('div.ag-center-cols-viewport');
				  if (vp) { vp.scrollTop = 0; vp.scrollLeft = 0; }
				  const pl = document.querySelector('div.ag-pinned-left-cols-viewport');
				  if (pl) { pl.scrollTop = 0; }
				  const root = document.querySelector('.ag-root') || document.querySelector('.ag-root-wrapper');
				  if (root) { root.scrollTop = 0; }
				  return true;
				}
				"""
			)
		except Exception:
			pass
		for sel in selectors:
			loc = ctx.locator(sel).first
			try:
				loc.wait_for(state="visible", timeout=timeout_ms)
				try:
					loc.scroll_into_view_if_needed(timeout=timeout_ms)
				except Exception:
					pass
				try:
					loc.focus()
				except Exception:
					pass
				loc.click(position={"x": 5, "y": 5}, timeout=timeout_ms)
				ok = bool(
					ctx.evaluate(
						"""
						() => {
						  const ae = document.activeElement||null;
						  const cls = (ae?.className||'').toString();
						  return cls.includes('ag-cell') && !cls.includes('ag-header-cell');
						}
						"""
					)
				)
				if ENABLE_FOCUS_DIAGNOSTICS:
					logger.info(f"focus_top_left_cell: context={ctx_name} selector='{sel}' ok={ok}")
				if ok:
					# If we landed in a pinned-left cell, nudge one step to the right into center container
					try:
						is_pinned = bool(ctx.evaluate(
							"() => { const ae=document.activeElement; return !!(ae && ae.closest('.ag-pinned-left-cols-container')); }"
						))
						if is_pinned:
							# Attempt to access a Page instance to send a right-arrow key
							try:
								page_obj = getattr(ctx, "page", None)
							except Exception:
								page_obj = None
							if page_obj is None and hasattr(ctx, "keyboard"):
								page_obj = ctx
							try:
								if page_obj is not None:
									page_obj.keyboard.press("ArrowRight")
							except Exception:
								pass
							# Verify moved into center
							try:
								ok2 = bool(ctx.evaluate(
									"() => { const ae=document.activeElement; return !!(ae && !ae.closest('.ag-pinned-left-cols-container') && (ae.className||'').toString().includes('ag-cell')); }"
								))
								if ENABLE_FOCUS_DIAGNOSTICS:
									logger.info(f"focus_top_left_cell: nudged right from pinned-left, ok2={ok2}")
								if ok2:
									return True
							except Exception:
								pass
					except Exception:
						pass
					return True
			except Exception:
				continue
		return False

	try:
		if _try_ctx(page, "main"):
			return True
		for fr in page.frames:
			if fr == page.main_frame:
				continue
			if _try_ctx(fr, "frame"):
				return True
	except Exception:
		pass
	if ENABLE_FOCUS_DIAGNOSTICS:
		logger.info("focus_top_left_cell: fallback to keyboard homing")
	return False

def _reselect_and_copy(page: Page, logger: logging.Logger) -> Optional[str]:
    """Use the initial selection path to re-anchor and copy on malformed selection."""
    # Best-effort reset/focus body
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass
    try:
        page.focus("body")
    except Exception:
        pass

    logger.info("(reselect) Using initial selection path")
    # Try DOM-driven anchor to top-left; fallback to grid focus
    try:
        used_dom = bool(_focus_top_left_cell(page, logger))
    except Exception:
        used_dom = False
    if not used_dom:
        try:
            _focus_grid(page, logger)
        except Exception:
            pass

    # Reuse the initial robust selection + copy path
    text = _select_copy(page, logger)
    if text and ("Loading..." not in text):
        return text

    # Fallback: Ctrl+A within focused grid
    try:
        page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=PM_BASIC_URL)
    except Exception:
        pass
    try:
        page.keyboard.press("Control+A")
        time.sleep(0.2)
        page.keyboard.press("Control+C")
        time.sleep(0.2)
        text = page.evaluate("async () => await navigator.clipboard.readText().catch(() => '')")
        return text
    except Exception:
        return text


def _parse_dataframe(text: str) -> pd.DataFrame:
	rows = [r for r in text.splitlines() if r.strip()]
	if not rows:
		return pd.DataFrame()
	if any("\t" in r for r in rows):
		data = [r.split("\t") for r in rows]
	else:
		data = [r.split() for r in rows]
	max_cols = max((len(r) for r in data), default=0)
	data = [r + ([""] * (max_cols - len(r))) for r in data]
	columns = [
		"Expiry Date",
		"Bloomberg",
		"Trade Description",
		"Trade Amount",
		"Underlying Shift",
		"Underlying",
		"Strike",
		"Bid",
		"Price",
		"Ask",
		"NPV",
		"scenario pnl",
		"Implied Vol (Daily BP)",
		"DV01",
		"DV01 Gamma",
		"Theta",
		"Vega",
	]
	df = pd.DataFrame(data)
	if df.shape[1] == len(columns):
		df.columns = columns
	return df


class PMBasicRunner:

	def __init__(self, url: str = PM_BASIC_URL, use_default_profile: bool = False) -> None:
		self._url = url
		self._logger = _setup_logger()
		self._use_default_profile = use_default_profile

	def collect_once(self) -> pd.DataFrame:
		user_data_dir = _resolve_profile_dir(self._use_default_profile)
		profile_dir_name = "Default" if self._use_default_profile else None
		ctx = _launch_context(
			self._logger,
			user_data_dir,
			profile_dir_name,
			require_profile_idle=self._use_default_profile,
		)
		try:
			page = ctx.new_page()
			self._logger.info(f"Opening Pricing Monkey URL: {self._url}")
			page.goto(self._url, wait_until="load")
			time.sleep(INITIAL_POST_NAV_DELAY_SEC)
			if MINIMIZE_DURING_RUN:
				self._logger.info("Minimizing Edge window…")
				_minimize_edge_window(page, self._logger)
			self._logger.info("Waiting for table DOM to render…")
			_wait_for_table_rendered(page)
			self._logger.info("Table detected; starting selection/copy automation…")
			text = _select_copy(page, self._logger)
			if not text:
				self._logger.warning("Empty clipboard/selection; returning empty DataFrame")
				if CLOSE_WINDOW_AT_END:
					_close_window(page, self._logger)
				else:
					self._logger.info("Debug mode: skipping window close (empty selection).")
				return pd.DataFrame()
			self._logger.info(f"Copy complete (chars={len(text)})")
			if CLOSE_WINDOW_AT_END:
				self._logger.info("Closing window…")
				_close_window(page, self._logger)
			else:
				self._logger.info("Debug mode: skipping window close after copy.")
			return _parse_dataframe(text)
		finally:
			if CLOSE_WINDOW_AT_END:
				_safe_close_context(ctx)
			else:
				self._logger.info("Debug mode: skipping context close; browser remains open.")


class PMBasicSessionRunner:

	def __init__(self, url: str = PM_BASIC_URL, use_default_profile: bool = False) -> None:
		self._url = url
		self._logger = _setup_logger()
		self._use_default_profile = use_default_profile
		self._ctx: Optional[BrowserContext] = None
		self._page: Optional[Page] = None
		self._has_anchor: bool = False
		self._last_copy_ts: float = 0.0
		# Background loop state
		self._thread: Optional[threading.Thread] = None
		self._stop_event: threading.Event = threading.Event()
		self._lock: threading.Lock = threading.Lock()
		self._latest_df: Optional[pd.DataFrame] = None
		self._latest_sig: str = ""
		self._last_updated: float = 0.0
		self._owner_ident: Optional[int] = None
		self._consec_failures: int = 0
		# Readiness event for UI consumers waiting on first successful tick
		self._ready_event: threading.Event = threading.Event()
		# Redis subscriber
		self._redis_thread: Optional[threading.Thread] = None
		self._refresh_requested: bool = False
		self._debounce_until: float = 0.0
		self._refresh_on_redis: bool = False
		# Writer queue (same-tab writes)
		self._write_q: "queue.Queue[list[dict]]" = queue.Queue()
		self._mode: str = "reader"  # reader | writer
		self._last_written: dict[int, dict[str, Optional[str]]] = {}
		self._prev_viewport: Optional[tuple[int, int]] = None
		# Auto-refresh (hourly close) scheduler (monotonic deadline)
		self._next_auto_close_deadline: float = 0.0

	def start(self) -> None:
		if self._ctx is not None and self._page is not None:
			return
		user_data_dir = _resolve_profile_dir(self._use_default_profile)
		profile_dir_name = "Default" if self._use_default_profile else None
		ctx = _launch_context(
			self._logger,
			user_data_dir,
			profile_dir_name,
			require_profile_idle=self._use_default_profile,
		)
		page = ctx.new_page()
		self._logger.info(f"(session) Opening Pricing Monkey URL: {self._url}")
		page.goto(self._url, wait_until="load")
		time.sleep(INITIAL_POST_NAV_DELAY_SEC)
		self._logger.info("(session) Waiting for table DOM to render…")
		_wait_for_table_rendered(page)
		self._ctx = ctx
		self._page = page
		self._has_anchor = False
		self._last_copy_ts = 0.0
		self._owner_ident = threading.get_ident()
		self._ready_event.clear()
		# Minimize reader window after initial setup if configured
		if MINIMIZE_READER_ON_START:
			try:
				_minimize_edge_window(self._page, self._logger)
			except Exception:
				pass

	def is_page_open(self) -> bool:
		try:
			return self._page is not None
		except Exception:
			return False

	def is_loop_alive(self) -> bool:
		thr = self._thread
		try:
			return bool(thr and thr.is_alive())
		except Exception:
			return False

	def _df_signature(self, df: pd.DataFrame) -> str:
		try:
			payload = df.to_json(orient="split", date_format="iso").encode("utf-8")
			return hashlib.md5(payload).hexdigest()
		except Exception:
			return f"{df.shape[0]}x{df.shape[1]}:{int(time.time())}"

	def _start_redis_subscriber(self) -> None:
		"""Start a background Redis subscriber that toggles a refresh flag.

		Best-effort: if redis is unavailable or errors occur, the reader proceeds without it.
		All Playwright interactions remain on the main background loop thread; the
		subscriber only flips flags that the loop reads.
		"""
		if self._redis_thread and self._redis_thread.is_alive():
			return
		if _redis is None:
			self._logger.info("(session) Redis not available; subscribe disabled")
			return
		# Build client from env
		host = os.environ.get("REDIS_HOST", "127.0.0.1")
		try:
			port = int(os.environ.get("REDIS_PORT", "6379"))
		except Exception:
			port = 6379
		try:
			db = int(os.environ.get("REDIS_DB", "0"))
		except Exception:
			db = 0
		pwd = os.environ.get("REDIS_PASSWORD", None)
		try:
			client = _redis.Redis(host=host, port=port, db=db, password=pwd, decode_responses=True)  # type: ignore
		except Exception as exc:
			self._logger.info(f"(session) Redis client init failed: {exc}")
			return

		def _run_sub() -> None:
			try:
				pubsub = client.pubsub()
				pubsub.subscribe("pm:sheet_changed")
				self._logger.info("(session) Subscribed to Redis channel pm:sheet_changed")
				for msg in pubsub.listen():
					if self._stop_event.is_set():
						break
					if not msg or msg.get("type") != "message":
						continue
					# Debounce frequent events and request refresh
					self._refresh_requested = True
					self._debounce_until = time.time() + 0.5
			except Exception as exc:
				self._logger.info(f"(session) Redis subscriber ended: {exc}")

		self._redis_thread = threading.Thread(target=_run_sub, name="PMRedisSubscriber", daemon=True)
		self._redis_thread.start()

	def tick_collect(self) -> pd.DataFrame:
		if self._page is None:
			raise RuntimeError("Session not started")
		page = self._page
		text: Optional[str] = None
		candidate_df: pd.DataFrame = pd.DataFrame()
		# Initial selection once to establish anchor
		if not self._has_anchor:
			self._logger.debug("(session) Performing initial selection to establish anchor…")
			text = _select_copy(page, self._logger)
			if text:
				self._has_anchor = True
				self._last_copy_ts = time.time()
		else:
			# Copy-only path: wait for stability, then Ctrl+C and read clipboard
			self._logger.debug("(session) Copy-only tick path…")
			_wait_for_grid_stable(page, self._logger)
			# Throttle to ~1s
			if time.time() - self._last_copy_ts < 1.0:
				time.sleep(max(0.0, 1.0 - (time.time() - self._last_copy_ts)))
			try:
				page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=PM_BASIC_URL)
			except Exception:
				pass
			for attempt in range(2):
				try:
					page.keyboard.press("Control+C")
					time.sleep(0.2)
					text = page.evaluate("async () => await navigator.clipboard.readText().catch(() => '')")
					if text and ("Loading..." not in text):
						break
				except Exception:
					text = None
					self._logger.debug("(session) Copy-only attempt %d failed; re-waiting…", attempt + 1)
					_wait_for_grid_stable(page, self._logger)
			self._last_copy_ts = time.time()
			# Drift detection: empty/Loading..., or wrong column count/too short payload
			needs_reselect = False
			if not text or ("Loading..." in (text or "")):
				needs_reselect = True
			else:
				candidate_df = _parse_dataframe(text)
				if candidate_df.empty or candidate_df.shape[1] != EXPECTED_COLS or len(text) < 100:
					needs_reselect = True
			if needs_reselect:
				self._logger.info("(session) Selection drift detected → reselection")
				text = _reselect_and_copy(page, self._logger)
				self._has_anchor = bool(text)
				self._last_copy_ts = time.time()
				if text:
					candidate_df = _parse_dataframe(text)
		if not text:
			self._logger.warning("(session) Empty clipboard/selection on tick; returning empty DataFrame")
			df = pd.DataFrame()
		else:
			df = candidate_df if not candidate_df.empty else _parse_dataframe(text)
		# Update snapshot under lock
		with self._lock:
			self._latest_df = df
			self._latest_sig = self._df_signature(df)
			self._last_updated = time.time()
			self._ready_event.set()
		return df

	def start_loop(self, interval_sec: float = 1.0) -> None:
		if self._thread and self._thread.is_alive():
			return
		self._stop_event.clear()
		# Schedule first auto-close (monotonic) – 1 hour
		try:
			self._next_auto_close_deadline = time.monotonic() + 3600.0
		except Exception:
			self._next_auto_close_deadline = 0.0
		# Start Redis subscriber (best-effort)
		self._start_redis_subscriber()
		def _run() -> None:
			while not self._stop_event.is_set():
				try:
					# Ensure session (context/page) is created on this thread
					cur_ident = threading.get_ident()
					if self._owner_ident is None or self._owner_ident != cur_ident or self._page is None:
						# Close any previous context created on a different thread
						try:
							if self._ctx is not None:
								_safe_close_context(self._ctx)
						except Exception:
							pass
						self._ctx = None
						self._page = None
						self._has_anchor = False
						self._owner_ident = None
						self.start()
					# Auto-close to refresh stale PM tab (reader mode only)
					try:
						if self._mode == "reader" and self._page is not None and self._next_auto_close_deadline and time.monotonic() >= self._next_auto_close_deadline:
							self._logger.info("(session) Hourly auto-close: refreshing Pricing Monkey page")
							try:
								_close_window(self._page, self._logger)
							except Exception:
								pass
							self._page = None
							# next refresh scheduled (monotonic) – 1 hour
							self._next_auto_close_deadline = time.monotonic() + 3600.0
							# allow loop to recreate session on next iteration
							continue
					except Exception:
						# If scheduling fails, attempt again in the next cycle
						try:
							self._next_auto_close_deadline = time.monotonic() + 3600.0
						except Exception:
							pass

					# If a write is queued, run writer mode
					if not self._write_q.empty():
						batch = None
						try:
							batch = self._write_q.get_nowait()
						except Exception:
							batch = None
						if batch:
							self._mode = "writer"
							# Ensure window is actionable: normalize and push to background
							try:
								if self._page is not None:
									# Normalize window then push to background (match probe timings)
									st0 = _get_window_state(self._page)
									self._logger.info(f"(window) state before writer: {st0}")
									_set_window_state(self._page, "normal", self._logger)
									time.sleep(WINDOW_NORMALIZE_DELAY_SEC)
									st1 = _get_window_state(self._page)
									self._logger.info(f"(window) state after normalize: {st1}")
									# Enlarge viewport to render full grid height
									try:
										vs = self._page.viewport_size
										vw = 1400; vh = 1200
										if isinstance(vs, dict):
											vw = int(vs.get("width", vw)); vh = int(vs.get("height", vh))
										self._prev_viewport = (vw, vh)
										new_h = 6000
										self._page.set_viewport_size({"width": vw, "height": new_h})
										self._logger.info(f"(window) viewport resized to {vw}x{new_h} for writer")
									except Exception:
										pass
									_push_window_to_background(self._logger)
									time.sleep(WINDOW_BACKGROUND_PUSH_DELAY_SEC)
									st2 = _get_window_state(self._page)
									self._logger.info(f"(window) state after background push: {st2}")
							except Exception:
								pass
							self._run_writer_batch(batch)
							self._mode = "reader"
							# Minimize again for reader if configured
							try:
								# Restore viewport first to avoid unminimizing side-effects
								try:
									if self._prev_viewport is not None:
										vw, vh = self._prev_viewport
										self._page.set_viewport_size({"width": vw, "height": vh})
										self._logger.info(f"(window) viewport restored to {vw}x{vh}")
										self._prev_viewport = None
								except Exception:
									pass
								if self._page is not None and MINIMIZE_READER_ON_START:
									_set_window_state(self._page, "minimized", self._logger)
									time.sleep(WINDOW_MINIMIZE_DELAY_SEC)
							except Exception:
								pass

					# Check for refresh request (debounced) only in reader mode; disabled by default
					if self._refresh_on_redis and self._refresh_requested and time.time() >= self._debounce_until:
						self._logger.info("(session) Refresh requested via Redis → reloading page and re-anchoring…")
						self._refresh_requested = False
						try:
							if self._page is not None:
								self._page.reload(wait_until="load")
								time.sleep(INITIAL_POST_NAV_DELAY_SEC)
								_wait_for_table_rendered(self._page)
								# Re-establish anchor and selection
								_select_copy(self._page, self._logger)
								self._has_anchor = True
						except Exception as exc:
							self._logger.warning(f"(session) Refresh path failed: {exc}")
					# Proceed with normal tick
					if self._mode == "reader":
						self.tick_collect()
					else:
						self._logger.debug("(session) Skipping reader tick (writer mode active)")
				except Exception as exc:
					self._consec_failures += 1
					self._logger.warning(f"(session) Background tick failed: {exc}")
					# Force re-create on next loop after too many failures
					if self._consec_failures >= 3:
						self._owner_ident = None
						self._consec_failures = 0
				# sleep remaining time up to interval
				end_ts = time.time() + interval_sec
				while time.time() < end_ts and not self._stop_event.is_set():
					time.sleep(0.05)
		self._thread = threading.Thread(target=_run, name="PMBasicSessionLoop", daemon=True)
		self._thread.start()

	def stop_loop(self) -> None:
		self._stop_event.set()
		thr = self._thread
		if thr and thr.is_alive():
			try:
				thr.join(timeout=2.0)
			except Exception:
				pass
		self._thread = None
		# Stop Redis subscriber
		rt = self._redis_thread
		if rt and rt.is_alive():
			try:
				rt.join(timeout=1.0)
			except Exception:
				pass
		self._redis_thread = None

	def get_snapshot(self) -> Tuple[Optional[pd.DataFrame], str, float]:
		with self._lock:
			df = self._latest_df
			sig = self._latest_sig
			updated = self._last_updated
		return df, sig, updated

	def stop(self) -> None:
		self.stop_loop()
		if self._ctx is not None:
			try:
				_close_window(self._page, self._logger)  # best-effort
			except Exception:
				pass
			try:
				_safe_close_context(self._ctx)
			except Exception:
				pass
		self._ctx = None
		self._page = None

	# ========== Public API: enqueue write ==========
	def enqueue_write(self, items: list[dict]) -> None:
		"""Queue a list of write items: {row, desc|None, qty|None}."""
		if not items:
			return
		self._write_q.put(items)

	# ========== Writer helpers (same-tab) ==========
	def _col_letter_to_index(self, letters: str) -> int:
		letters = letters.upper()
		value = 0
		for ch in letters:
			if 'A' <= ch <= 'Z':
				value = value * 26 + (ord(ch) - ord('A') + 1)
		return max(1, value)

	def _log_active_cell_raw(self, context: str) -> None:
		if self._page is None:
			return
		js = (
			r"""
		() => {
		  const ae = document.activeElement;
		  const gc = (ae && (ae.closest('[role="gridcell"]') || ae.closest('.ag-cell')))
		            || document.querySelector('[role="gridcell"][tabindex="0"]')
		            || document.querySelector('.ag-cell-focus');
		  if (!gc) return null;
		  const rowEl = gc.closest('[row-index]');
		  const riStr = gc.getAttribute('aria-rowindex') || (rowEl ? rowEl.getAttribute('row-index') : null);
		  const ciStr = gc.getAttribute('aria-colindex') || gc.getAttribute('col-id');
		  const ri = riStr != null ? parseInt(riStr, 10) : null;
		  const ci = ciStr != null ? parseInt(ciStr, 10) : null;
		  const t = (gc.innerText || '').trim();
		  return { rowIndex: ri, colIndex: ci, text: t };
		}
		"""
		)
		try:
			info = self._page.evaluate(js)
			self._logger.info(f"(writer) Active cell raw at {context}: {info}")
		except Exception:
			pass

	def _scroll_into_view_and_settle(self, selector: str) -> None:
		if self._page is None:
			return
		loc = self._page.locator(selector).first
		try:
			loc.scroll_into_view_if_needed()
			self._page.evaluate("() => new Promise(r => requestAnimationFrame(()=>r(true)))")
		except Exception:
			pass

	def _ensure_row_in_view(self, raw_row: int) -> None:
		"""Ensure the AG Grid row with given raw_row index is rendered.

		Strategy:
		- If row element exists, return.
		- Ensure grid focus; press End once (likely already at bottom), then PageUp in small steps.
		- If still not found, jump to top-left (Ctrl+ArrowUp/Left) and PageDown in steps.
		- Final fallback: approximate scrollTop via rowHeight and settle.
		"""
		if self._page is None:
			return
		check_js = "(r)=> !!document.querySelector(`div[row-index='${r}']`)"
		try:
			present = bool(self._page.evaluate(check_js, raw_row))
			self._logger.info(f"(writer) ensure_row_in_view start raw_row={raw_row} present={present}")
			if present:
				return
		except Exception:
			pass
		# Ensure focus on grid
		try:
			_focus_grid(self._page, self._logger)
		except Exception:
			pass
		# Try PageUp from bottom
		try:
			self._page.keyboard.press("End")
		except Exception:
			pass
		for i in range(8):
			try:
				self._page.keyboard.press("PageUp")
				self._page.evaluate("() => new Promise(r => requestAnimationFrame(()=>r(true)))")
				exists = bool(self._page.evaluate(check_js, raw_row))
				if exists:
					self._logger.info(f"(writer) ensure_row_in_view found via PageUp after {i+1} steps")
					return
			except Exception:
				break
		# Jump to top-left and PageDown
		try:
			self._page.keyboard.press("Control+ArrowUp")
			self._page.keyboard.press("Control+ArrowLeft")
			exists = bool(self._page.evaluate(check_js, raw_row))
			if exists:
				self._logger.info("(writer) ensure_row_in_view found immediately after jump to top-left")
				return
			for j in range(8):
				self._page.keyboard.press("PageDown")
				self._page.evaluate("() => new Promise(r => requestAnimationFrame(()=>r(true)))")
				exists = bool(self._page.evaluate(check_js, raw_row))
				if exists:
					self._logger.info(f"(writer) ensure_row_in_view found via PageDown after {j+1} steps")
					return
		except Exception:
			pass
		# Fallback: approximate scrollTop by rowHeight
		try:
			js = r"""
(row) => {
  const viewport = document.querySelector('div.ag-center-cols-viewport')
    || document.querySelector('div[role="rowgroup"]')
    || document.querySelector('div.euiDataGrid');
  if (!viewport) return false;
  let rowHeight = 24;
  const sample = viewport.querySelector('[role="row"]');
  if (sample) {
    const r = sample.getBoundingClientRect();
    if (r && r.height > 0) rowHeight = r.height;
  }
  const targetTop = Math.max(0, Math.floor(rowHeight * (row - 2)));
  viewport.scrollTop = targetTop;
  return true;
}
"""
			ok = self._page.evaluate(js, raw_row)
			self._page.evaluate("() => new Promise(r => requestAnimationFrame(()=>r(true)))")
			self._logger.info(f"(writer) ensure_row_in_view fallback scroll applied ok={ok}")
		except Exception:
			pass

	def _fast_click_cell(self, col_letter: str, excel_row: int) -> None:
		if self._page is None:
			return
		grid_col = GRID_COL_DESC if col_letter.upper() == 'C' else GRID_COL_QTY
		grid_row = GRID_OPTION_ROWS.get(excel_row, excel_row - 1)
		sel = f"div[row-index='{grid_row}'] .ag-cell[aria-colindex='{grid_col}']"
		self._logger.info(f"(writer) Click {col_letter}{excel_row} -> rowIndex={grid_row} colIndex={grid_col}")
		try:
			cnt = self._page.locator(sel).count()
			self._logger.info(f"(writer) Target selector count={cnt} for {col_letter}{excel_row}")
		except Exception:
			pass
		self._log_active_cell_raw(f"pre-click {col_letter}{excel_row}")
		# Ensure row is rendered before attempting pointer click
		self._ensure_row_in_view(grid_row)
		self._scroll_into_view_and_settle(sel)
		try:
			self._page.locator(sel).first.click(timeout=400)
		except Exception as exc:
			self._logger.info(f"(writer) Click initial attempt failed for {col_letter}{excel_row}: {exc}")
			self._scroll_into_view_and_settle(sel)
			# Second attempt with force
			try:
				self._page.locator(sel).first.click(timeout=600, force=True)
			except Exception as exc2:
				self._logger.info(f"(writer) Forced click failed for {col_letter}{excel_row}: {exc2} → PageUp fallback")
				# PageUp fallback up to 7 times
				for i in range(7):
					try:
						self._page.keyboard.press("PageUp")
						self._page.evaluate("() => new Promise(r => requestAnimationFrame(()=>r(true)))")
						self._scroll_into_view_and_settle(sel)
						self._page.locator(sel).first.click(timeout=400)
						self._logger.info(f"(writer) Click succeeded after PageUp x{i+1} for {col_letter}{excel_row}")
						break
					except Exception:
						continue
				else:
					self._logger.info(f"(writer) Click failed after PageUp attempts for {col_letter}{excel_row}")
					return
		self._logger.info(f"(writer) Clicked {col_letter}{excel_row}")

	def _set_clipboard(self, text: str) -> bool:
		if self._page is None:
			return False
		js = "(t) => navigator.clipboard.writeText(t)"
		for _ in range(2):
			try:
				self._page.evaluate(js, text)
				return True
			except Exception:
				time.sleep(0.01)
		return False

	def _paste_and_commit(self, text: str) -> None:
		if not self._set_clipboard(text):
			# fallback to typing
			if self._page is not None:
				self._page.keyboard.type(text, delay=0)
				time.sleep(0.01)
			return
		if self._page is None:
			return
		# paste
		self._page.keyboard.press("Control+V")
		if PASTE_COMMIT_WITH_ENTER:
			time.sleep(WRITER_PASTE_SETTLE_SEC)
			self._page.keyboard.press("Enter")
		else:
			time.sleep(WRITER_PASTE_SETTLE_SEC)

	def _reanchor_to_reader_start(self) -> None:
		# Reader's anchor is A3 baseline after initial run: Ctrl+Up, Ctrl+Left, then Down x2
		if self._page is None:
			return
		try:
			self._page.keyboard.press("Escape")
			self._page.focus("body")
		except Exception:
			pass
		self._page.keyboard.press("Control+ArrowUp"); time.sleep(KEY_PAUSE_SEC)
		self._page.keyboard.press("Control+ArrowLeft"); time.sleep(KEY_PAUSE_SEC)

	def _reanchor_to_writer_start(self) -> None:
		"""Anchor to A1 for writer actions (Ctrl+Up, Ctrl+Left)."""
		if self._page is None:
			return
		try:
			self._page.keyboard.press("Escape")
			self._page.focus("body")
		except Exception:
			pass
		self._page.keyboard.press("Control+ArrowUp"); time.sleep(KEY_PAUSE_SEC)
		self._page.keyboard.press("Control+ArrowLeft"); time.sleep(KEY_PAUSE_SEC)

	def _run_writer_batch(self, items: list[dict]) -> None:
		self._logger.info(f"(writer) Starting batch with {len(items)} item(s)")
		# Ensure known anchor first (writer uses A1)
		self._reanchor_to_writer_start()
		# Build per-field actions with diff vs cache
		plan: list[tuple[int, str, str, Optional[str]]] = []  # (row, field, action, value)
		for it in items:
			row = int(it.get("row", 0))
			desc_in = it.get("desc")
			qty_in = it.get("qty")
			prev = self._last_written.get(row, {"desc": None, "qty": None})
			# normalize blanks to None
			desc_norm = (str(desc_in).strip() if desc_in is not None else None) or None
			qty_norm = (str(qty_in).strip() if qty_in is not None else None) or None
			# desc: delete only if cache unknown or previously non-empty
			if desc_norm is None and (row not in self._last_written or (prev.get("desc") is not None)):
				plan.append((row, "desc", "delete", None))
			elif desc_norm is not None and (desc_norm != prev.get("desc")):
				plan.append((row, "desc", "write", desc_norm))
			# qty: delete only if cache unknown or previously non-empty
			if qty_norm is None and (row not in self._last_written or (prev.get("qty") is not None)):
				plan.append((row, "qty", "delete", None))
			elif qty_norm is not None and (qty_norm != prev.get("qty")):
				plan.append((row, "qty", "write", qty_norm))
		self._logger.info(f"(writer) Planned actions: {plan}")
		# Execute plan
		for row, field, action, value in plan:
			col_letter = 'C' if field == 'desc' else 'D'
			self._fast_click_cell(col_letter, row)
			if action == 'delete':
				if self._page is not None:
					self._page.keyboard.press("Delete")
					time.sleep(0.01)
			else:  # write
				self._paste_and_commit(value or "")
		# Final small settle to ensure commit
		time.sleep(WRITER_FINAL_SETTLE_SEC)
		# Update cache with intended final state for rows present in items
		for it in items:
			row = int(it.get("row", 0))
			desc_in = it.get("desc")
			qty_in = it.get("qty")
			desc_norm = (str(desc_in).strip() if desc_in is not None else None) or None
			qty_norm = (str(qty_in).strip() if qty_in is not None else None) or None
			prev = self._last_written.get(row, {"desc": None, "qty": None})
			fields_in_plan = [f for r, f, _, _ in plan if r == row]
			new_desc = desc_norm if ("desc" in fields_in_plan) else prev.get("desc")
			new_qty = qty_norm if ("qty" in fields_in_plan) else prev.get("qty")
			self._last_written[row] = {"desc": new_desc, "qty": new_qty}
		# Re-anchor and perform initial selection to resume reader
		self._reanchor_to_reader_start()
		if self._page is not None:
			try:
				_select_copy(self._page, self._logger)
				self._has_anchor = True
			except Exception:
				pass


def _wait_for_user_login(logger: logging.Logger) -> None:
	logger.info("If login is required, complete it in the opened Edge window.")
	logger.info("Press Enter to continue …")
	try:
		input("")
	except Exception:
		time.sleep(15)


def main() -> int:
	parser = argparse.ArgumentParser(description="Pricing Monkey Playwright basic runner")
	parser.add_argument("--use-default-profile", action="store_true", help="Use the system default Edge profile")
	parser.add_argument(
		"--profile-dir-name",
		type=str,
		default=None,
		help="Edge profile directory name when using default user data dir (e.g., 'Default', 'Profile 1')",
	)
	args = parser.parse_args()
	use_default_profile = bool(args.use_default_profile)
	runner = PMBasicRunner(use_default_profile=use_default_profile)
	df = runner.collect_once()
	print(f"Collected DataFrame shape: {df.shape}")
	if not df.empty:
		print(df.head(10).to_string(index=False))
	return 0


if __name__ == "__main__":
	sys.exit(main())


