"""Debug the price query issue."""

import sqlite3
from datetime import datetime, date

conn = sqlite3.connect('data/output/pnl/pnl_tracker.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

bloomberg_symbol = "VBYN25C2 110.750 Comdty"
as_of = datetime.now()
as_of_date = as_of.date()
as_of_hour = as_of.hour

print(f"Looking for: {bloomberg_symbol}")
print(f"As of: {as_of} (hour={as_of_hour})")
print(f"Date: {as_of_date}\n")

# Check what data exists for this symbol
print("All records for this symbol:")
cursor.execute("""
    SELECT bloomberg, px_settle, px_last, upload_timestamp, upload_date, upload_hour
    FROM market_prices
    WHERE bloomberg = ?
    ORDER BY upload_timestamp DESC
    LIMIT 5
""", (bloomberg_symbol,))

for row in cursor.fetchall():
    print(f"  {dict(row)}")

# Now run the actual query from get_market_price
print(f"\nRunning get_market_price query (hour < 15: {as_of_hour < 15}):")

if as_of_hour < 15:
    # Use previous day's 5pm px_settle
    query = """
    SELECT px_settle, upload_timestamp
    FROM market_prices
    WHERE bloomberg = ? 
      AND upload_date < ?
      AND upload_hour = 17
    ORDER BY upload_timestamp DESC
    LIMIT 1
    """
    print(f"Query: previous day 5pm settle (upload_date < {as_of_date})")
else:
    # Check for today's 3pm or 5pm
    if as_of_hour < 17:
        query = """
        SELECT px_last, upload_timestamp
        FROM market_prices
        WHERE bloomberg = ? 
          AND upload_date = ?
          AND upload_hour = 15
        ORDER BY upload_timestamp DESC
        LIMIT 1
        """
        print(f"Query: today's 3pm last (upload_date = {as_of_date})")
    else:
        query = """
        SELECT px_settle, upload_timestamp
        FROM market_prices
        WHERE bloomberg = ? 
          AND upload_date = ?
          AND upload_hour = 17
        ORDER BY upload_timestamp DESC
        LIMIT 1
        """
        print(f"Query: today's 5pm settle (upload_date = {as_of_date})")

cursor.execute(query, (bloomberg_symbol, as_of_date))
result = cursor.fetchone()

if result:
    print(f"Result: {dict(result)}")
else:
    print("No result found!")
    
    # Let's see what dates/hours we have
    print("\nAvailable upload dates and hours for this symbol:")
    cursor.execute("""
        SELECT DISTINCT upload_date, upload_hour
        FROM market_prices
        WHERE bloomberg = ?
        ORDER BY upload_date DESC, upload_hour DESC
    """, (bloomberg_symbol,))
    
    for row in cursor.fetchall():
        print(f"  Date: {row['upload_date']}, Hour: {row['upload_hour']}")

conn.close() 