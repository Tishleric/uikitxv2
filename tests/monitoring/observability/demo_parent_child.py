#!/usr/bin/env python3
"""Demo: Parent-Child Relationship Tracking in Observability System"""

import os
import sys
import time
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Set quiet mode to reduce console noise
os.environ["MONITOR_QUIET"] = "1"

from lib.monitoring.decorators import monitor, start_observability_writer, stop_observability_writer


# Demo functions with nested calls
@monitor(process_group="demo.parent_child")
def parent_function(x: int) -> int:
    """Top-level parent function"""
    print(f"Parent: Processing {x}")
    
    # Call child functions
    result1 = child_function_a(x)
    result2 = child_function_b(x * 2)
    
    # Simulate some work
    time.sleep(0.01)
    
    return result1 + result2


@monitor(process_group="demo.parent_child")
def child_function_a(value: int) -> int:
    """First child function"""
    print(f"  Child A: Processing {value}")
    
    # Call grandchild
    result = grandchild_function(value + 10)
    
    time.sleep(0.005)
    return result * 2


@monitor(process_group="demo.parent_child")
def child_function_b(value: int) -> int:
    """Second child function"""
    print(f"  Child B: Processing {value}")
    
    time.sleep(0.008)
    return value + 5


@monitor(process_group="demo.parent_child")
def grandchild_function(value: int) -> int:
    """Grandchild function"""
    print(f"    Grandchild: Processing {value}")
    
    time.sleep(0.003)
    return value * 3


def analyze_relationships(db_path: str):
    """Query and display parent-child relationships"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("PARENT-CHILD RELATIONSHIPS")
    print("="*80)
    
    # Query the parent-child view
    cursor.execute("""
        SELECT 
            child_process,
            parent_process,
            thread_id,
            relative_depth
        FROM parent_child_traces
        ORDER BY child_ts DESC
        LIMIT 10
    """)
    
    relationships = cursor.fetchall()
    
    print(f"\nFound {len(relationships)} parent-child relationships:\n")
    
    for rel in relationships:
        parent = rel['parent_process'] or "ROOT"
        indent = "  " * rel['relative_depth']
        print(f"Thread {rel['thread_id']}: {parent}")
        print(f"{indent}└─> {rel['child_process']}")
        print()
    
    # Show call tree for a specific execution
    print("\n" + "="*80)
    print("CALL TREE VISUALIZATION")
    print("="*80)
    
    cursor.execute("""
        WITH RECURSIVE call_tree AS (
            -- Find root calls (no parent)
            SELECT 
                ts, process, duration_ms, thread_id, call_depth,
                0 as level,
                process as path,
                start_ts_us,
                start_ts_us + (duration_ms * 1000) as end_ts_us
            FROM process_trace
            WHERE NOT EXISTS (
                SELECT 1 FROM process_trace p2
                WHERE p2.thread_id = process_trace.thread_id
                AND p2.start_ts_us < process_trace.start_ts_us
                AND p2.start_ts_us + (p2.duration_ms * 1000) > process_trace.start_ts_us + (process_trace.duration_ms * 1000)
                AND p2.call_depth < process_trace.call_depth
            )
            AND process LIKE 'demo.parent_child%'
            
            UNION ALL
            
            -- Find children recursively
            SELECT 
                c.ts, c.process, c.duration_ms, c.thread_id, c.call_depth,
                p.level + 1,
                p.path || ' -> ' || c.process,
                c.start_ts_us,
                c.start_ts_us + (c.duration_ms * 1000) as end_ts_us
            FROM process_trace c
            JOIN call_tree p ON (
                c.thread_id = p.thread_id
                AND c.start_ts_us >= p.start_ts_us
                AND c.start_ts_us + (c.duration_ms * 1000) <= p.end_ts_us
                AND c.call_depth > p.call_depth
                AND c.ts != p.ts
            )
        )
        SELECT 
            substr('    ', 1, level*2) || process as display,
            duration_ms,
            call_depth
        FROM call_tree
        ORDER BY start_ts_us, level
        LIMIT 20
    """)
    
    tree_results = cursor.fetchall()
    
    print("\nCall Tree (most recent execution):\n")
    for row in tree_results:
        print(f"{row['display']} [{row['duration_ms']:.2f}ms, depth={row['call_depth']}]")
    
    # Show timing analysis
    print("\n" + "="*80)
    print("TIMING ANALYSIS")
    print("="*80)
    
    cursor.execute("""
        SELECT 
            p.process as parent_process,
            p.duration_ms as parent_duration,
            SUM(c.duration_ms) as children_duration,
            p.duration_ms - SUM(c.duration_ms) as exclusive_duration
        FROM process_trace p
        LEFT JOIN parent_child_traces pc ON p.ts = pc.parent_ts AND p.process = pc.parent_process
        LEFT JOIN process_trace c ON pc.child_ts = c.ts AND pc.child_process = c.process
        WHERE p.process LIKE 'demo.parent_child%'
        GROUP BY p.ts, p.process
        HAVING COUNT(c.ts) > 0
        ORDER BY p.start_ts_us DESC
        LIMIT 5
    """)
    
    timing_results = cursor.fetchall()
    
    print("\nExclusive vs Inclusive Time:\n")
    print(f"{'Function':<50} {'Total':<10} {'Children':<10} {'Exclusive':<10}")
    print("-" * 80)
    
    for row in timing_results:
        print(f"{row['parent_process']:<50} "
              f"{row['parent_duration']:<10.2f} "
              f"{row['children_duration'] or 0:<10.2f} "
              f"{row['exclusive_duration'] or row['parent_duration']:<10.2f}")
    
    conn.close()


def main():
    # Set up database path
    db_path = "logs/demo_parent_child.db"
    
    # Clear existing database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Start the observability writer
    writer = start_observability_writer(db_path=db_path)
    
    print("Running parent-child demo...")
    print("-" * 40)
    
    try:
        # Run the demo functions
        result = parent_function(5)
        print(f"\nResult: {result}")
        
        # Give writer time to flush
        time.sleep(0.5)
        
        # Stop the writer
        stop_observability_writer()
        
        # Analyze the relationships
        analyze_relationships(db_path)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Ensure writer is stopped
        stop_observability_writer()


if __name__ == "__main__":
    main() 