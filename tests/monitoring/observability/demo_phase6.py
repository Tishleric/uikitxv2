#!/usr/bin/env python3
"""Demo: Complete Observability Pipeline - Phase 6

This demo showcases:
1. @monitor decorator automatically sending data to queue
2. Complete integration: Function → Queue → Writer → Database
3. Various function types and data captures
4. Error tracking and performance monitoring
5. Real-world usage patterns
"""

import time
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import json

from lib.monitoring.decorators import monitor, start_observability_writer, stop_observability_writer, get_observability_queue


# Example decorated functions for different use cases

@monitor(process_group="web.api")
def handle_request(endpoint: str, method: str, user_id: int):
    """Simulate handling a web request"""
    time.sleep(0.01)  # Simulate processing
    return {
        "status": 200,
        "data": {"message": f"Hello user {user_id}"},
        "timestamp": datetime.now().isoformat()
    }


@monitor(process_group="data.processing", capture={"args": True, "result": True})
def process_dataframe(df: pd.DataFrame, operations: list):
    """Process a pandas DataFrame with multiple operations"""
    result = df.copy()
    
    for op in operations:
        if op == "normalize":
            result = (result - result.mean()) / result.std()
        elif op == "square":
            result = result ** 2
        elif op == "sum":
            return float(result.sum().sum())
    
    return result


@monitor(process_group="ml.prediction")
def predict_batch(features: np.ndarray, model_name: str = "default"):
    """Simulate ML model prediction"""
    # Simulate model inference
    time.sleep(0.05)
    predictions = np.random.random(len(features))
    
    return {
        "predictions": predictions,
        "model": model_name,
        "confidence": float(predictions.mean())
    }


@monitor(process_group="auth.security", sensitive_fields=("password", "token", "api_key"))
def authenticate_user(username: str, password: str):
    """Authenticate user (with sensitive data masking)"""
    # Simulate auth check
    if username == "admin" and password == "secret123":
        return {
            "success": True,
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "user_id": 1
        }
    else:
        raise ValueError("Invalid credentials")


@monitor(process_group="trading.calculation", sample_rate=0.5)
def calculate_pnl(position: float, entry_price: float, current_price: float):
    """Calculate P&L (with 50% sampling)"""
    pnl = position * (current_price - entry_price)
    return {
        "pnl": pnl,
        "percentage": (current_price / entry_price - 1) * 100
    }


def print_separator(title=""):
    """Print a visual separator"""
    print(f"\n{'='*60}")
    if title:
        print(f" {title}")
        print('='*60)
    print()


def query_database(db_path: str):
    """Query and display database contents"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Process trace summary
    print_separator("Process Trace Summary")
    cursor.execute("""
        SELECT 
            substr(process, 1, 30) as process,
            COUNT(*) as calls,
            AVG(duration_ms) as avg_ms,
            MIN(duration_ms) as min_ms,
            MAX(duration_ms) as max_ms,
            SUM(CASE WHEN status = 'ERR' THEN 1 ELSE 0 END) as errors
        FROM process_trace
        GROUP BY process
        ORDER BY calls DESC
    """)
    
    print(f"{'Process':<30} {'Calls':<8} {'Avg(ms)':<10} {'Min(ms)':<10} {'Max(ms)':<10} {'Errors':<8}")
    print("-" * 86)
    for row in cursor.fetchall():
        process, calls, avg_ms, min_ms, max_ms, errors = row
        print(f"{process:<30} {calls:<8} {avg_ms:<10.2f} {min_ms:<10.2f} {max_ms:<10.2f} {errors:<8}")
    
    # Recent errors
    print_separator("Recent Errors")
    cursor.execute("""
        SELECT ts, process, substr(exception, 1, 100) as error
        FROM process_trace
        WHERE status = 'ERR'
        ORDER BY ts DESC
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        ts, process, error = row
        print(f"[{ts}] {process}")
        print(f"  {error}...")
    
    # Data trace sample
    print_separator("Sample Data Traces")
    cursor.execute("""
        SELECT process, data, data_type, substr(data_value, 1, 60) as value
        FROM data_trace
        WHERE data_type = 'OUTPUT'
        ORDER BY ts DESC
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        process, data_name, data_type, value = row
        print(f"{process} - {data_name}: {value}...")
    
    # Performance stats
    print_separator("Performance Statistics")
    cursor.execute("""
        SELECT 
            COUNT(*) as total_traces,
            SUM(CASE WHEN status = 'OK' THEN 1 ELSE 0 END) as successful,
            SUM(CASE WHEN status = 'ERR' THEN 1 ELSE 0 END) as errors,
            AVG(duration_ms) as avg_duration_ms
        FROM process_trace
    """)
    
    row = cursor.fetchone()
    if row:
        total, successful, errors, avg_duration = row
        print(f"Total function calls: {total}")
        print(f"Successful: {successful} ({successful/total*100:.1f}%)")
        print(f"Errors: {errors} ({errors/total*100:.1f}%)")
        print(f"Average duration: {avg_duration:.2f}ms")
    
    conn.close()


def main():
    """Run the complete observability demo"""
    print("\n🚀 Complete Observability Pipeline Demo - Phase 6")
    print("===============================================")
    
    # Setup
    db_path = "logs/demo_observability_phase6.db"
    Path("logs").mkdir(exist_ok=True)
    
    # Start the observability writer
    print("\n1️⃣ Starting observability writer...")
    writer = start_observability_writer(db_path)
    print(f"   ✅ Writer started → {db_path}")
    
    # Get queue for monitoring
    queue = get_observability_queue()
    
    print_separator("2️⃣ Executing Monitored Functions")
    
    # Web API calls
    print("\n📡 Web API calls:")
    for i in range(5):
        result = handle_request(f"/api/users/{i}", "GET", i)
        print(f"   • GET /api/users/{i} → {result['status']}")
    
    # Data processing
    print("\n📊 Data processing:")
    df = pd.DataFrame({
        "A": [1, 2, 3, 4, 5],
        "B": [10, 20, 30, 40, 50]
    })
    result = process_dataframe(df, ["normalize", "square", "sum"])
    print(f"   • Processed DataFrame → sum: {result:.2f}")
    
    # ML predictions
    print("\n🤖 ML predictions:")
    features = np.random.randn(100, 10)
    result = predict_batch(features, model_name="neural_net_v2")
    print(f"   • Predicted {len(result['predictions'])} samples")
    print(f"   • Average confidence: {result['confidence']:.3f}")
    
    # Authentication (with error)
    print("\n🔐 Authentication:")
    try:
        result = authenticate_user("admin", "secret123")
        print(f"   • Login successful for admin")
    except ValueError:
        pass
    
    try:
        result = authenticate_user("hacker", "wrong")
        print(f"   • Login successful for hacker")
    except ValueError as e:
        print(f"   • Login failed: {e}")
    
    # Trading calculations (sampled)
    print("\n💰 Trading calculations (50% sampling):")
    positions = [(100, 110.5, 112.3), (-50, 98.2, 97.1), (200, 105.0, 106.8)]
    for pos, entry, current in positions:
        try:
            result = calculate_pnl(pos, entry, current)
            print(f"   • Position {pos}: P&L ${result['pnl']:.2f} ({result['percentage']:.2f}%)")
        except:
            # Some calls will be skipped due to sampling
            pass
    
    # Show queue statistics
    print_separator("3️⃣ Queue Statistics")
    stats = queue.get_queue_stats()
    metrics = stats['metrics']
    print(f"Normal queue size: {stats['normal_queue_size']}")
    print(f"Error queue size: {stats['error_queue_size']}")
    print(f"Normal enqueued: {metrics['normal_enqueued']}")
    print(f"Errors enqueued: {metrics['error_enqueued']}")
    print(f"Using overflow: {'Yes' if metrics['overflowed'] > 0 else 'No'}")
    
    # Wait for all data to be written
    print("\n⏳ Waiting for data to be written to database...")
    time.sleep(1.0)
    
    # Query and display results
    query_database(db_path)
    
    # Demonstrate error preservation
    print_separator("4️⃣ Error Preservation Test")
    
    # Create a function that always fails
    @monitor(process_group="test.errors")
    def always_fails(x):
        raise RuntimeError(f"Intentional failure with input: {x}")
    
    # Generate some errors
    for i in range(3):
        try:
            always_fails(f"test_{i}")
        except RuntimeError:
            pass
    
    time.sleep(0.5)
    
    # Verify errors were captured
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM process_trace WHERE process LIKE '%always_fails%' AND status = 'ERR'")
    error_count = cursor.fetchone()[0]
    print(f"Errors captured: {error_count}/3")
    conn.close()
    
    # Stop the writer
    print_separator("5️⃣ Shutting Down")
    writer_metrics = writer.get_metrics()
    print(f"Total records written: {writer_metrics['records_written']}")
    print(f"Write rate: {writer_metrics['records_per_second']:.1f} records/sec")
    print(f"Database size: {writer_metrics['database']['db_size_mb']:.2f} MB")
    
    stop_observability_writer()
    print("\n✅ Observability writer stopped")
    
    print_separator("Summary")
    print("The complete observability pipeline is now operational!")
    print("\nKey features demonstrated:")
    print("  • Automatic function monitoring with @monitor decorator")
    print("  • Zero-configuration queue and database integration")
    print("  • Complex data type serialization")
    print("  • Sensitive data masking")
    print("  • Error tracking with full tracebacks")
    print("  • Sampling for high-frequency functions")
    print("  • Performance metrics and statistics")
    print(f"\n📁 Database saved at: {Path(db_path).absolute()}")
    print("   You can explore it with any SQLite browser!")
    print("\n🎉 The observability system is production-ready!")


if __name__ == "__main__":
    main() 