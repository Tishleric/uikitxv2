import argparse
import os
import math
from typing import List, Dict

import numpy as np
import pandas as pd


def _collect_plex_csvs(root_dir: str) -> List[str]:
    files: List[str] = []
    for dirpath, _dirnames, filenames in os.walk(root_dir):
        for fname in filenames:
            if not fname.endswith("_Plex.csv"):
                continue
            if "outliers" in fname:
                continue
            files.append(os.path.join(dirpath, fname))
    files.sort()
    return files


def analyze_accuracy_data(input_dir: str, output_dir: str, thresholds: List[float], epsilons: List[float]) -> Dict[str, object]:
    file_list = _collect_plex_csvs(input_dir)
    if not file_list:
        raise FileNotFoundError(f"No Plex CSV files found under {input_dir}")

    # Read and concatenate
    df_all: List[pd.DataFrame] = []
    for fpath in file_list:
        try:
            chunk = pd.read_csv(fpath)
        except Exception:
            chunk = pd.read_csv(fpath, engine="python")
        chunk["source_file"] = os.path.basename(fpath)
        df_all.append(chunk)
    df = pd.concat(df_all, ignore_index=True)

    # Coerce numerics
    numeric_cols = [
        "underlying_future_price",
        "strike",
        "moneyness",
        "adjtheor",
        "vtexp",
        "IV_binary_search",
        "recalculated_price_binary_search",
        "pnl_explained",
        "pnl_explained_2nd_order",
        "error",
        "error_2nd_order",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    total_rows = len(df)

    # Manifest for hygiene decisions
    base_cols = [
        "source_file",
        "timestamp",
        "underlying_future_price",
        "strike",
        "itype",
        "moneyness",
        "adjtheor",
        "vtexp",
        "IV_binary_search",
        "error_2nd_order",
    ]
    present_cols = [c for c in base_cols if c in df.columns]
    manifest = df[present_cols].copy()
    manifest["keep"] = True
    manifest["drop_reason"] = ""

    # Finite-only error policy
    mask_nonfinite = ~np.isfinite(df["error_2nd_order"])
    manifest.loc[mask_nonfinite, ["keep", "drop_reason"]] = [False, "error_nonfinite"]

    # Known corrupt spike
    if "timestamp" in df.columns:
        mask_known = (df["timestamp"] == "2025-08-21 09:24:25") & manifest["keep"]
        manifest.loc[mask_known, ["keep", "drop_reason"]] = [False, "known_outlier"]

    # Sanity ranges
    if "underlying_future_price" in df.columns:
        mask_underlying = manifest["keep"] & (
            (df["underlying_future_price"] < 90) | (df["underlying_future_price"] > 150)
        )
        manifest.loc[mask_underlying, ["keep", "drop_reason"]] = [False, "underlying_out_of_range"]
    if "vtexp" in df.columns:
        mask_vtexp = manifest["keep"] & ((df["vtexp"] <= 0) | (df["vtexp"] > 1))
        manifest.loc[mask_vtexp, ["keep", "drop_reason"]] = [False, "vtexp_out_of_range"]
    # NOTE: IV filter removed per request – extremely high IVs can occur; do not drop by IV.
    if "moneyness" in df.columns:
        mask_mny = manifest["keep"] & (df["moneyness"].abs() > 5)
        manifest.loc[mask_mny, ["keep", "drop_reason"]] = [False, "moneyness_out_of_range"]

    total_dropped = int((~manifest["keep"]).sum())
    drop_reasons = manifest.loc[~manifest["keep"], "drop_reason"].value_counts().to_dict()

    df_clean = df[manifest["keep"]].copy().reset_index(drop=True)

    os.makedirs(output_dir, exist_ok=True)
    manifest.to_csv(os.path.join(output_dir, "clean_manifest.csv"), index=False)

    # Binning
    mon_edges = [-5, -2, -1, -0.5, -0.25, -0.125, -0.0625, -0.015625, 0, 0.015625, 0.05, 0.125, float("inf")]
    mon_labels = [
        "(-5,-2]",
        "(-2,-1]",
        "(-1,-0.5]",
        "(-0.5,-0.25]",
        "(-0.25,-0.125]",
        "(-0.125,-0.0625]",
        "(-0.0625,-0.015625]",
        "(-0.015625,0]",
        "(0,0.015625]",
        "(0.015625,0.05]",
        "(0.05,0.125]",
        "(>0.125)",
    ]
    if "moneyness" in df_clean.columns:
        df_clean["moneyness_bin"] = pd.cut(
            df_clean["moneyness"], bins=mon_edges, labels=mon_labels, include_lowest=True
        )

    vte_edges = [0, 0.002, 0.01, 0.05, 1.0]
    vte_labels = ["<0.002", "0.002-0.01", "0.01-0.05", ">=0.05"]
    if "vtexp" in df_clean.columns:
        df_clean["vtexp_bin"] = pd.cut(df_clean["vtexp"], bins=vte_edges, labels=vte_labels, right=False)

    adj_edges = [0, 0.015625, 0.05, 0.125, float("inf")]
    adj_labels = ["<=0.015625", "0.015625-0.05", "0.05-0.125", ">0.125"]
    if "adjtheor" in df_clean.columns:
        df_clean["adj_bin"] = pd.cut(
            df_clean["adjtheor"], bins=adj_edges, labels=adj_labels, include_lowest=True
        )

    # Success metrics (percentage): treat error_2nd_order as percentage points
    # Primary success definition: |error_2nd_order| ≤ 5 (% points)
    df_clean["success_abs"] = df_clean["error_2nd_order"].abs() <= 5

    # Threshold sweep
    sweep_records: List[Dict[str, object]] = []
    # Define OTM subset mask (calls OTM when moneyness < 0, puts OTM when moneyness > 0).
    if "moneyness" in df_clean.columns:
        if "itype" in df_clean.columns:
            it = df_clean["itype"].astype(str).str.upper()
            mask_otm_global = ((it == "C") & (df_clean["moneyness"] < 0)) | (
                (it == "P") & (df_clean["moneyness"] > 0)
            )
        else:
            # Fallback: if type missing, assume calls-only dataset → use moneyness < 0
            mask_otm_global = df_clean["moneyness"] < 0
    else:
        mask_otm_global = pd.Series(False, index=df_clean.index)
    for tau in thresholds:
        # Non-strict compare so threshold == 0 acts as true "no AdjTheor filter" for non-negative values
        hi_mask = df_clean["adjtheor"] >= tau
        lo_mask = ~hi_mask
        count_total = len(df_clean)
        count_hi = int(hi_mask.sum())
        count_lo = int(lo_mask.sum())
        success_hi_count = int((df_clean["success_abs"] & hi_mask).sum())
        success_lo_count = int((df_clean["success_abs"] & lo_mask).sum())
        success_overall = (success_hi_count + success_lo_count) / count_total if count_total else math.nan
        success_hi_rate = success_hi_count / count_hi if count_hi else math.nan
        success_lo_rate = success_lo_count / count_lo if count_lo else math.nan

        # OTM-only success within high-price region
        hi_otm_mask = hi_mask & mask_otm_global
        count_hi_otm = int(hi_otm_mask.sum())
        success_hi_otm_count = int((df_clean["success_abs"] & hi_otm_mask).sum())
        success_hi_otm_rate = success_hi_otm_count / count_hi_otm if count_hi_otm else math.nan

        mneg_mask = df_clean["moneyness"] < 0
        mpos_mask = ~mneg_mask
        count_mneg = int(mneg_mask.sum())
        count_mpos = int(mpos_mask.sum())
        success_any = df_clean["success_abs"]
        success_mneg = int((success_any & mneg_mask).sum())
        success_mpos = int((success_any & mpos_mask).sum())
        success_mneg_rate = success_mneg / count_mneg if count_mneg else math.nan
        success_mpos_rate = success_mpos / count_mpos if count_mpos else math.nan

        # vtexp categories
        vcat_rates: Dict[str, float] = {}
        for label in vte_labels:
            vmask = df_clean["vtexp_bin"] == label
            cnt_v = int(vmask.sum())
            if cnt_v:
                succ_v = int((success_any & vmask).sum())
                vcat_rates[label] = succ_v / cnt_v
            else:
                vcat_rates[label] = math.nan

        if (not math.isnan(success_mneg_rate)) and (not math.isnan(success_mpos_rate)):
            success_macro = 0.5 * (success_mneg_rate + success_mpos_rate)
        else:
            success_macro = math.nan

        # 95% CI for success_hi
        if not math.isnan(success_hi_rate):
            p = success_hi_rate
            n = count_hi
            se = math.sqrt(p * (1 - p) / n) if n and (0 < p < 1) else 0.0
            ci_lower = max(0.0, p - 1.96 * se)
            ci_upper = min(1.0, p + 1.96 * se)
        else:
            ci_lower = math.nan
            ci_upper = math.nan

        rec: Dict[str, object] = {
            "threshold": tau,
            "count_total": count_total,
            "count_hi": count_hi,
            "count_lo": count_lo,
            "success_overall": success_overall,
            "success_hi": success_hi_rate,
            "success_hi_otm": success_hi_otm_rate,
            "count_hi_otm": count_hi_otm,
            "success_lo": success_lo_rate,
            "success_mneg": success_mneg_rate,
            "success_mpos": success_mpos_rate,
            "success_macro": success_macro,
            "success_hi_ci_lower": ci_lower,
            "success_hi_ci_upper": ci_upper,
        }
        for label in vte_labels:
            rec[f"success_{label}"] = vcat_rates[label]
        sweep_records.append(rec)

    df_sweep = pd.DataFrame(sweep_records)
    df_sweep.to_csv(os.path.join(output_dir, "threshold_sweep.csv"), index=False)

    # Recommended tau*: smallest tau with ≥95% success in high region
    recommended_tau = None
    for tau in thresholds:
        row = df_sweep[df_sweep["threshold"] == tau]
        if not row.empty:
            sr = float(row["success_hi"].iloc[0])
            if not math.isnan(sr) and sr >= 0.95:
                recommended_tau = tau
                break

    # Recommended tau for OTM-only (if available)
    recommended_tau_otm = None
    if "success_hi_otm" in df_sweep.columns:
        for tau in thresholds:
            row = df_sweep[df_sweep["threshold"] == tau]
            if not row.empty:
                sr = float(row["success_hi_otm"].iloc[0])
                if not math.isnan(sr) and sr >= 0.95:
                    recommended_tau_otm = tau
                    break

    # Summary by bins
    df_clean["success_flag"] = df_clean["error_2nd_order"].abs() <= 5
    agg = (
        df_clean.groupby(["moneyness_bin", "vtexp_bin", "adj_bin"], dropna=False, observed=False)["success_flag"]
        .agg(["sum", "count"])  # type: ignore
        .reset_index()
    )
    agg.rename(columns={"sum": "success_count", "count": "total_count"}, inplace=True)
    agg["success_rate"] = agg["success_count"] / agg["total_count"]
    agg.to_csv(os.path.join(output_dir, "summary_success_by_bins.csv"), index=False)

    # DOTM epsilon analysis
    dotm_mask_125 = df_clean["moneyness"] <= -0.125
    dotm_mask_0625 = df_clean["moneyness"] <= -0.0625
    dotm_records: List[Dict[str, object]] = []
    for eps in epsilons:
        succ_125 = ((df_clean["error_2nd_order"].abs() <= (df_clean["adjtheor"] + eps)) & dotm_mask_125).sum()
        denom_125 = int(dotm_mask_125.sum())
        rate_125 = succ_125 / denom_125 if denom_125 else math.nan
        succ_0625 = ((df_clean["error_2nd_order"].abs() <= (df_clean["adjtheor"] + eps)) & dotm_mask_0625).sum()
        denom_0625 = int(dotm_mask_0625.sum())
        rate_0625 = succ_0625 / denom_0625 if denom_0625 else math.nan
        dotm_records.append(
            {
                "epsilon": eps,
                "success_moneyness_le_-0.0625": rate_0625,
                "success_moneyness_le_-0.125": rate_125,
            }
        )
    pd.DataFrame(dotm_records).to_csv(os.path.join(output_dir, "dotm_epsilon.csv"), index=False)

    # Inflection candidates by vtexp bin (95% target crossing)
    inflection_list = [{"category": "All", "threshold_for_95pct": recommended_tau}]
    if recommended_tau_otm is not None:
        inflection_list.append({"category": "OTM_only", "threshold_for_95pct": recommended_tau_otm})
    for label in vte_labels:
        col = f"success_{label}"
        valid = df_sweep[(df_sweep[col] >= 0.95) & (~df_sweep[col].isna())]
        thr_val = float(valid["threshold"].iloc[0]) if not valid.empty else math.nan
        inflection_list.append({"category": f"vtexp_{label}", "threshold_for_95pct": thr_val})
    pd.DataFrame(inflection_list).to_csv(os.path.join(output_dir, "inflection_candidates.csv"), index=False)

    return {
        "total_rows": total_rows,
        "dropped": total_dropped,
        "drop_reasons": drop_reasons,
        "recommended_threshold": recommended_tau,
    }


def main() -> None:
    # Defaults allow running with no args
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    default_root = os.path.join(
        base_path,
        "lib",
        "trading",
        "bond_future_options",
        "data_validation",
        "accuracy_validation",
    )
    default_out = os.path.join(base_path, "data", "output", "accuracy_validation")

    parser = argparse.ArgumentParser(description="Analyze accuracy frontier from Plex validation data")
    parser.add_argument(
        "--root",
        type=str,
        default=default_root,
        help="Root directory containing *Plex.csv files (recursed)",
    )
    parser.add_argument(
        "--outdir", type=str, default=default_out, help="Output directory for results CSVs"
    )
    parser.add_argument(
        "--min-adjtheor-grid",
        type=str,
        default=(
            "0.0,0.0005,0.001,0.0015,0.002,0.0025,0.003,0.0035,0.004,0.0045,0.005,"
            "0.006,0.007,0.008,0.009,0.01,0.011,0.012,0.013,0.014,0.015,0.015625,"
            "0.016,0.017,0.018,0.019,0.02,0.021,0.022,0.023,0.024,0.025,0.026,0.027,0.028,0.029,0.03,"
            "0.04,0.05,0.07,0.1"
        ),
        help="Comma-separated grid of minimum adjtheor thresholds to test",
    )
    parser.add_argument(
        "--epsilon-grid",
        type=str,
        default="0.0078125,0.015625,0.03125",
        help="Comma-separated list of epsilon values for DOTM analysis",
    )
    args = parser.parse_args()

    thresholds = [float(x) for x in args.min_adjtheor_grid.split(",")]
    # Ensure a true no-filter point exists even if the caller didn't pass 0 explicitly
    if 0.0 not in thresholds:
        thresholds.append(0.0)
    # Densify near-zero region to resolve the steep change between 0 and 0.0005
    dense_near_zero = np.linspace(0.0, 0.0005, num=101).tolist()
    thresholds = sorted(set(thresholds + dense_near_zero))
    epsilons = [float(x) for x in args.epsilon_grid.split(",")]
    os.makedirs(args.outdir, exist_ok=True)
    results = analyze_accuracy_data(args.root, args.outdir, thresholds, epsilons)
    print("Analysis complete.")
    print(f"Total rows processed: {results['total_rows']}")
    print(f"Rows dropped: {results['dropped']} (Reasons: {results['drop_reasons']})")
    if results["recommended_threshold"] is not None:
        print(f"Recommended adjtheor threshold: {results['recommended_threshold']:.6f}")
    else:
        print("No threshold in grid achieved ≥95% success in high-price region.")


if __name__ == "__main__":
    main()


