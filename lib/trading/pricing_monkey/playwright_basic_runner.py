from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional, Tuple
import threading
import hashlib

import pandas as pd
from playwright.sync_api import BrowserContext, Page, sync_playwright
import psutil


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
			viewport={"width": 1400, "height": 900},
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

	# Precise key-sequence per spec: Tab×5, Down×3, then Ctrl+Shift+Down and Ctrl+Shift+Right
	# Anchor to first cell region
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


def _reselect_and_copy(page: Page, logger: logging.Logger) -> Optional[str]:
	_focus_grid(page, logger)
	# Reuse the initial robust selection path
	text = _select_copy(page, logger)
	if text and ("Loading..." not in text):
		return text
	# Fallback: try Ctrl+A within focused grid
	try:
		page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=PM_BASIC_URL)
	except Exception:
		pass
	try:
		page.keyboard.press("Control+A"); time.sleep(0.2)
		page.keyboard.press("Control+C"); time.sleep(0.2)
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
		self._ready_event: threading.Event = threading.Event()
		self._consec_failures: int = 0

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

	def _df_signature(self, df: pd.DataFrame) -> str:
		try:
			payload = df.to_json(orient="split", date_format="iso").encode("utf-8")
			return hashlib.md5(payload).hexdigest()
		except Exception:
			return f"{df.shape[0]}x{df.shape[1]}:{int(time.time())}"

	def tick_collect(self) -> pd.DataFrame:
		if self._page is None:
			raise RuntimeError("Session not started")
		page = self._page
		text: Optional[str] = None
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
			candidate_df = pd.DataFrame()
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
					self.tick_collect()
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


