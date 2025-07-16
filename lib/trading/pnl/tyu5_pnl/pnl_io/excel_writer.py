import pandas as pd

class ExcelWriterModule:
    def write(self, filename: str,
              trades_df: pd.DataFrame,
              positions_df: pd.DataFrame,
              summary_df: pd.DataFrame,
              risk_df: pd.DataFrame,
              breakdown_df: pd.DataFrame):
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            positions_df.to_excel(writer, sheet_name='Positions', index=False)
            trades_df.to_excel(writer, sheet_name='Trades', index=False)
            risk_df.to_excel(writer, sheet_name='Risk_Matrix', index=False)
            breakdown_df.to_excel(writer, sheet_name='Position_Breakdown', index=False)
