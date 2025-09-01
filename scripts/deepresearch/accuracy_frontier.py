# Path: tools/analysis/accuracy_frontier.py
import argparse
import pandas as pd
import numpy as np
import os
import math

def analyze_accuracy_data(input_dir, output_dir, thresholds, epsilons):
    # List all files in input_dir that end with "_Plex.csv" (exclude outlier files)
    file_list = []
    for fname in os.listdir(input_dir):
        if fname.endswith("_Plex.csv") and "outliers" not in fname:
            file_list.append(os.path.join(input_dir, fname))
    file_list.sort()
    if not file_list:
        raise FileNotFoundError(f"No Plex CSV files found in directory {input_dir}")
    # Read and concatenate all CSVs
    df_all = []
    for f in file_list:
        try:
            df_chunk = pd.read_csv(f)
        except Exception:
            df_chunk = pd.read_csv(f, engine='python')
        df_chunk['source_file'] = os.path.basename(f)
        df_all.append(df_chunk)
    df = pd.concat(df_all, ignore_index=True)
    # Coerce numeric fields (convert "inf" or non-numeric to NaN)
    numeric_cols = ['underlying_future_price','strike','moneyness','adjtheor','vtexp',
                    'IV_binary_search','recalculated_price_binary_search',
                    'pnl_explained','pnl_explained_2nd_order','error','error_2nd_order']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    # Data cleaning according to policies
    total_rows = len(df)
    manifest = df[['source_file','timestamp','underlying_future_price','strike',
                   'itype','moneyness','adjtheor','vtexp','IV_binary_search','error_2nd_order']].copy()
    manifest['keep'] = True
    manifest['drop_reason'] = ""
    # Drop conditions:
    mask_nonfinite = ~np.isfinite(df['error_2nd_order'])
    manifest.loc[mask_nonfinite, 'keep'] = False
    manifest.loc[mask_nonfinite, 'drop_reason'] = "error_nonfinite"
    mask_outlier = np.isfinite(df['error_2nd_order']) & (df['error_2nd_order'].abs() > 50)
    mask_outlier = mask_outlier & manifest['keep']
    manifest.loc[mask_outlier, 'keep'] = False
    manifest.loc[mask_outlier, 'drop_reason'] = "error_outlier"
    mask_known = (df['timestamp'] == '2025-08-21 09:24:25') & manifest['keep']
    manifest.loc[mask_known, 'keep'] = False
    manifest.loc[mask_known, 'drop_reason'] = "known_outlier"
    mask_underlying = manifest['keep'] & ((df['underlying_future_price'] < 90) | (df['underlying_future_price'] > 150))
    manifest.loc[mask_underlying, 'keep'] = False
    manifest.loc[mask_underlying, 'drop_reason'] = "underlying_out_of_range"
    mask_vtexp = manifest['keep'] & ((df['vtexp'] <= 0) | (df['vtexp'] > 1))
    manifest.loc[mask_vtexp, 'keep'] = False
    manifest.loc[mask_vtexp, 'drop_reason'] = "vtexp_out_of_range"
    if 'IV_binary_search' in df.columns:
        mask_iv = manifest['keep'] & ((df['IV_binary_search'] <= 0) | (df['IV_binary_search'] > 200))
        manifest.loc[mask_iv, 'keep'] = False
        manifest.loc[mask_iv, 'drop_reason'] = "iv_out_of_range"
    mask_moneyness = manifest['keep'] & (df['moneyness'].abs() > 5)
    manifest.loc[mask_moneyness, 'keep'] = False
    manifest.loc[mask_moneyness, 'drop_reason'] = "moneyness_out_of_range"
    total_dropped = (~manifest['keep']).sum()
    drop_reasons_count = manifest.loc[~manifest['keep'], 'drop_reason'].value_counts().to_dict()
    df_clean = df[manifest['keep']].copy().reset_index(drop=True)
    # Save manifest of kept/dropped rows
    os.makedirs(output_dir, exist_ok=True)
    manifest.to_csv(os.path.join(output_dir, "clean_manifest.csv"), index=False)
    # Feature engineering: define bins for moneyness, vtexp, adjtheor
    mon_edges = [-5, -2, -1, -0.5, -0.25, -0.125, -0.0625, -0.015625, 0, 0.015625, 0.05, 0.125, float('inf')]
    mon_labels = ["(-5,-2]", "(-2,-1]", "(-1,-0.5]", "(-0.5,-0.25]", 
                  "(-0.25,-0.125]", "(-0.125,-0.0625]", "(-0.0625,-0.015625]", "( -0.015625,0]", 
                  "(0,0.015625]", "(0.015625,0.05]", "(0.05,0.125]", "(>0.125)"]
    df_clean['moneyness_bin'] = pd.cut(df_clean['moneyness'], bins=mon_edges, labels=mon_labels, include_lowest=True)
    vte_edges = [0, 0.002, 0.01, 0.05, 1.0]
    vte_labels = ["<0.002", "0.002-0.01", "0.01-0.05", ">=0.05"]
    df_clean['vtexp_bin'] = pd.cut(df_clean['vtexp'], bins=vte_edges, labels=vte_labels, right=False)
    adj_edges = [0, 0.015625, 0.05, 0.125, float('inf')]
    adj_labels = ["<=0.015625", "0.015625-0.05", "0.05-0.125", ">0.125"]
    df_clean['adj_bin'] = pd.cut(df_clean['adjtheor'], bins=adj_edges, labels=adj_labels, include_lowest=True)
    # Define success metrics
    epsilon_tick = 0.015625  # one tick
    df_clean['success_fallback'] = (df_clean['error_2nd_order'].abs() <= (df_clean['adjtheor'].abs() + epsilon_tick))
    df_clean['success_abs'] = (df_clean['error_2nd_order'].abs() <= 5)
    # Threshold sweep analysis
    sweep_records = []
    for tau in thresholds:
        hi_mask = df_clean['adjtheor'] > tau
        lo_mask = df_clean['adjtheor'] <= tau
        count_total = len(df_clean)
        count_hi = hi_mask.sum()
        count_lo = lo_mask.sum()
        success_hi_count = ((df_clean['success_abs']) & hi_mask).sum()
        success_lo_count = ((df_clean['success_fallback']) & lo_mask).sum()
        success_overall = (success_hi_count + success_lo_count) / count_total if count_total > 0 else 0.0
        success_hi_rate = success_hi_count / count_hi if count_hi > 0 else np.nan
        success_lo_rate = success_lo_count / count_lo if count_lo > 0 else np.nan
        mneg_mask = df_clean['moneyness'] < 0
        mpos_mask = df_clean['moneyness'] >= 0
        count_mneg = mneg_mask.sum(); count_mpos = mpos_mask.sum()
        success_mneg = (((df_clean['success_abs'] & hi_mask) | (df_clean['success_fallback'] & lo_mask)) & mneg_mask).sum()
        success_mpos = (((df_clean['success_abs'] & hi_mask) | (df_clean['success_fallback'] & lo_mask)) & mpos_mask).sum()
        success_mneg_rate = success_mneg / count_mneg if count_mneg > 0 else np.nan
        success_mpos_rate = success_mpos / count_mpos if count_mpos > 0 else np.nan
        # Success by vtexp categories
        vcat_rates = {}
        for label in vte_labels:
            vmask = (df_clean['vtexp_bin'] == label)
            count_v = vmask.sum()
            if count_v > 0:
                success_v = (((df_clean['success_abs'] & hi_mask) | (df_clean['success_fallback'] & lo_mask)) & vmask).sum()
                rate_v = success_v / count_v
            else:
                rate_v = np.nan
            vcat_rates[label] = rate_v
        success_macro = 0.5*(success_mneg_rate + success_mpos_rate) if (~np.isnan(success_mneg_rate) and ~np.isnan(success_mpos_rate)) else np.nan
        # 95% CI for high-region success
        if count_hi > 0 and not np.isnan(success_hi_rate):
            p = success_hi_rate; n = count_hi
            se = np.sqrt(p*(1-p)/n) if p*(1-p) > 0 else 0.0
            ci_lower = max(0.0, p - 1.96*se)
            ci_upper = min(1.0, p + 1.96*se)
        else:
            ci_lower = np.nan; ci_upper = np.nan
        rec = {
            "threshold": tau,
            "count_total": count_total,
            "count_hi": int(count_hi), "count_lo": int(count_lo),
            "success_overall": success_overall,
            "success_hi": success_hi_rate, "success_lo": success_lo_rate,
            "success_mneg": success_mneg_rate, "success_mpos": success_mpos_rate
        }
        for label in vte_labels:
            rec[f"success_{label}"] = vcat_rates[label]
        rec["success_macro"] = success_macro
        rec["success_hi_ci_lower"] = ci_lower; rec["success_hi_ci_upper"] = ci_upper
        sweep_records.append(rec)
    df_sweep = pd.DataFrame(sweep_records)
    df_sweep.to_csv(os.path.join(output_dir, "threshold_sweep.csv"), index=False)
    # Determine recommended threshold (smallest tau with ≥95% success_hi)
    recommended_tau = None
    for tau in thresholds:
        row = df_sweep[df_sweep['threshold'] == tau]
        if not row.empty:
            sr = float(row['success_hi'])
            if not np.isnan(sr) and sr >= 0.95:
                recommended_tau = tau
                break
    # Pivot success by bins
    df_clean['success_flag'] = (df_clean['error_2nd_order'].abs() <= 5)
    agg = df_clean.groupby(['moneyness_bin','vtexp_bin','adj_bin'])['success_flag'].agg(['sum','count']).reset_index()
    agg.rename(columns={'sum':'success_count','count':'total_count'}, inplace=True)
    agg['success_rate'] = agg['success_count'] / agg['total_count']
    agg.to_csv(os.path.join(output_dir, "summary_success_by_bins.csv"), index=False)
    # DOTM epsilon analysis
    dotm_mask_125 = (df_clean['moneyness'] <= -0.125)
    dotm_mask_0625 = (df_clean['moneyness'] <= -0.0625)
    dotm_records = []
    for eps in epsilons:
        succ_125 = ((df_clean['error_2nd_order'].abs() <= (df_clean['adjtheor'] + eps)) & dotm_mask_125).sum()
        succ_125 = succ_125 / dotm_mask_125.sum() if dotm_mask_125.sum()>0 else None
        succ_0625 = ((df_clean['error_2nd_order'].abs() <= (df_clean['adjtheor'] + eps)) & dotm_mask_0625).sum()
        succ_0625 = succ_0625 / dotm_mask_0625.sum() if dotm_mask_0625.sum()>0 else None
        dotm_records.append({
            "epsilon": eps,
            "success_moneyness_le_-0.0625": succ_0625,
            "success_moneyness_le_-0.125": succ_125
        })
    df_dotm = pd.DataFrame(dotm_records)
    df_dotm.to_csv(os.path.join(output_dir, "dotm_epsilon.csv"), index=False)
    # Placeholder external vol diff file
    pd.DataFrame(columns=["moneyness","vtexp","our_vol","pm_vol","vol_diff"])\
      .to_csv(os.path.join(output_dir, "vol_diff_vs_pm.csv"), index=False)
    # Inflection point candidates (95% success threshold per expiry category)
    inflection_list = [{"category": "All", "threshold_for_95pct": recommended_tau}]
    for label in vte_labels:
        col = f"success_{label}"
        valid_rows = df_sweep[(df_sweep[col] >= 0.95) & (~df_sweep[col].isna())]
        thr_val = float(valid_rows['threshold'].iloc[0]) if not valid_rows.empty else None
        inflection_list.append({"category": f"vtexp_{label}", "threshold_for_95pct": thr_val})
    pd.DataFrame(inflection_list).to_csv(os.path.join(output_dir, "inflection_candidates.csv"), index=False)
    return {
        "total_rows": total_rows,
        "dropped": int(total_dropped),
        "drop_reasons": drop_reasons_count,
        "recommended_threshold": recommended_tau
    }

def main():
    parser = argparse.ArgumentParser(description="Analyze accuracy frontier from Plex validation data")
    parser.add_argument("--root", type=str, required=True, help="Root directory containing *Plex.csv files")
    parser.add_argument("--outdir", type=str, required=True, help="Output directory for results CSVs")
    parser.add_argument("--min-adjtheor-grid", type=str, default="0.001,0.002,0.005,0.01,0.015625,0.02,0.03,0.05,0.07,0.1",
                        help="Comma-separated grid of minimum adjtheor thresholds to test")
    parser.add_argument("--epsilon-grid", type=str, default="0.0078125,0.015625,0.03125",
                        help="Comma-separated list of epsilon values for DOTM analysis")
    args = parser.parse_args()
    thresholds = [float(x) for x in args.min_adjtheor_grid.split(",")]
    epsilons = [float(x) for x in args.epsilon_grid.split(",")]
    os.makedirs(args.outdir, exist_ok=True)
    results = analyze_accuracy_data(args.root, args.outdir, thresholds, epsilons)
    print("Analysis complete.")
    print(f"Total rows processed: {results['total_rows']}")
    print(f"Rows dropped: {results['dropped']} (Reasons: {results['drop_reasons']})")
    if results['recommended_threshold'] is not None:
        print(f"Recommended adjtheor threshold: {results['recommended_threshold']:.6f}")
    else:
        print("No threshold in grid achieved ≥95% success in high-price region.")

if __name__ == "__main__":
    main()
