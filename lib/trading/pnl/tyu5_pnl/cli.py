import argparse
import sys
from tyu5_pnl.main import run_pnl_analysis
from tyu5_pnl.sample_generator import create_sample_input_data
import pandas as pd

def run_cli():
    parser = argparse.ArgumentParser(
        description="TYU5 PNL Excel Tracker - Process and analyze futures/options trades."
    )

    parser.add_argument(
        "--mode", choices=["actual", "simulated"], default="actual",
        help="Execution mode: 'actual' for real input file, 'simulated' for demo mode (default: actual)"
    )

    parser.add_argument(
        "input_file", nargs="?", help="Input Excel file (required for actual mode)"
    )
    parser.add_argument(
        "output_file", help="Output Excel file to save analysis"
    )

    parser.add_argument(
        "--risk-base", type=float, default=120.0, help="Base price for risk matrix (default: 120.0)"
    )
    parser.add_argument(
        "--risk-range", type=float, nargs=2, default=[-3, 3], help="Price range (min max) for risk matrix"
    )
    parser.add_argument(
        "--risk-steps", type=int, default=13, help="Steps in risk matrix price scenarios"
    )

    args = parser.parse_args()

    if args.mode == "actual" and not args.input_file:
        parser.error("In 'actual' mode, input_file is required.")

    if args.mode == "simulated":
        print("[✓] Running in simulated mode (no input required).")
        sample_data = create_sample_input_data()
        input_file = None
    else:
        sample_data = None
        input_file = args.input_file

    run_pnl_analysis(
        input_file=input_file,
        output_file=args.output_file,
        base_price=args.risk_base,
        price_range=tuple(args.risk_range),
        steps=args.risk_steps,
        sample_data=sample_data
    )
