import argparse
import sqlite3
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Diagnostics: query trades.db for symbol state")
    parser.add_argument("--db", default="trades.db", help="Path to trades.db (default: trades.db)")
    parser.add_argument("--symbol", default="TYU5 Comdty", help="Symbol to inspect (default: TYU5 Comdty)")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sym = args.symbol
    print("=== positions row ===")
    row = cur.execute(
        """
        SELECT symbol, open_position, closed_position,
               fifo_realized_pnl, fifo_unrealized_pnl,
               lifo_realized_pnl, lifo_unrealized_pnl,
               last_updated, last_trade_update
        FROM positions WHERE symbol=?
        """,
        (sym,),
    ).fetchone()
    print(dict(row) if row else None)

    print("\n=== pricing rows ===")
    for r in cur.execute(
        """
        SELECT price_type, price, timestamp
        FROM pricing WHERE symbol=?
        ORDER BY price_type
        """,
        (sym,),
    ):
        print(dict(r))

    print("\n=== realized_fifo today (raw vs adjusted) ===")
    realized_rows = cur.execute(
        """
        WITH today(day) AS (
          SELECT DATE('now')
        ), rf AS (
          SELECT * FROM realized_fifo WHERE symbol=?
            AND DATE(timestamp,
                     CASE WHEN CAST(strftime('%H',timestamp) AS INTEGER) >= 17
                          THEN '+1 day' ELSE '+0 day' END)
                = (SELECT day FROM today)
        )
        SELECT rf.symbol, rf.quantity, rf.entryPrice, rf.exitPrice, rf.realizedPnL AS raw,
               t.buySell AS entry_side, t.time AS entry_time,
               sod.price AS sodTod,
               CASE
                 WHEN DATE(t.time,
                          CASE WHEN CAST(strftime('%H',t.time) AS INTEGER) >= 17
                               THEN '+1 day' ELSE '+0 day' END)
                      <> (SELECT day FROM today)
                   THEN CASE WHEN t.buySell='B'
                             THEN (rf.exitPrice - COALESCE(sod.price, rf.entryPrice)) * rf.quantity * 1000
                             ELSE (COALESCE(sod.price, rf.entryPrice) - rf.exitPrice) * rf.quantity * 1000
                        END
                   ELSE rf.realizedPnL
               END AS adjusted,
               rf.timestamp
        FROM rf
        LEFT JOIN trades_fifo t ON t.sequenceId = rf.sequenceIdBeingOffset
        LEFT JOIN pricing sod ON sod.symbol=rf.symbol AND sod.price_type='sodTod'
        ORDER BY rf.timestamp
        """,
        (sym,),
    ).fetchall()
    for r in realized_rows:
        print(dict(r))

    print("\n=== sum adjusted (expected fifo_realized_pnl) ===")
    sum_row = cur.execute(
        """
        WITH today(day) AS (
          SELECT DATE('now')
        ), rf AS (
          SELECT * FROM realized_fifo WHERE symbol=?
            AND DATE(timestamp,
                     CASE WHEN CAST(strftime('%H',timestamp) AS INTEGER) >= 17
                          THEN '+1 day' ELSE '+0 day' END)
                = (SELECT day FROM today)
        )
        SELECT SUM(CASE
                 WHEN DATE(t.time,
                          CASE WHEN CAST(strftime('%H',t.time) AS INTEGER) >= 17
                               THEN '+1 day' ELSE '+0 day' END)
                      <> (SELECT day FROM today)
                   THEN CASE WHEN t.buySell='B'
                             THEN (rf.exitPrice - COALESCE(sod.price, rf.entryPrice)) * rf.quantity * 1000
                             ELSE (COALESCE(sod.price, rf.entryPrice) - rf.exitPrice) * rf.quantity * 1000
                        END
                   ELSE rf.realizedPnL
               END) AS expected_fifo_realized_pnl
        FROM rf
        LEFT JOIN trades_fifo t ON t.sequenceId = rf.sequenceIdBeingOffset
        LEFT JOIN pricing sod ON sod.symbol=rf.symbol AND sod.price_type='sodTod'
        """,
        (sym,),
    ).fetchone()
    print(dict(sum_row) if sum_row else None)

    print("\n=== open fifo positions (quantity>0) ===")
    for r in cur.execute(
        """
        SELECT sequenceId, buySell, price, quantity, time
        FROM trades_fifo WHERE symbol=? AND quantity>0
        ORDER BY sequenceId
        """,
        (sym,),
    ):
        print(dict(r))

    # Also report computed live PnL from positions row if present
    if row:
        live = (row["fifo_realized_pnl"] or 0) + (row["fifo_unrealized_pnl"] or 0)
        print("\n=== computed PnL Live (fifo_realized_pnl + fifo_unrealized_pnl) ===")
        print(live)

    conn.close()


if __name__ == "__main__":
    main()

