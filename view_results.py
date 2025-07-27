import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('trades.db')

# Get tables
cursor = conn.cursor()
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables in database:", [t[0] for t in tables])

# Get daily positions
daily_pos = pd.read_sql_query("SELECT * FROM daily_positions ORDER BY date, method", conn)

if not daily_pos.empty:
    print("\nDaily Positions Summary:")
    print("="*80)
    print(daily_pos[['date', 'method', 'open_position', 'closed_position', 'realized_pnl', 'unrealized_pnl']])
    
    print("\n" + "="*50)
    print("SUMMARY BY METHOD:")
    print("="*50)
    
    for method in ['fifo', 'lifo']:
        method_data = daily_pos[daily_pos['method'] == method]
        if not method_data.empty:
            total_realized = method_data['realized_pnl'].sum()
            final_unrealized = method_data.iloc[-1]['unrealized_pnl']
            total_pnl = total_realized + final_unrealized
            
            print(f"\n{method.upper()} Method:")
            print(f"  Number of days: {len(method_data)}")
            print(f"  Total Realized P&L: ${total_realized:,.2f}")
            print(f"  Final Unrealized P&L: ${final_unrealized:,.2f}")
            print(f"  Total P&L: ${total_pnl:,.2f}")
            
            # Show final position
            final_pos = method_data.iloc[-1]['open_position']
            print(f"  Final Open Position: {final_pos}")
else:
    print("\nNo daily positions found in database")

# Check for trades
for method in ['fifo', 'lifo']:
    trades_count = cursor.execute(f"SELECT COUNT(*) FROM trades_{method}").fetchone()[0]
    realized_count = cursor.execute(f"SELECT COUNT(*) FROM realized_{method}").fetchone()[0]
    print(f"\n{method.upper()} - Unrealized trades: {trades_count}, Realized trades: {realized_count}")

conn.close() 