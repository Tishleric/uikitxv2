import pandas as pd

df = pd.read_csv('../data/input/trade_ledger/trades_20250717.csv')
print('Columns in trades file:')
print(df.columns.tolist())
print('\nFirst few rows:')
print(df.head()) 