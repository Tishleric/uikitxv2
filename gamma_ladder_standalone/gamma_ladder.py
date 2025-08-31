import pandas as pd
import numpy as np

### Get Live Px and Create Px Ladder

## Get Live TY Px
import pandas as pd
import sys
import os
from datetime import datetime, timedelta, date
import time
import math
import pickle
import requests
import subprocess
from io import StringIO
import re
import numpy as np
import glob
# ADDED: glob used to discover latest PricingMonkey CSV for today

_TT_RE = re.compile(r"^\s*([+-]?\d+)\s*[''`\-\s]\s*(\d{1,3})\s*$")

# ADDED: Auto-refresh wrapper (injects meta tag for 1s reload)
def _wrap_with_meta_refresh(html: str, seconds: int = 1) -> str:
    return f"<!DOCTYPE html><html><head><meta http-equiv=\"refresh\" content=\"{seconds}\"></head><body>{html}</body></html>"

# ADDED: Atomic file write (tmp + replace) to avoid partial reads
def _atomic_write_text(path: str, text: str, encoding: str = "utf-8") -> None:
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding=encoding) as f:
        f.write(text)
    os.replace(tmp_path, path)

def zn_to_decimal(value):

    """Converts 32nd Format to decimal format"""

    s = str(value).strip()
    if not s:
        return math.nan

    # Remove thousands separators and exotic whitespace
    s = s.replace(",", "").replace("\u2009", "").replace("\u00A0", " ")

    m = _TT_RE.match(s)
    if m:
        whole = int(m.group(1))
        frac = m.group(2)
        if len(frac) == 3:
            # XY5 -> XY in 32nds, +1/64 if last digit is 5
            thirty2 = int(frac[:2])
            half = 1 if frac[2] == "5" else 0
        elif len(frac) == 2:
            thirty2 = int(frac)
            half = 0
        elif len(frac) == 1:
            thirty2 = int(frac)
            half = 0
        else:
            return math.nan
        sixty4 = 2 * thirty2 + half
        return whole + sixty4 / 64.0


def decimal_to_zn(x: float) -> str:
    """Convert decimal prices back to the CBOT 32nds string format."""
    pts = int(x)
    # Multiply by 32 **before** taking int to avoid FP rounding surprises
    remainder = int((x - pts) * 320)  # keep three decimals, good enough
    if remainder//100 == 0 and remainder//10 != 0:
        remainder = f"0{remainder}"
    elif remainder//100 == 0 and remainder//10 == 0:
        remainder = f"00{remainder}"
    return f"{pts}'{remainder}"


def get_current_price(TICKER="ZN") -> float:
    """Get the latest valid price from the price streaming CSV without loading the full file."""
    try:

        # Base folder where files are stored
        base_dir = r"Y:\\Archive"

        # Today's date in YYYY-MM-DD format
        today_str = date.today().strftime("%Y-%m-%d")

        # Build full file path
        file_path = os.path.join(base_dir, f"Live_TT_{TICKER}_prices_{today_str}.csv")

        df_tail = pd.read_csv(file_path)

        # Drop NaNs in price column
        df_tail = df_tail.dropna(subset=["price"])

        if df_tail.empty:
            return 0  # No valid prices found

        # Get the last valid price
        current_price = df_tail["price"].iloc[-1]

        # Ensure float type
        if isinstance(current_price, str):
            current_price = float(current_price)

        return float(current_price)
    
    except Exception as e:
        print(f"Error reading price streaming: {e}")
        return 0


def create_price_array(current_price: float) -> np.ndarray:
    """Create price array with 4 basis points up/down, spaced by 1/64."""
    # 1 basis point = 1/16 = 0.0625
    # 4 basis points = 4/16 = 0.25
    # Spacing = 1/64 = 0.015625
    
    spacing = 1/64
    range_bps = 4 * (1/16)  # 4 basis points = 0.25
    
    # Calculate number of steps (4 bps / (1/64) = 16 steps each way)
    steps = int(range_bps / spacing)
    
    # Create array from (current - 4bps) to (current + 4bps)
    return np.arange(current_price - range_bps, current_price + range_bps + spacing, spacing)


# ADDED: Selects today's latest PricingMonkey CSV by modification time
def _get_latest_pm_file() -> str | None:
    base_dir = r"Z:\\Hanyu\\FiveMinuteMonkey"
    today_str = date.today().strftime("%m-%d-%Y")
    today_folder = os.path.join(base_dir, today_str)
    pattern = os.path.join(today_folder, "*.csv")
    files = []
    try:
        files = [p for p in glob.glob(pattern)]
    except Exception:
        return None
    if not files:
        return None
    return max(files, key=os.path.getmtime)


# ADDED: Wrapped original notebook logic into a function for reuse by the live loop
def build_html_once() -> str:
    current_price = get_current_price()
    curpx = decimal_to_zn(current_price)
    price_array = create_price_array(current_price)[::-1]
    px_array = pd.Series(np.vectorize(decimal_to_zn)(price_array))
    print(f"Current price: {curpx}")

    # --- Build ladder dataframe ---
    ladder_df = pd.DataFrame({
        "Price lvl (dec)": price_array,
        "Price lvl (zn)": np.vectorize(decimal_to_zn)(price_array)
    })
    ladder_df["bps away"] = (ladder_df["Price lvl (dec)"] - current_price) / 0.0625
    ladder_df["ticks_away"] = (ladder_df["bps away"].abs() * 4)
    ladder_df["target_abs_delta"] = 1.0 / ladder_df["ticks_away"]
    ladder_df.loc[ladder_df["target_abs_delta"] > 1, "target_abs_delta"] = 1.0
    ladder_df["Chosen Type"] = np.where(
        ladder_df["bps away"] > 0, "Put",
        np.where(ladder_df["bps away"] < 0, "Call", None)
    )

    # Load latest PM CSV
    latest_file = _get_latest_pm_file()
    if not latest_file:
        raise FileNotFoundError("No PricingMonkey CSV found for today")
    print(f"Loading latest file: {latest_file}")
    df = pd.read_csv(latest_file)

    def parse_cme_ticks(x):
        if pd.isna(x):
            return None
        if isinstance(x, (int, float)):
            return int(x)
        s = str(x).strip()
        if "-" in s:
            parts = s.split("-")
            if len(parts) == 2:
                try:
                    return int(parts[1])
                except:
                    return None
        try:
            return int(float(s))
        except:
            return None

    def preprocess_options(df):
        df = df[df['Trade Description'].notna() & ~df['Trade Description'].str.contains("#", na=False)].copy()
        df['Type'] = df['Trade Description'].str.extract(r'(?i)(call|put)')[0].str.title()
        df['Ordinal'] = df['Trade Description'].str.extract(r'(\d+(?:st|nd|rd|th))')[0]
        df['Bucket'] = df['Ordinal'] + ' ' + df['Type']
        if '% Delta' in df.columns:
            df['% Delta'] = (
                df['% Delta']
                .astype(str)
                .str.replace('%','', regex=False)
                .replace('nan','')
            )
            df['% Delta'] = pd.to_numeric(df['% Delta'], errors='coerce') / 100.0
            df.rename(columns={'% Delta': '%Delta'}, inplace=True)
        if 'Bid' in df.columns:
            df['Bid'] = df['Bid'].apply(parse_cme_ticks)
        numeric_cols = ['Gamma', 'Theta', 'NPV', 'DV01 Gamma', 'DV01']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=['Bid','%Delta'])
        return df

    raw_df = df.copy()
    opts = preprocess_options(raw_df)
    calls = opts[(opts['Type'] == 'Call') & opts['Ordinal'].isin(['2nd','3rd','4th','5th'])].copy()
    puts  = opts[(opts['Type'] == 'Put')  & opts['Ordinal'].isin(['2nd','3rd','4th','5th'])].copy()

    def closest_options(df, target_delta, n=2):
        if df.empty or pd.isna(target_delta):
            return pd.DataFrame()
        df = df.assign(dist=(df["%Delta"] - target_delta).abs())
        return df.nsmallest(n, "dist")

    rows = []
    target_gamma = 500
    for _, r in ladder_df.iterrows():
        tgt_abs = r["target_abs_delta"]
        if r["bps away"] == 0:
            rows.append({
                "Price lvl (zn)": r["Price lvl (zn)"],
                "Price lvl (dec)": r["Price lvl (dec)"],
                "bps away": r["bps away"],
                "ticks_away": np.nan,
                "target_delta": np.nan,
                "Chosen Type": "Anchor",
                "IsCurrent": True
            })
            continue
        if r["Chosen Type"] == "Put":
            subset = puts
            target = -tgt_abs
        else:
            subset = calls
            target = +tgt_abs
        chosen = closest_options(subset, target, n=2).reset_index(drop=True)
        out = {
            "Price lvl (zn)": r["Price lvl (zn)"],
            "Price lvl (dec)": r["Price lvl (dec)"],
            "bps away": r["bps away"],
            "ticks_away": r["ticks_away"],
            "target_delta": target,
            "Chosen Type": r["Chosen Type"],
            "IsCurrent": False
        }
        for i, opt in chosen.iterrows():
            j = i+1
            out[f"Opt{j}_Desc"]   = opt["Trade Description"]
            out[f"Opt{j}_Strike"] = opt["Strike"]
            out[f"Opt{j}_%Delta"] = opt["%Delta"]
            out[f"Opt{j}_Bid"]    = opt.get("Bid")
            out[f"Opt{j}_IV"]    = opt.get("Implied Vol (Daily BP)")
            dv01_gamma = opt.get("DV01 Gamma")
            if pd.notna(dv01_gamma) and dv01_gamma != 0:
                dv01_gamma_scaled = dv01_gamma * 1000
                lots = int(target_gamma / dv01_gamma_scaled)
            else:
                dv01_gamma_scaled = 0.0
                lots = 0
            out[f"Opt{j}_DV01_Gamma"] = lots * dv01_gamma_scaled
            out[f"Opt{j}_Qty"]       = lots
            out[f"Opt{j}_DV01"]       = lots * (opt.get("DV01") or 0) * 1000
            out[f"Opt{j}_fut_equiv"]  = int(out[f"Opt{j}_DV01"]/62.5) if out[f"Opt{j}_DV01"] else 0
            bid_ticks = opt.get("Bid") or 0
            npv_per_lot = bid_ticks * 15.625
            npv_total = lots * npv_per_lot
            out[f"Opt{j}_NPV"] = int(round(npv_total))
            biz_days = opt.get("Biz Days")
            if pd.notna(biz_days) and biz_days > 0:
                out[f"Opt{j}_Theta"] = int(round(npv_total / biz_days))
            else:
                out[f"Opt{j}_Theta"] = 0
        rows.append(out)

    ladder_with_opts = pd.DataFrame(rows)

    df_out = ladder_with_opts.copy()
    df_export = df_out.drop(columns=["Price lvl (dec)", "ticks_away","bps away", "target_delta"]).copy()

    def clean_percent(col):
        return (
            df_export[col]
            .astype(str)
            .str.replace("%", "", regex=False)
            .str.strip()
            .replace("nan", None)
            .astype(float)
        )

    def clean_numeric(col):
        return (
            df_export[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
            .replace("nan", None)
            .astype(float)
        )

    for col in df_export.columns:
        if "%Delta" in col:
            df_export[col] = clean_percent(col)
        elif "Strike" in col or "bps away" in col:
            df_export[col] = clean_numeric(col)
        elif any(k in col for k in ["Bid","Lots","DV01","fut_equiv","NPV","Theta"]):
            df_export[col] = clean_numeric(col)

    def highlight_anchor(row):
        if row.get("IsCurrent", False):
            return ['background-color: red; color: white; font-weight: bold;'] * len(row)
        return [''] * len(row)

    styled = (
        df_export.style
        .apply(highlight_anchor, axis=1)
        .format({"bps away": "{:.0f}"})
        .format({col: "{:.1%}" for col in df_export.columns if "%Delta" in col})
        .format({col: "{:.2f}" for col in df_export.columns if "Strike" in col})
        .format({col: "{:,.0f}" for col in df_export.columns 
                 if any(k in col for k in ["Bid","Lots","DV01","fut_equiv","NPV","Theta"])})
        .set_table_styles(
            [
                {"selector": "th", "props": [("border", "1px solid black"),
                                                 ("padding", "4px"),
                                                 ("position", "sticky"),
                                                 ("top", "0"),
                                                 ("background-color", "#f2f2f2"),
                                                 ("z-index", "2")]},
                {"selector": "td", "props": [("border", "1px solid black"),
                                                 ("padding", "4px"),
                                                 ("text-align", "center"),
                                                 ("font-family", "monospace")]}
            ]
        )
    )

    html_out = styled.hide(axis="index").hide(axis="columns", subset=["IsCurrent"]).to_html()
    # ADDED: Inject auto-refresh and write HTML atomically
    final_html = _wrap_with_meta_refresh(html_out, seconds=1)
    _atomic_write_text("Y:\\Gamma Screener\\option_ladder.html", final_html, encoding="utf-8")
    print("✅ HTML ladder saved with correct formatting")
    return final_html


# ADDED: TT change detection (path, mtime, last price)
def _get_tt_state() -> tuple:
    base_dir = r"Y:\\Archive"
    ticker = "ZN"
    today_str = date.today().strftime("%Y-%m-%d")
    file_path = os.path.join(base_dir, f"Live_TT_{ticker}_prices_{today_str}.csv")
    try:
        mtime = os.path.getmtime(file_path)
    except Exception:
        mtime = 0.0
    price_val = 0.0
    try:
        df_tail = pd.read_csv(file_path)
        df_tail = df_tail.dropna(subset=["price"])
        if not df_tail.empty:
            price_val = float(df_tail["price"].iloc[-1])
    except Exception:
        pass
    return (file_path, mtime, price_val)


# ADDED: PM change detection (path, mtime)
def _get_pm_state() -> tuple:
    latest = _get_latest_pm_file()
    if not latest:
        return (None, 0.0)
    try:
        return (latest, os.path.getmtime(latest))
    except Exception:
        return (latest, 0.0)


if __name__ == "__main__":
    # Initial build
    try:
        build_html_once()
    except Exception as e:
        print(f"Initial build failed: {e}")

    last_tt = _get_tt_state()
    last_pm = _get_pm_state()

    # ADDED: 1 Hz polling loop (rebuilds only on change)
    while True:
        try:
            tt_now = _get_tt_state()
            pm_now = _get_pm_state()
            if tt_now != last_tt or pm_now != last_pm:
                print("Change detected → rebuild")
                build_html_once()
                last_tt, last_pm = tt_now, pm_now
        except Exception as e:
            print(f"Loop error: {e}")
        time.sleep(1)
