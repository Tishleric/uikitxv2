import sqlite3
import json

conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
cursor = conn.cursor()

cursor.execute('SELECT trade_id, Symbol, Action, Quantity, Realized_PNL, Matches FROM tyu5_trades')
rows = cursor.fetchall()

print('Trade ID | Symbol | Action | Qty | P&L    | Matches')
print('-'*80)

for row in rows:
    matches_str = row[5]
    if matches_str:
        # Parse and show first match
        matches = json.loads(matches_str)
        match_info = f"{len(matches)} matches" if matches else "No matches"
    else:
        match_info = "No matches"
    
    print(f'{row[0]:8} | {row[1]:6} | {row[2]:6} | {row[3]:3} | {row[4]:7.2f} | {match_info}')

conn.close() 