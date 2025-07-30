"""Run the spot risk pipeline with profiling enabled."""
import os
import subprocess
import time

# Set profiling environment variable
os.environ["MONITOR_PROFILING"] = "1"

print("Starting Spot Risk Pipeline with Profiling Enabled")
print(f"MONITOR_PROFILING = {os.environ.get('MONITOR_PROFILING')}")
print("-" * 60)

# Start the consumer services
print("Starting consumer services...")
price_updater = subprocess.Popen(
    ["python", "run_price_updater_service.py"],
    creationflags=subprocess.CREATE_NEW_CONSOLE,
    env=os.environ.copy()  # Explicitly pass environment
)

positions_aggregator = subprocess.Popen(
    ["python", "run_positions_aggregator_service.py"],
    creationflags=subprocess.CREATE_NEW_CONSOLE,
    env=os.environ.copy()  # Explicitly pass environment
)

# Wait for consumers to start
print("Waiting 5 seconds for consumers to initialize...")
time.sleep(5)

# Start the producer service
print("Starting producer service...")
producer = subprocess.Popen(
    ["python", "run_spot_risk_watcher.py"],
    creationflags=subprocess.CREATE_NEW_CONSOLE,
    env=os.environ.copy()  # Explicitly pass environment
)

print("\nAll services started with profiling enabled.")
print("Check logs/observatory.db for profiling results.")
print("\nPress Ctrl+C to stop all services...")

try:
    # Wait for user to stop
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping services...")
    producer.terminate()
    price_updater.terminate()
    positions_aggregator.terminate()
    print("Services stopped.") 