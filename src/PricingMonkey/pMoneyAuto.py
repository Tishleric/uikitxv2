"""
pMoneyAuto - Multi-Option Workflow using openpyxl for Excel

This version is adapted for integration with a dashboard.
It accepts option data as an argument and returns a joined DataFrame.
"""

import time
import os
import io
import pandas as pd
import pyperclip
import webbrowser
import traceback
import openpyxl
from openpyxl.utils import get_column_letter, column_index_from_string
from pywinauto.keyboard import send_keys

# --- Configuration Constants ---
# Ensure this path is accessible from where the dashboard server runs,
# or consider making it configurable.
FILE_PATH = r"\\ERIC-HOST-PC\FRGMSharedSpace\PnL Scanrios - US Rates.4.30.25.xlsx"
SHEET_NAME = "Sheet2"
PNL_SCENARIO_BUY_SHEET_NAME = "PnL Scenario - Buy"
PRICING_MONKEY_URL_FOR_PASTE = "https://pricingmonkey.com/b/3580a62f-daf9-49bd-bf2e-01120ff59371"

PHASE_CONFIGS = {
    1: {"excel_start_row": 3,  "excel_results_data_start_row": 3},
    2: {"excel_start_row": 6,  "excel_results_data_start_row": 6},
    3: {"excel_start_row": 8,  "excel_results_data_start_row": 8},
    4: {"excel_start_row": 10, "excel_results_data_start_row": 10},
    5: {"excel_start_row": 12, "excel_results_data_start_row": 12},
}
EXCEL_PM_DATA_END_ROW = 14
EXCEL_PM_RESULTS_MAX_ROW_FOR_CLEARING_UNUSED = 14
PNL_VALUE_TARGET_START_ROW_SHEET2 = 3
PNL_VALUE_TARGET_END_ROW_SHEET2 = 14

OPT1_USER_QTY_COL = "F"
OPT1_PM_QTY_COL = "G"
OPT1_PM_DESC_COL = "H"
OPT1_PM_COPY_END_COL = "I"
COL_OFFSET_FOR_SETUP_BLOCKS = 9

OPT2_USER_QTY_COL = get_column_letter(column_index_from_string(OPT1_USER_QTY_COL) + COL_OFFSET_FOR_SETUP_BLOCKS)
OPT2_PM_QTY_COL = get_column_letter(column_index_from_string(OPT1_PM_QTY_COL) + COL_OFFSET_FOR_SETUP_BLOCKS)
OPT2_PM_DESC_COL = get_column_letter(column_index_from_string(OPT1_PM_DESC_COL) + COL_OFFSET_FOR_SETUP_BLOCKS)
OPT2_PM_COPY_END_COL = get_column_letter(column_index_from_string(OPT1_PM_COPY_END_COL) + COL_OFFSET_FOR_SETUP_BLOCKS)

OPT3_USER_QTY_COL = get_column_letter(column_index_from_string(OPT2_USER_QTY_COL) + COL_OFFSET_FOR_SETUP_BLOCKS)
OPT3_PM_QTY_COL = get_column_letter(column_index_from_string(OPT2_PM_QTY_COL) + COL_OFFSET_FOR_SETUP_BLOCKS)
OPT3_PM_DESC_COL = get_column_letter(column_index_from_string(OPT2_PM_DESC_COL) + COL_OFFSET_FOR_SETUP_BLOCKS)
OPT3_PM_COPY_END_COL = get_column_letter(column_index_from_string(OPT2_PM_COPY_END_COL) + COL_OFFSET_FOR_SETUP_BLOCKS)

OPT1_PM_RESULT_START_COL = "J"
OPT1_PM_RESULT_END_COL = "L"
OPT2_PM_RESULT_START_COL = "S"
OPT2_PM_RESULT_END_COL = "U"
OPT3_PM_RESULT_START_COL = "AB"
OPT3_PM_RESULT_END_COL = "AD"

OPTION_COLUMN_MAP = [
    {"user_qty_col": OPT1_USER_QTY_COL, "pm_qty_col": OPT1_PM_QTY_COL, "pm_desc_col": OPT1_PM_DESC_COL, "pm_copy_end_col": OPT1_PM_COPY_END_COL,
     "pm_result_start_col": OPT1_PM_RESULT_START_COL, "pm_result_end_col": OPT1_PM_RESULT_END_COL},
    {"user_qty_col": OPT2_USER_QTY_COL, "pm_qty_col": OPT2_PM_QTY_COL, "pm_desc_col": OPT2_PM_DESC_COL, "pm_copy_end_col": OPT2_PM_COPY_END_COL,
     "pm_result_start_col": OPT2_PM_RESULT_START_COL, "pm_result_end_col": OPT2_PM_RESULT_END_COL},
    {"user_qty_col": OPT3_USER_QTY_COL, "pm_qty_col": OPT3_PM_QTY_COL, "pm_desc_col": OPT3_PM_DESC_COL, "pm_copy_end_col": OPT3_PM_COPY_END_COL,
     "pm_result_start_col": OPT3_PM_RESULT_START_COL, "pm_result_end_col": OPT3_PM_RESULT_END_COL},
]

PNL_BUY_SOURCE_COL = 'U'
PNL_BUY_SOURCE_ROWS = [4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26]

KEY_PRESS_PAUSE = 0.01
WAIT_FOR_BROWSER_TO_OPEN = 2.5
WAIT_AFTER_BROWSER_NAVIGATION = 0.1
WAIT_AFTER_BROWSER_PASTE = 5.0
WAIT_FOR_COPY_OPERATION = 0.2
WAIT_FOR_BROWSER_CLOSE = 0.5

# --- Helper Functions (largely unchanged, but no longer ask for input) ---

def check_file_exists(file_path):
    """Checks if the Excel file exists."""
    if os.path.exists(file_path):
        print(f"Excel file verified at: {file_path}")
        return True
    else:
        print(f"Error: Excel file not found at {file_path}.")
        return False

def excel_setup_options_and_consolidate_for_pm_openpyxl(file_path, sheet_name_target, pnl_sheet_name_source, options_data_list):
    """
    Prepares Excel data for PM, consolidates it, and returns a DataFrame.
    Args:
        options_data_list (list): List of dicts, each with 'desc', 'qty', 'phase', 'id'.
    """
    print(f"\n--- Preparing Excel Data for {len(options_data_list)} Option(s) using openpyxl ---")
    fixed_pm_quantity = 1000
    workbook = None
    all_data_for_pm_list_of_lists = []

    try:
        print("Loading workbook...")
        workbook = openpyxl.load_workbook(file_path)
        sheet_target = workbook[sheet_name_target]
        sheet_source_pnl = workbook[pnl_sheet_name_source]

        print(f"Reading 12 source values from '{pnl_sheet_name_source}' column '{PNL_BUY_SOURCE_COL}'...")
        pnl_buy_values = []
        if len(PNL_BUY_SOURCE_ROWS) != 12:
            print(f"Error: PNL_BUY_SOURCE_ROWS should have 12 rows, has {len(PNL_BUY_SOURCE_ROWS)}.")
            workbook.close()
            return None
            
        for row_num_pnl in PNL_BUY_SOURCE_ROWS:
            cell_addr_pnl = f"{PNL_BUY_SOURCE_COL}{row_num_pnl}"
            value = sheet_source_pnl[cell_addr_pnl].value
            if isinstance(value, str):
                try: num_val = float(value); pnl_buy_values.append(num_val)
                except ValueError: pnl_buy_values.append(value) 
            elif value is not None: pnl_buy_values.append(value)
            else: pnl_buy_values.append('')
        print(f"  Source values: {pnl_buy_values}")

        for opt_data in options_data_list: # opt_data comes from dashboard
            option_idx = opt_data['id']
            cols = OPTION_COLUMN_MAP[option_idx]
            phase_config = PHASE_CONFIGS[opt_data['phase']]
            phase_dependent_block_start_row = phase_config['excel_start_row'] 
            
            print(f"\nProcessing Option {option_idx + 1} (Description: '{opt_data['desc']}', Qty: {opt_data['qty']}, Phase: {opt_data['phase']}) on '{sheet_name_target}':")

            user_qty_cell = f"{cols['user_qty_col']}2"
            sheet_target[user_qty_cell] = opt_data['qty']
            print(f"  Stored user qty {opt_data['qty']} in {user_qty_cell}")

            pm_qty_col_letter = cols['pm_qty_col']
            pm_desc_col_letter = cols['pm_desc_col']
            pm_third_col_letter = cols['pm_copy_end_col']

            print(f"  Writing Qty/Desc to {pm_qty_col_letter}:{pm_desc_col_letter} (rows {phase_dependent_block_start_row}-{EXCEL_PM_DATA_END_ROW}).")
            print(f"  Writing PnL values to {pm_third_col_letter} (rows {PNL_VALUE_TARGET_START_ROW_SHEET2}-{PNL_VALUE_TARGET_END_ROW_SHEET2}).")

            for i in range(12): 
                current_row_for_qty_desc = phase_dependent_block_start_row + i
                if current_row_for_qty_desc <= EXCEL_PM_DATA_END_ROW:
                    sheet_target[f"{pm_qty_col_letter}{current_row_for_qty_desc}"] = fixed_pm_quantity
                    sheet_target[f"{pm_desc_col_letter}{current_row_for_qty_desc}"] = opt_data['desc']
                
                fixed_row_for_pnl_value = PNL_VALUE_TARGET_START_ROW_SHEET2 + i 
                sheet_target[f"{pm_third_col_letter}{fixed_row_for_pnl_value}"] = pnl_buy_values[i]
            print(f"  Data written for Option {option_idx + 1} block.")

        print("\nReading data from 'Sheet2' for PM consolidation...")
        for opt_data in options_data_list:
            option_idx = opt_data['id']
            cols = OPTION_COLUMN_MAP[option_idx]
            phase_config = PHASE_CONFIGS[opt_data['phase']]
            block_start_row_for_read = phase_config['excel_start_row'] 
            
            print(f"  Reading data for Option {option_idx + 1} from block starting at row {block_start_row_for_read}")
            
            read_qty_col = cols['pm_qty_col']
            read_desc_col = cols['pm_desc_col']
            read_val_col = cols['pm_copy_end_col']

            option_rows_data = []
            num_rows_to_read = EXCEL_PM_DATA_END_ROW - block_start_row_for_read + 1
            if num_rows_to_read < 0: num_rows_to_read = 0 

            for i in range(num_rows_to_read):
                current_row_to_read = block_start_row_for_read + i
                qty_val = sheet_target[f"{read_qty_col}{current_row_to_read}"].value
                desc_val = sheet_target[f"{read_desc_col}{current_row_to_read}"].value
                underlying_val = sheet_target[f"{read_val_col}{current_row_to_read}"].value 
                
                option_rows_data.append([
                    qty_val if qty_val is not None else '',
                    desc_val if desc_val is not None else '',
                    underlying_val 
                ])
            all_data_for_pm_list_of_lists.extend(option_rows_data)
            print(f"  Option {option_idx+1} data (shape {len(option_rows_data)}x3) collected.")

        if not all_data_for_pm_list_of_lists:
            print("Error: No data collected from Excel for PM DataFrame."); workbook.close(); return None
        
        consolidated_df = pd.DataFrame(all_data_for_pm_list_of_lists)
        
        if not consolidated_df.empty:
            consolidated_df.columns = ["Trade Amount", "Trade Description", "Underlying_Raw"]
            print("DataFrame columns renamed to ['Trade Amount', 'Trade Description', 'Underlying_Raw']")
        
        print("DataFrame BEFORE 'Underlying_Raw' modification:\n", consolidated_df.head().to_string())

        if not consolidated_df.empty and "Underlying_Raw" in consolidated_df.columns:
            def format_for_pm(x):
                if pd.isnull(x) or x == '': return '' 
                try: return f"{float(x):.3f}".replace('.', '-')
                except ValueError: return str(x).replace('.', '-')
            consolidated_df["Underlying"] = consolidated_df["Underlying_Raw"].apply(format_for_pm)
            consolidated_df.drop(columns=["Underlying_Raw"], inplace=True)
            print(f"  Formatted 'Underlying_Raw' into 'Underlying' column for PM.")
        
        print("DataFrame AFTER 'Underlying' modification:\n", consolidated_df.head().to_string())

        pyperclip.copy(consolidated_df.to_csv(sep='\t', index=False, header=False))
        print("Consolidated data copied to clipboard.")

        print("\nSaving Excel workbook...")
        workbook.save(file_path)
        print("Excel workbook saved.")
        return consolidated_df

    except Exception as e:
        print(f"Error during Excel setup/consolidation: {e}"); traceback.print_exc(); return None
    finally:
        if workbook: workbook.close()

def browser_operations_and_copy(url_to_open, total_rows_pasted_to_pm):
    """Performs browser automation to paste data and copy results."""
    try:
        print(f"\nOpening URL: {url_to_open} ..."); webbrowser.open(url_to_open, new=2); time.sleep(WAIT_FOR_BROWSER_TO_OPEN)
        print("Navigating for paste: 8 TABs, 1 DOWN");
        for _ in range(8): send_keys('{TAB}', pause=KEY_PRESS_PAUSE); time.sleep(WAIT_AFTER_BROWSER_NAVIGATION)
        send_keys('{DOWN}', pause=KEY_PRESS_PAUSE); time.sleep(WAIT_AFTER_BROWSER_NAVIGATION)
        print("Pasting data (Ctrl+V)..."); send_keys('^v', pause=KEY_PRESS_PAUSE); time.sleep(WAIT_AFTER_BROWSER_PASTE); print("Paste complete.")
        print("Navigating for copy: 8 RIGHT arrows");
        for _ in range(8): send_keys('{RIGHT}', pause=KEY_PRESS_PAUSE); time.sleep(WAIT_AFTER_BROWSER_NAVIGATION)
        
        pm_down_arrow_count = total_rows_pasted_to_pm - 1 if total_rows_pasted_to_pm > 0 else 0
        print(f"Selecting results: SHIFT + {pm_down_arrow_count} DOWN, then SHIFT + 2 RIGHT")
        if pm_down_arrow_count > 0 : send_keys(f'+({{DOWN {pm_down_arrow_count}}})', pause=KEY_PRESS_PAUSE); time.sleep(WAIT_AFTER_BROWSER_NAVIGATION)
        send_keys(f'+({{RIGHT 2}})', pause=KEY_PRESS_PAUSE); time.sleep(WAIT_AFTER_BROWSER_NAVIGATION) # Select 3 columns
        print("Copying results (Ctrl+C)..."); send_keys('^c', pause=KEY_PRESS_PAUSE); time.sleep(WAIT_FOR_COPY_OPERATION)

        pm_clipboard_content = pyperclip.paste()
        if pm_clipboard_content:
            pyperclip.copy(pm_clipboard_content); print("PM results copied to clipboard.")
        else:
            print("Warning: Clipboard from PM was empty."); pyperclip.copy("")
        
        print("Closing browser tab (Ctrl+W)..."); send_keys('^w', pause=KEY_PRESS_PAUSE); time.sleep(WAIT_FOR_BROWSER_CLOSE); print("Browser close command sent.")
        return True
    except Exception as e: print(f"Error during browser ops: {e}"); traceback.print_exc(); return False

def excel_distribute_pm_data_and_final_cleanup_openpyxl(file_path, sheet_name_target, all_options_inputs_list, pm_data_from_clipboard):
    """Distributes PM results to Excel, cleans up, and returns PM results DataFrame."""
    workbook = None
    df_pm_results = None
    try:
        print("\n--- Distributing PM Data to Excel & Final Cleanup ---")
        if not pm_data_from_clipboard:
            print("Error: Clipboard empty (no PM data)."); return None

        print("Loading workbook for PM data distribution...")
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook[sheet_name_target]

        cleaned_lines = [
            '\t'.join(field.replace(',', '') for field in line.split('\t'))
            for line in pm_data_from_clipboard.splitlines()
        ]
        cleaned_pm_data_for_df = "\n".join(cleaned_lines)
        
        df_pm_results = pd.read_csv(io.StringIO(cleaned_pm_data_for_df), sep='\t', header=None)
        print(f"Parsed PM results from clipboard (Shape: {df_pm_results.shape})")

        if not df_pm_results.empty:
            # IMPORTANT: Rename to match dashboard's expectation for DV01 Gamma
            df_pm_results.columns = ["DV01 Gamma", "Theta", "Vega"]
            print("PM results DataFrame columns renamed to ['DV01 Gamma', 'Theta', 'Vega']")
            print("PM Results DataFrame head:\n", df_pm_results.head().to_string())

        current_row_index_in_pm_df = 0
        for opt_data in all_options_inputs_list:
            option_idx = opt_data['id']
            phase_config = PHASE_CONFIGS[opt_data['phase']]
            excel_setup_start_row = phase_config['excel_start_row']
            num_rows_for_this_option = EXCEL_PM_DATA_END_ROW - excel_setup_start_row + 1

            cols_map = OPTION_COLUMN_MAP[option_idx]
            target_paste_start_col_letter = cols_map['pm_result_start_col']
            target_result_end_col_letter = cols_map['pm_result_end_col'] # For cleanup
            target_data_paste_start_row = phase_config['excel_results_data_start_row']
            
            print(f"\nProcessing PM results for Option {option_idx + 1}:")
            print(f"  Target Excel: Col {target_paste_start_col_letter}, Row {target_data_paste_start_row} ({num_rows_for_this_option} rows)")

            if current_row_index_in_pm_df + num_rows_for_this_option > len(df_pm_results):
                print(f"  Error: Not enough rows in PM results for Option {option_idx + 1}."); continue

            df_slice = df_pm_results.iloc[current_row_index_in_pm_df : current_row_index_in_pm_df + num_rows_for_this_option]
            if df_slice.empty: print(f"  Warning: Slice for Option {option_idx + 1} is empty."); current_row_index_in_pm_df += num_rows_for_this_option; continue
            
            start_col_idx_paste = column_index_from_string(target_paste_start_col_letter)
            for r_offset, pm_row_tuple in enumerate(df_slice.itertuples(index=False, name=None)):
                excel_row = target_data_paste_start_row + r_offset
                for c_offset, cell_val in enumerate(pm_row_tuple):
                    try: numeric_cell_val = float(cell_val); sheet.cell(row=excel_row, column=start_col_idx_paste + c_offset, value=numeric_cell_val)
                    except (ValueError, TypeError): sheet.cell(row=excel_row, column=start_col_idx_paste + c_offset, value=cell_val) 
            print(f"  Pasted data slice into Excel.")
            current_row_index_in_pm_df += num_rows_for_this_option

            if target_data_paste_start_row > 1: # Cleanup above pasted block
                cleanup_above_end_row = target_data_paste_start_row - 1
                print(f"  Cleaning above: {target_paste_start_col_letter}1:{target_result_end_col_letter}{cleanup_above_end_row}")
                clean_start_col_idx = column_index_from_string(target_paste_start_col_letter)
                clean_end_col_idx = column_index_from_string(target_result_end_col_letter)
                for r_val in range(1, cleanup_above_end_row + 1):
                    for c_idx in range(clean_start_col_idx, clean_end_col_idx + 1):
                        sheet.cell(row=r_val, column=c_idx).value = None
        
        num_options_processed = len(all_options_inputs_list) # Cleanup unused option blocks
        for i in range(num_options_processed, 3):
            cols_map_unused = OPTION_COLUMN_MAP[i]
            unused_start = cols_map_unused['pm_result_start_col']
            unused_end = cols_map_unused['pm_result_end_col']
            print(f"Clearing unused Option {i+1} results: {unused_start}1:{unused_end}{EXCEL_PM_RESULTS_MAX_ROW_FOR_CLEARING_UNUSED}")
            unused_start_idx = column_index_from_string(unused_start)
            unused_end_idx = column_index_from_string(unused_end)
            for r_val in range(1, EXCEL_PM_RESULTS_MAX_ROW_FOR_CLEARING_UNUSED + 1):
                for c_idx in range(unused_start_idx, unused_end_idx + 1):
                    sheet.cell(row=r_val, column=c_idx).value = None
        
        print("Saving Excel workbook after PM data distribution and cleanup...")
        workbook.save(file_path)
        print("Excel workbook saved.")
        return df_pm_results

    except Exception as e:
        print(f"Error during Excel PM data distribution/cleanup: {e}"); traceback.print_exc(); return None
    finally:
        if workbook: workbook.close()

def run_pm_automation(options_data_from_dashboard: list):
    """
    Main automation function to be called by the dashboard.
    Args:
        options_data_from_dashboard (list): List of option dicts from the dashboard.
                                            Each dict: {'desc': str, 'qty': int, 'phase': int, 'id': int}
    Returns:
        pd.DataFrame or None: The joined DataFrame of inputs and PM results, or None on failure.
    """
    print("--- Running Pricing Monkey Automation (Dashboard Integration) ---")
    if not options_data_from_dashboard:
        print("No option data received from dashboard. Exiting.")
        return None

    if not check_file_exists(FILE_PATH):
        return None

    consolidated_df_for_pm = None
    df_pm_results_from_function = None
    joined_df = None

    try:
        # Step 1: Setup Excel and consolidate data for PM
        consolidated_df_for_pm = excel_setup_options_and_consolidate_for_pm_openpyxl(
            FILE_PATH, 
            SHEET_NAME, 
            PNL_SCENARIO_BUY_SHEET_NAME, 
            options_data_from_dashboard # Use data from dashboard
        )
        if consolidated_df_for_pm is None or consolidated_df_for_pm.empty:
            print("Failed Excel data prep or no data for PM. Automation cannot continue.")
            return None
        
        total_rows_for_pm_selection = len(consolidated_df_for_pm)

        # Step 2: Browser operations
        print("\n--- Starting Browser Operations ---")
        browser_success = browser_operations_and_copy(PRICING_MONKEY_URL_FOR_PASTE, total_rows_for_pm_selection)
        if not browser_success:
            print("Browser operations failed. Automation cannot continue.")
            return None
        
        clipboard_content_from_pm = pyperclip.paste() 

        # Step 3: Distribute PM data back to Excel and get PM results DataFrame
        df_pm_results_from_function = excel_distribute_pm_data_and_final_cleanup_openpyxl(
            FILE_PATH, SHEET_NAME, options_data_from_dashboard, clipboard_content_from_pm
        )

        if df_pm_results_from_function is None:
            print("Failed to process PM data into Excel or get PM results DataFrame.")
            return None # Return None if this step fails
        else:
            print("Successfully processed PM data back into Excel.")
            
            # Step 4: Join DataFrames
            if consolidated_df_for_pm is not None and not consolidated_df_for_pm.empty and \
               df_pm_results_from_function is not None and not df_pm_results_from_function.empty:
                
                if len(consolidated_df_for_pm) == len(df_pm_results_from_function):
                    consolidated_df_for_pm.reset_index(drop=True, inplace=True)
                    df_pm_results_from_function.reset_index(drop=True, inplace=True)

                    # Ensure column names are as expected by dashboard before returning
                    # consolidated_df_for_pm should have: "Trade Amount", "Trade Description", "Underlying"
                    # df_pm_results_from_function should have: "DV01 Gamma", "Theta", "Vega"
                    
                    joined_df = pd.concat([consolidated_df_for_pm, df_pm_results_from_function], axis=1)
                    print("\n--- Joined DataFrame (Input vs. Output) ---")
                    print(joined_df.head().to_string())
                    print(f"Joined DataFrame shape: {joined_df.shape}")
                    return joined_df # Return the successfully joined DataFrame
                else:
                    print("\nError: DataFrames have different numbers of rows and cannot be joined.")
                    print(f"  Input DF rows: {len(consolidated_df_for_pm)}, PM Results DF rows: {len(df_pm_results_from_function)}")
                    return None # Return None on join failure
            else:
                print("\nError: One or both DataFrames are missing or empty for join.")
                return None # Return None if DFs are not suitable for join

    except Exception as e:
        print(f"\nCRITICAL ERROR in run_pm_automation: {e}")
        traceback.print_exc()
        return None # Return None on any critical error
    finally:
        print("--- Pricing Monkey Automation Run Finished ---")

# --- Standalone Execution (for testing pMoneyAuto.py directly) ---
def get_all_user_inputs_for_standalone():
    """Gets user inputs when script is run standalone."""
    num_options = 0
    while True:
        try:
            num_input = input("How many options for standalone test (1-3)? ").strip()
            num_options = int(num_input)
            if 1 <= num_options <= 3: break
            else: print("Error: Number of options must be between 1 and 3.")
        except ValueError: print("Error: Please enter a valid integer (1, 2, or 3).")

    collected_options_data = []
    # For standalone, generate VALID_OPTIONS if not already done (though it's global)
    # from pMoneyAuto import VALID_OPTIONS # Assuming VALID_OPTIONS is defined globally
    
    # Minimal VALID_OPTIONS for testing if the main one is complex to generate here
    test_valid_options = {"1st 10y note 0 out call", "2nd 10y note 50 out put"}


    min_allowable_phase_for_current_option = 1
    for i in range(num_options):
        print(f"\n--- Standalone Test Option {i+1} ---")
        while True:
            # In a real standalone, you might want to use the full VALID_OPTIONS set
            # For this example, using a simpler set or allowing any string.
            desc = input(f"Option {i+1} Description (e.g., '1st 10y note 0 out call'): ").strip()
            # if desc in VALID_OPTIONS: # Or use your main VALID_OPTIONS
            #     print(f"  Option {i+1} Description: '{desc}'"); break
            # else: print(f"  Error: '{desc}' is not a valid option for standalone test.")
            print(f"  Option {i+1} Description (standalone): '{desc}'"); break # Allow any for quick test
        while True:
            qty_str = input(f"Option {i+1} Trade Amount: ").strip()
            try: qty = int(qty_str); print(f"  Option {i+1} Trade Amount: {qty}"); break
            except ValueError: print("  Error: Trade Amount must be an integer.")
        while True:
            phase_str = input(f"Option {i+1} Phase ({', '.join(map(str, PHASE_CONFIGS.keys()))}): ").strip()
            try:
                phase = int(phase_str)
                if phase not in PHASE_CONFIGS: print(f"  Error: Phase must be one of {list(PHASE_CONFIGS.keys())}.")
                elif phase < min_allowable_phase_for_current_option: print(f"  Error: Phase for Option {i+1} ({phase}) must be >= Phase for Option {i} ({min_allowable_phase_for_current_option}).")
                else: print(f"  Option {i+1} Phase: {phase}"); min_allowable_phase_for_current_option = phase; collected_options_data.append({'desc': desc, 'qty': qty, 'phase': phase, 'id': i}); break
            except ValueError: print(f"  Error: Phase must be an integer.")
    return collected_options_data


if __name__ == "__main__":
    print("--- Running pMoneyAuto.py in STANDALONE mode for testing ---")
    # This part now calls the new run_pm_automation function
    # after getting inputs via the console for testing purposes.
    
    # 1. Get inputs for standalone run
    standalone_options_input = get_all_user_inputs_for_standalone()
    
    if standalone_options_input:
        # 2. Call the main automation logic
        final_dataframe = run_pm_automation(standalone_options_input)

        if final_dataframe is not None:
            print("\n\n=== FINAL JOINED DATAFRAME (from standalone run) ===")
            print(final_dataframe.to_string())
            print("=====================================================")
        else:
            print("\nStandalone run completed, but no final DataFrame was produced (check logs for errors).")
    else:
        print("No inputs provided for standalone run. Exiting.")
    
    print("--- Standalone pMoneyAuto.py test finished ---")
    time.sleep(1)
