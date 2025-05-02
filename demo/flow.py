# demo/flow.py (Added Actant Analytics Step)

import logging
import os
import sys
import atexit
import time # Keep time for potential future use if needed
import random # Needed for state generation
import math # For ceiling calculation

# --- Adjust Python path to find 'src' ---
# Get the directory containing the current script (demo/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (uikitxv2/)
project_root = os.path.dirname(current_dir)
# Construct the path to the src directory
src_path = os.path.join(project_root, 'src')
# Add src path to the beginning of sys.path if it's not already there
if src_path not in sys.path:
    sys.path.insert(0, src_path)
# --- End Path Adjustment ---

# --- Import lumberjack and decorators ---
try:
    # Import logging setup and shutdown functions
    from lumberjack.logging_config import setup_logging, shutdown_logging
    # Import the decorators in the standard order
    from decorators.trace_closer import TraceCloser
    from decorators.logger_decorator import FunctionLogger
    from decorators.trace_cpu import TraceCpu
    from decorators.trace_memory import TraceMemory
    # Import context vars if needed (not directly used in this version but good practice)
    from decorators.context_vars import log_uuid_var, current_log_data
except ImportError as e:
    # Use print here as logging might not be set up yet
    print(f"[Import Error] Failed to import necessary components: {e}", file=sys.stderr)
    print(f"[Import Error] Current sys.path: {sys.path}", file=sys.stderr)
    sys.exit(1) # Exit if essential imports fail
# --- End Imports ---

# --- Logging Configuration ---
# Define the directory for log files relative to the project root
LOG_DB_DIR = os.path.join(project_root, 'logs')
# Define the specific database file path for this flow
LOG_DB_PATH = os.path.join(LOG_DB_DIR, 'trading_flow_logs.db')
# Ensure the log directory exists
os.makedirs(LOG_DB_DIR, exist_ok=True)

# Setup logging: Console output at DEBUG level, Database logging at INFO level
# The root logger level is set to DEBUG to allow all messages through initially
console_handler, db_handler = setup_logging(
    db_path=LOG_DB_PATH,
    log_level_console=logging.DEBUG, # Show detailed logs in console
    log_level_db=logging.INFO,       # Only store INFO level (decorator summaries) in DB
    log_level_main=logging.DEBUG     # Root logger allows DEBUG and above
)

# Register the shutdown_logging function to be called automatically on script exit
# This ensures database connections are closed properly.
atexit.register(shutdown_logging)
# --- End Logging Configuration ---

# --- Decorated Business Logic Functions ---

@TraceCloser()
@TraceMemory()
@TraceCpu()
@FunctionLogger(log_args=True, log_return=True)
def StartOfDay(trading_instrument: str):
    """
    Determines the initial state for the trading day for a given instrument.
    Randomly sets Position, Risk, Market state, and initial Market Price.
    """
    possible_positions = ['Long', 'Short', 'Flat']
    possible_risks = ['Low', 'Medium', 'High']
    possible_market_states = ['Trending Up', 'Trending Down', 'Sideways', 'Volatile']

    initial_position_type = random.choice(possible_positions)
    initial_risk = random.choice(possible_risks)
    initial_market_state = random.choice(possible_market_states)
    initial_market_price = round(random.uniform(95.0, 105.0), 2) # Simulate starting price

    if initial_position_type == 'Flat':
        initial_quantity = 0
    else:
        initial_quantity = random.randint(1, 100) * 10

    formatted_position = f"{initial_quantity} {initial_position_type}"
    time.sleep(random.uniform(0.05, 0.1))

    if random.random() < 0.05:
        raise ValueError(f"Failed to retrieve initial market data for {trading_instrument}.")

    return {
        "status": "success",
        "instrument": trading_instrument,
        "initial_position_type": initial_position_type,
        "initial_quantity": initial_quantity,
        "initial_position_formatted": formatted_position,
        "initial_risk_level": initial_risk,
        "initial_market_state": initial_market_state,
        "initial_market_price": initial_market_price, # Added initial price
        "message": f"Initial state determined for {trading_instrument}."
    }

@TraceCloser()
@TraceMemory()
@TraceCpu()
@FunctionLogger(log_args=True, log_return=True)
def HandoffToTradingTech(instrument: str, position_type: str, quantity: int):
    """
    Simulates sending a portion of the position to Trading Technologies (TT).
    """
    if position_type == 'Flat' or quantity <= 0:
        return {"status": "skipped", "instrument": instrument, "quantity_handed_off": 0, "message": "TT Handoff skipped, position is Flat or zero."}

    min_portion, max_portion = 0.10, 0.80
    portion = random.uniform(min_portion, max_portion)
    qty_handoff = min(quantity, math.ceil(quantity * portion))
    if quantity > 0 and qty_handoff == 0: qty_handoff = 1

    time.sleep(random.uniform(0.15, 0.4))
    if random.random() < 0.1: raise ConnectionError(f"Failed to connect to TT API for {instrument} handoff.")

    return {"status": "success", "instrument": instrument, "total_quantity": quantity, "quantity_handed_off": qty_handoff, "message": f"Successfully handed off {qty_handoff} units of {instrument} ({position_type}) to TT."}

@TraceCloser()
@TraceMemory()
@TraceCpu()
@FunctionLogger(log_args=True, log_return=True)
def ExecuteCMEDirectInternal(instrument: str, position_type: str, initial_quantity: int, tt_handed_off: int, initial_market_price: float):
    """
    Simulates internal execution within CME Direct for its portion of the position.
    Calculates final position and realized PnL.
    """
    if position_type == 'Flat' or initial_quantity <= 0:
        return {"status": "skipped", "instrument": instrument, "final_quantity": 0, "realized_pnl": 0.0, "message": "CMEDirect execution skipped, initial position Flat."}

    max_cme_quantity = initial_quantity - tt_handed_off - 1
    if max_cme_quantity <= 0:
        return {"status": "skipped", "instrument": instrument, "final_quantity": 0, "realized_pnl": 0.0, "message": "CMEDirect execution skipped, no quantity available."}

    min_portion, max_portion = 0.10, 0.80
    portion = random.uniform(min_portion, max_portion)
    cme_direct_initial_qty = min(max_cme_quantity, max(1, math.ceil(max_cme_quantity * portion)))

    action = random.choice(['increase', 'decrease', 'keep'])
    change_amount = 0
    final_quantity = cme_direct_initial_qty

    if action == 'increase':
        change_percent = random.uniform(0.05, 0.30)
        change_amount = math.ceil(cme_direct_initial_qty * change_percent)
        final_quantity += change_amount
    elif action == 'decrease':
        change_percent = random.uniform(0.05, 0.30)
        change_amount = -math.ceil(cme_direct_initial_qty * change_percent)
        final_quantity = max(0, cme_direct_initial_qty + change_amount)

    price_change = random.uniform(-0.5, 0.5)
    final_price = round(initial_market_price + price_change, 2)
    realized_pnl = 0.0
    if change_amount != 0:
        pnl_per_unit = final_price - initial_market_price
        if position_type == 'Short': pnl_per_unit *= -1
        realized_pnl = round(change_amount * pnl_per_unit, 2)

    time.sleep(random.uniform(0.2, 0.5))
    if random.random() < 0.15: raise TimeoutError(f"CMEDirect internal execution failed for {instrument}.")

    return {
        "status": "success",
        "instrument": instrument,
        "initial_cme_direct_quantity": cme_direct_initial_qty,
        "action": action,
        "change_amount": change_amount,
        "final_quantity": final_quantity,
        "realized_pnl": realized_pnl,
        "message": f"CMEDirect internally executed: {action} by {abs(change_amount)}, final quantity {final_quantity}, PnL {realized_pnl}."
    }

@TraceCloser()
@TraceMemory()
@TraceCpu()
@FunctionLogger(log_args=True, log_return=True)
def ExecuteTTAlgoOnCME(instrument: str, tt_quantity: int, initial_market_price: float, position_type: str):
    """
    Simulates TT algo adjusting its quantity, executing on CME, calculating PnL,
    and getting the final CME market price.
    """
    if tt_quantity <= 0:
        return {"status": "skipped", "instrument": instrument, "final_quantity": 0, "realized_pnl": 0.0, "final_market_price": initial_market_price, "message": "TT execution on CME skipped, no quantity."}

    action = random.choice(['increase', 'decrease', 'keep'])
    change_amount = 0
    final_quantity = tt_quantity

    if action == 'increase':
        change_percent = random.uniform(0.10, 0.50)
        change_amount = math.ceil(tt_quantity * change_percent)
        final_quantity += change_amount
    elif action == 'decrease':
        change_percent = random.uniform(0.10, 0.50)
        change_amount = -math.ceil(tt_quantity * change_percent)
        final_quantity = max(0, tt_quantity + change_amount)

    price_change = random.uniform(-0.6, 0.6)
    final_market_price = round(initial_market_price + price_change, 2)
    realized_pnl = 0.0
    if change_amount != 0:
        pnl_per_unit = final_market_price - initial_market_price
        if position_type == 'Short': pnl_per_unit *= -1
        realized_pnl = round(change_amount * pnl_per_unit, 2)

    time.sleep(random.uniform(0.1, 0.3))
    if random.random() < 0.08: raise ConnectionRefusedError(f"CME rejected TT execution for {instrument}.")

    return {
        "status": "success",
        "instrument": instrument,
        "original_tt_quantity": tt_quantity,
        "action": action,
        "change_amount": change_amount,
        "final_quantity": final_quantity,
        "realized_pnl": realized_pnl,
        "final_market_price": final_market_price,
        "message": f"TT algo executed on CME: {action} by {abs(change_amount)}, final quantity {final_quantity}, PnL {realized_pnl}."
    }

@TraceCloser()
@TraceMemory()
@TraceCpu()
@FunctionLogger(log_args=True, log_return=True)
def SendDataToActant(instrument: str, cme_exec_result: dict, cme_direct_exec_result: dict):
    """
    Aggregates results from CME (via TT) and CMEDirect internal execution
    and simulates sending the data to Actant.
    """
    cme_final_qty = cme_exec_result.get("final_quantity", 0)
    cme_pnl = cme_exec_result.get("realized_pnl", 0.0)
    final_market_price = cme_exec_result.get("final_market_price", None)

    cme_direct_final_qty = cme_direct_exec_result.get("final_quantity", 0)
    cme_direct_pnl = cme_direct_exec_result.get("realized_pnl", 0.0)

    total_final_quantity = cme_final_qty + cme_direct_final_qty
    total_realized_pnl = round(cme_pnl + cme_direct_pnl, 2)

    if final_market_price is None:
        final_market_price = cme_exec_result.get("initial_market_price", 0.0)
        status_message = "Aggregated data, but final market price from CME was missing."
        status = "warning"
    else:
        status_message = f"Aggregated data for Actant: Total Qty={total_final_quantity}, Total PnL={total_realized_pnl}, Market Price={final_market_price}."
        status = "success"

    time.sleep(random.uniform(0.05, 0.15))
    if random.random() < 0.03:
        raise ConnectionAbortedError(f"Failed to send aggregated data to Actant for {instrument}.")

    # Return the aggregated data needed for the next step (analytics)
    return {
        "status": status,
        "instrument": instrument,
        "total_final_quantity": total_final_quantity,
        "total_realized_pnl": total_realized_pnl,
        "final_market_price": final_market_price,
        "message": status_message
    }

@TraceCloser()
@TraceMemory()
@TraceCpu()
@FunctionLogger(log_args=True, log_return=True)
def RunActantAnalytics(instrument: str, aggregated_data: dict):
    """
    Simulates Actant running analytics on the aggregated end-of-day data.
    Generates mock metrics like final risk, model signal, VaR.
    """
    # Extract data safely
    final_qty = aggregated_data.get("total_final_quantity", 0)
    final_pnl = aggregated_data.get("total_realized_pnl", 0.0)
    final_price = aggregated_data.get("final_market_price", 0.0)

    # Simulate Analytics Calculation
    # 1. Final Position Value
    final_position_value = round(final_qty * final_price, 2)

    # 2. Final Risk Level (Mock logic)
    possible_risks = ['Low', 'Medium', 'High', 'Very High']
    risk_level = 'Low'
    if abs(final_position_value) > 50000: risk_level = 'Very High'
    elif abs(final_position_value) > 20000: risk_level = 'High'
    elif abs(final_position_value) > 5000: risk_level = 'Medium'
    # Add PnL volatility factor (mock)
    if abs(final_pnl) > 1000 and risk_level == 'Medium': risk_level = 'High'
    if abs(final_pnl) > 2000 and risk_level == 'High': risk_level = 'Very High'

    # 3. Mock Model Signal
    model_signals = ['Hold Position', 'Reduce Exposure', 'Increase Exposure', 'Liquidate Immediately']
    model_signal = random.choice(model_signals)
    # Simple logic: if risk is high/very high, more likely to liquidate/reduce
    if risk_level in ['High', 'Very High'] and random.random() < 0.6:
        model_signal = random.choice(['Reduce Exposure', 'Liquidate Immediately'])
    elif risk_level == 'Low' and random.random() < 0.4:
        model_signal = 'Increase Exposure'

    # 4. Mock VaR (Value at Risk) - simplified
    # VaR could be a percentage of position value, influenced by risk level
    var_percentage = 0.01 # Default 1%
    if risk_level == 'Medium': var_percentage = 0.02
    elif risk_level == 'High': var_percentage = 0.05
    elif risk_level == 'Very High': var_percentage = 0.10
    value_at_risk = round(abs(final_position_value * var_percentage), 2)

    # Simulate processing time for analytics
    time.sleep(random.uniform(0.2, 0.6))

    # Simulate potential analytics failure
    if random.random() < 0.05: # 5% chance
        raise RuntimeError(f"Actant analytics engine failed for {instrument}.")

    # Return the End Of Day summary including analytics
    return {
        "status": "success",
        "instrument": instrument,
        "eod_quantity": final_qty,
        "eod_market_price": final_price,
        "eod_position_value": final_position_value,
        "eod_realized_pnl": final_pnl,
        "eod_risk_level": risk_level,
        "eod_model_signal": model_signal,
        "eod_value_at_risk": value_at_risk,
        "message": f"End of Day analytics completed for {instrument}."
    }


# --- Main Execution Logic ---
def run_trading_day_flow():
    """
    Orchestrates the sequence of operations for the trading day.
    Relies purely on decorators for function success/failure logging
    and exception handling within decorated functions.
    """
    main_logger = logging.getLogger(__name__) # For critical orchestration errors
    # Initialize variables
    start_result, handoff_tt_result, exec_cme_direct_result, exec_tt_cme_result, actant_send_result, analytics_result = (None,) * 6
    position_type, instrument = None, "Gold Bond Futures"
    initial_quantity, tt_quantity_handed_off = 0, 0
    initial_market_price = 0.0

    try:
        # --- Step 1: Start of Day ---
        start_result = StartOfDay(trading_instrument=instrument)
        position_type = start_result["initial_position_type"]
        initial_quantity = start_result["initial_quantity"]
        initial_market_price = start_result["initial_market_price"]

        # --- Step 2: Handoff to TT ---
        handoff_tt_result = HandoffToTradingTech(
            instrument=instrument,
            position_type=position_type,
            quantity=initial_quantity
        )
        tt_quantity_handed_off = handoff_tt_result.get("quantity_handed_off", 0)

        # --- Step 3: Execute CMEDirect Internally ---
        exec_cme_direct_result = ExecuteCMEDirectInternal(
            instrument=instrument,
            position_type=position_type,
            initial_quantity=initial_quantity,
            tt_handed_off=tt_quantity_handed_off,
            initial_market_price=initial_market_price
        )

        # --- Step 4: Execute TT Algo on CME ---
        exec_tt_cme_result = ExecuteTTAlgoOnCME(
            instrument=instrument,
            tt_quantity=tt_quantity_handed_off,
            initial_market_price=initial_market_price,
            position_type=position_type
        )

        # --- Step 5: Send Data to Actant ---
        if exec_tt_cme_result and exec_cme_direct_result:
            actant_send_result = SendDataToActant(
                instrument=instrument,
                cme_exec_result=exec_tt_cme_result,
                cme_direct_exec_result=exec_cme_direct_result
            )
        else:
             main_logger.warning("Skipping Actant update due to missing execution results.")
             # Decide if flow should stop if Actant update is critical
             return

        # --- Step 6: Run Actant Analytics ---
        if actant_send_result and actant_send_result.get("status") in ["success", "warning"]: # Proceed even if price was missing
             analytics_result = RunActantAnalytics(
                 instrument=instrument,
                 aggregated_data=actant_send_result # Pass the result containing aggregated data
             )
        else:
             main_logger.warning("Skipping Actant Analytics due to SendDataToActant failure or skip.")
             return # Stop if analytics requires successful Actant send

        # --- End of Flow ---
        # analytics_result contains the final EOD summary
        # In a real app, this might be saved or passed to another process.
        # For the demo, the decorators have logged its execution.


    except Exception as e:
        # Catch errors from decorated functions OR orchestration logic.
        main_logger.critical(f"Trading day flow failed: {e}", exc_info=True)
        # Decorators log the specific function failure to flowTrace.


# --- Script Entry Point ---
if __name__ == "__main__":
    main_logger = logging.getLogger(__name__)
    main_logger.info("Initializing trading day flow simulation...")
    run_trading_day_flow()
    main_logger.info("Trading day flow simulation finished.")
    logging.shutdown()
    if shutdown_logging in getattr(atexit, '_exithandlers', []):
         try: atexit.unregister(shutdown_logging)
         except Exception as e: main_logger.warning(f"Could not unregister atexit handler: {e}")

