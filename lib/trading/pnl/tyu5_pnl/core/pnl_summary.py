import pandas as pd
import numpy as np

class PNLSummary:
    def generate(self, positions_df: pd.DataFrame, trades_df: pd.DataFrame) -> pd.DataFrame:
        summary = []
        
        # Safe aggregation - skip NaN and string values
        if not positions_df.empty:
            # Convert string values to NaN for numeric operations
            unrealized_vals = pd.to_numeric(positions_df['Unrealized_PNL'], errors='coerce')
            daily_vals = pd.to_numeric(positions_df['Daily_PNL'], errors='coerce')
            
            total_unrealized = unrealized_vals.sum(skipna=True)
            daily_pnl = daily_vals.sum(skipna=True)
            
            # If all values are NaN, set to NaN instead of 0
            if unrealized_vals.isna().all():
                total_unrealized = np.nan
            if daily_vals.isna().all():
                daily_pnl = np.nan
        else:
            total_unrealized = 0
            daily_pnl = 0
            
        total_realized = trades_df['Realized_PNL'].sum() if not trades_df.empty else 0
        
        # Handle total P&L calculation
        if pd.isna(total_unrealized):
            total_pnl = total_realized  # Only show realized if unrealized is unavailable
        else:
            total_pnl = total_unrealized + total_realized

        summary.extend([
            {'Metric': 'Total PNL', 'Value': total_pnl, 'Details': 'Realized + Unrealized'},
            {'Metric': 'Daily PNL', 'Value': daily_pnl, 'Details': 'From prior close'},
            {'Metric': 'Realized PNL', 'Value': total_realized, 'Details': 'From closed trades'},
            {'Metric': 'Unrealized PNL', 'Value': total_unrealized, 'Details': 'Open positions'},
            {'Metric': 'Active Positions', 'Value': len(positions_df), 'Details': 'Open count'},
            {'Metric': 'Total Trades', 'Value': len(trades_df), 'Details': 'Executed trades'}
        ])

        return pd.DataFrame(summary)
