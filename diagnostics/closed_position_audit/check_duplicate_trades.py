"""
Diagnostic Script: Check for duplicate trades in realized tables
This will help identify if trades are being processed multiple times
"""
import sqlite3
import pandas as pd
from datetime import datetime

def check_duplicate_trades(db_path='trades.db'):
    """Check for duplicate trades in realized_fifo and realized_lifo tables"""
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("DUPLICATE TRADE ANALYSIS")
    print("=" * 80)
    print(f"Analyzing database: {db_path}")
    print(f"Report generated: {datetime.now()}")
    print()
    
    for method in ['fifo', 'lifo']:
        table_name = f'realized_{method}'
        print(f"\n### Checking {table_name.upper()} table ###")
        
        # First, check if we have any exact duplicate rows
        duplicate_check_query = f"""
        SELECT 
            symbol,
            sequenceIdBeingOffset,
            sequenceIdDoingOffsetting,
            quantity,
            timestamp,
            COUNT(*) as duplicate_count
        FROM {table_name}
        GROUP BY 
            symbol,
            sequenceIdBeingOffset,
            sequenceIdDoingOffsetting,
            quantity,
            timestamp
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC, timestamp DESC
        """
        
        duplicates = pd.read_sql_query(duplicate_check_query, conn)
        
        if len(duplicates) > 0:
            print(f"\n⚠️  FOUND {len(duplicates)} DUPLICATE TRADE ENTRIES!")
            print("\nDuplicate trades:")
            print(duplicates.to_string(index=False))
            
            # Get more details about when these duplicates were inserted
            print("\nDetailed duplicate analysis:")
            for idx, row in duplicates.iterrows():
                detail_query = f"""
                SELECT *
                FROM {table_name}
                WHERE sequenceIdBeingOffset = ?
                  AND sequenceIdDoingOffsetting = ?
                ORDER BY timestamp
                """
                details = pd.read_sql_query(detail_query, conn, 
                    params=[row['sequenceIdBeingOffset'], row['sequenceIdDoingOffsetting']])
                print(f"\nTrade IDs: {row['sequenceIdBeingOffset']} -> {row['sequenceIdDoingOffsetting']}")
                print(f"Symbol: {row['symbol']}, Quantity: {row['quantity']}")
                print(f"Appears {row['duplicate_count']} times")
                print("Timestamps:", details['timestamp'].tolist())
        else:
            print("✅ No duplicate trades found in realized table")
        
        # Check for trades with same IDs but different quantities (partial fills?)
        id_duplicate_query = f"""
        SELECT 
            symbol,
            sequenceIdBeingOffset,
            sequenceIdDoingOffsetting,
            GROUP_CONCAT(quantity) as quantities,
            GROUP_CONCAT(timestamp) as timestamps,
            COUNT(*) as entry_count
        FROM {table_name}
        GROUP BY 
            symbol,
            sequenceIdBeingOffset,
            sequenceIdDoingOffsetting
        HAVING COUNT(*) > 1
        ORDER BY entry_count DESC
        """
        
        id_duplicates = pd.read_sql_query(id_duplicate_query, conn)
        
        if len(id_duplicates) > 0:
            print(f"\n⚠️  Found {len(id_duplicates)} trade ID pairs appearing multiple times")
            print("(May be legitimate partial fills or actual duplicates)")
            print("\nTrade ID duplicates:")
            for idx, row in id_duplicates.iterrows():
                print(f"\nSymbol: {row['symbol']}")
                print(f"Trade IDs: {row['sequenceIdBeingOffset']} -> {row['sequenceIdDoingOffsetting']}")
                print(f"Quantities: {row['quantities']}")
                print(f"Entry count: {row['entry_count']}")
    
    conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_duplicate_trades()