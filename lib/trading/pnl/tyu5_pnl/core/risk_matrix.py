import pandas as pd
import numpy as np
from core.utils import decimal_to_32nds
from core.bachelier import BachelierCombined  # Adjust import as needed

class RiskMatrix:
    def create(self, positions_df: pd.DataFrame, base_price: float = 120.0,
               price_range: tuple = (-3, 3), steps: int = 13, 
               vol: float = 5.0, T: float = 0.25, r: float = 0.0) -> pd.DataFrame:
        """
        Generate a risk matrix for both futures and options using BachelierCombined for options.
        """
        risk_data = []
        price_changes = np.linspace(price_range[0], price_range[1], steps)

        for change in price_changes:
            scenario_price = base_price + change
            total_pnl = 0

            for _, pos in positions_df.iterrows():
                qty = pos['Net_Quantity']
                entry = pos['Avg_Entry_Price']
                symbol = pos['Symbol']
                type_ = pos['Type']

                if type_ == 'FUT':
                    pnl = qty * (scenario_price - entry) * 1000
                elif type_ in ['CALL', 'PUT']:
                    # Use BachelierCombined for option pricing
                    option_type = 'call' if type_ == 'CALL' else 'put'
                    K = pos.get('Strike', entry)  # Use entry as fallback for strike
                    model = BachelierCombined(
                        F=scenario_price, K=K, T=T, r=r, sigma=vol, option_type=option_type
                    )
                    price_today = model.price()
                    # Price at entry (for PNL calculation)
                    model_entry = BachelierCombined(
                        F=entry, K=K, T=T, r=r, sigma=vol, option_type=option_type
                    )
                    price_entry = model_entry.price()
                    pnl = qty * (price_today - price_entry) * 1000
                else:
                    # fallback for unknown types
                    pnl = 0

                total_pnl += pnl

                risk_data.append({
                    'Position_ID': symbol,
                    'TYU5_Price': scenario_price,
                    'TYU5_Price_32nds': decimal_to_32nds(scenario_price),
                    'Price_Change': change,
                    'Scenario_PNL': total_pnl                })

        return pd.DataFrame(risk_data)