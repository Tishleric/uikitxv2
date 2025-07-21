import pandas as pd

class PNLSummary:
    def generate(self, positions_df: pd.DataFrame, trades_df: pd.DataFrame) -> pd.DataFrame:
        summary = []
        total_unrealized = positions_df['Unrealized_PNL'].sum() if not positions_df.empty else 0
        total_realized = trades_df['Realized_PNL'].sum() if not trades_df.empty else 0
        total_pnl = total_unrealized + total_realized
        daily_pnl = positions_df['Daily_PNL'].sum() if not positions_df.empty else 0

        summary.extend([
            {'Metric': 'Total PNL', 'Value': total_pnl, 'Details': 'Realized + Unrealized'},
            {'Metric': 'Daily PNL', 'Value': daily_pnl, 'Details': 'From prior close'},
            {'Metric': 'Realized PNL', 'Value': total_realized, 'Details': 'From closed trades'},
            {'Metric': 'Unrealized PNL', 'Value': total_unrealized, 'Details': 'Open positions'},
            {'Metric': 'Active Positions', 'Value': len(positions_df), 'Details': 'Open count'},
            {'Metric': 'Total Trades', 'Value': len(trades_df), 'Details': 'Executed trades'}
        ])

        return pd.DataFrame(summary)
