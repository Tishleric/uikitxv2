#!/usr/bin/env python3
"""Helper script to create tables in test database"""

import sqlite3
import sys

sys.path.append('.')
from lib.trading.pnl_fifo_lifo import create_all_tables

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'trades_test.db'
    conn = sqlite3.connect(db_path)
    create_all_tables(conn)
    conn.close()
    print(f"Tables created successfully in {db_path}") 