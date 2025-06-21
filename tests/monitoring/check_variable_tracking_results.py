"""Check the results of variable-level tracking in the test database"""

import sqlite3
import pandas as pd
from pathlib import Path

def check_results():
    db_path = "logs/test_variable_tracking.db"
    
    if not Path(db_path).exists():
        print(f"Database {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    
    # Query 1: Show data trace entries for the add function
    print("=" * 80)
    print("1. Variable tracking for add(x, y) function:")
    print("=" * 80)
    query = """
    SELECT process, data, data_type, data_value 
    FROM data_trace 
    WHERE process LIKE '%add%'
    ORDER BY ts DESC, data_type, data
    """
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))
    
    # Query 2: Show data trace entries for divmod_custom (multiple returns)
    print("\n" + "=" * 80)
    print("2. Multiple return values for divmod_custom:")
    print("=" * 80)
    query = """
    SELECT process, data, data_type, data_value 
    FROM data_trace 
    WHERE process LIKE '%divmod_custom%'
    ORDER BY ts DESC, data_type, data
    """
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))
    
    # Query 3: Show data trace entries for get_point (named tuple)
    print("\n" + "=" * 80)
    print("3. Named tuple return for get_point:")
    print("=" * 80)
    query = """
    SELECT process, data, data_type, data_value 
    FROM data_trace 
    WHERE process LIKE '%get_point%'
    ORDER BY ts DESC, data_type, data
    """
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))
    
    # Query 4: Show data trace entries for create_user (dataclass)
    print("\n" + "=" * 80)
    print("4. Dataclass return for create_user:")
    print("=" * 80)
    query = """
    SELECT process, data, data_type, data_value 
    FROM data_trace 
    WHERE process LIKE '%create_user%'
    ORDER BY ts DESC, data_type, data
    """
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))
    
    # Query 5: Show data trace entries for get_stats (dict return)
    print("\n" + "=" * 80)
    print("5. Dictionary return for get_stats:")
    print("=" * 80)
    query = """
    SELECT process, data, data_type, data_value 
    FROM data_trace 
    WHERE process LIKE '%get_stats%'
    ORDER BY ts DESC, data_type, data
    """
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))
    
    # Query 6: Show data trace entries for sum_all (*args)
    print("\n" + "=" * 80)
    print("6. Variable args for sum_all:")
    print("=" * 80)
    query = """
    SELECT process, data, data_type, data_value 
    FROM data_trace 
    WHERE process LIKE '%sum_all%'
    ORDER BY ts DESC, data_type, data
    """
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))
    
    # Query 7: Show overall statistics
    print("\n" + "=" * 80)
    print("7. Overall Statistics:")
    print("=" * 80)
    
    # Count by data type
    query = """
    SELECT data_type, COUNT(*) as count
    FROM data_trace
    GROUP BY data_type
    """
    df = pd.read_sql_query(query, conn)
    print("\nData Type Distribution:")
    print(df.to_string(index=False))
    
    # Count unique parameter names
    query = """
    SELECT COUNT(DISTINCT data) as unique_param_names
    FROM data_trace
    """
    result = conn.execute(query).fetchone()
    print(f"\nUnique parameter names: {result[0]}")
    
    # Show all unique parameter names
    query = """
    SELECT DISTINCT data 
    FROM data_trace
    ORDER BY data
    """
    df = pd.read_sql_query(query, conn)
    print("\nAll unique parameter names:")
    print(", ".join(df['data'].tolist()))
    
    conn.close()

if __name__ == "__main__":
    check_results() 