"""Generate mock market price data for testing P&L system."""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import os

def get_futures_prices():
    """Generate futures price data."""
    # Base futures - roughly matching the provided examples
    futures = [
        {'bloomberg': 'TU', 'base_price': 103.7},
        {'bloomberg': 'FV', 'base_price': 108.3},
        {'bloomberg': 'TY', 'base_price': 111.075},
        {'bloomberg': 'US', 'base_price': 114.281},
        {'bloomberg': 'RX', 'base_price': 129.56},
        {'bloomberg': 'ZN', 'base_price': 111.075},  # Add ZN for options
        {'bloomberg': 'XCMEFFDPSX20250919U0ZN', 'base_price': 2.5},  # Add special format future
    ]
    
    rows = []
    for future in futures:
        # Add some small variations for bid/ask spread
        settle = future['base_price']
        last = settle + np.random.uniform(-0.02, 0.02)
        bid = last - 0.003125  # Small spread
        ask = last + 0.003125
        
        rows.append({
            'bloomberg': future['bloomberg'],
            'PX_SETTLE': round(settle, 6),
            'PX_LAST': round(last, 6),
            'PX_BID': round(bid, 6),
            'PX_ASK': round(ask, 6)
        })
    
    return rows

def get_next_expiry_dates(base_date, count=10):
    """Get next N expiry dates (Mon/Wed/Fri only)."""
    expiries = []
    current = base_date
    
    while len(expiries) < count:
        # Find next Mon(0), Wed(2), or Fri(4)
        weekday = current.weekday()
        if weekday in [0, 2, 4]:
            expiries.append(current)
        current += timedelta(days=1)
    
    return expiries

def generate_option_chain(underlying_symbol, underlying_price, expiry_date, base_date):
    """Generate option chain for a specific expiry in XCME format."""
    rows = []
    
    # ATM strike (round to nearest 0.25)
    atm_strike = round(underlying_price * 4) / 4
    
    # Generate strikes around ATM
    # For the mock data, let's generate fewer strikes to match the trades
    strikes = []
    for i in range(-8, 9):  # ±2 points in 0.25 increments
        strike = atm_strike + (i * 0.25)
        strikes.append(round(strike, 3))
    
    # Days to expiry
    dte = (expiry_date - base_date).days
    
    # Determine exchange code based on weekday
    weekday = expiry_date.weekday()
    if weekday == 0:  # Monday
        exchange_code = 'VY'
    elif weekday == 2:  # Wednesday
        exchange_code = 'WY'
    elif weekday == 4:  # Friday
        exchange_code = 'ZN'
    else:
        return []  # Skip non-standard expiries
    
    for strike in strikes:
        # Determine moneyness
        call_moneyness = 'ITM' if strike < underlying_price else 'OTM'
        put_moneyness = 'ITM' if strike > underlying_price else 'OTM'
        
        # Simple Black-Scholes-like pricing (simplified for mock data)
        distance_from_atm = abs(strike - atm_strike)
        impl_vol = 0.08 + distance_from_atm * 0.01  # Base vol + skew
        
        # Time value decay
        time_factor = max(0.1, dte / 365)
        
        # Call option
        intrinsic_call = max(0, underlying_price - strike)
        time_value_call = impl_vol * np.sqrt(time_factor) * underlying_price * 0.4
        call_price = intrinsic_call + time_value_call * np.random.uniform(0.8, 1.2)
        
        # Put option  
        intrinsic_put = max(0, strike - underlying_price)
        time_value_put = impl_vol * np.sqrt(time_factor) * underlying_price * 0.4
        put_price = intrinsic_put + time_value_put * np.random.uniform(0.8, 1.2)
        
        # Format expiry date
        expiry_str = expiry_date.strftime('%Y-%m-%d')
        
        # Generate XCME-style option codes
        # Format: XCMEOCADPS20250714N0VY2/108.75 (for puts)
        # Format: XCMEOCADCS20250714N0VY2/108.75 (for calls)
        date_code = expiry_date.strftime('%Y%m%d')
        
        # Format strike - remove unnecessary .0 for integers
        strike_str = str(int(strike)) if strike == int(strike) else str(strike)
        
        # Generate both CAD and PAD patterns, and both 2 and 3 suffixes
        patterns = ['CAD', 'PAD']
        suffixes = ['2', '3']
        
        for pattern in patterns:
            for suffix in suffixes:
                # Call option
                call_code = f"XCMEO{pattern}CS{date_code}N0{exchange_code}{suffix}/{strike_str}"
                call_bid = call_price - 0.015625  # 1/64 spread
                call_ask = call_price + 0.015625
                
                rows.append({
                    'bloomberg': call_code,
                    'PX_SETTLE': round(call_price, 6),
                    'PX_LAST': round(call_price, 6),
                    'PX_BID': round(call_bid, 6),
                    'PX_ASK': round(call_ask, 6),
                    'OPT_EXPIRE_DT': expiry_str,
                    'MONEYNESS': call_moneyness
                })
                
                # Put option
                put_code = f"XCMEO{pattern}PS{date_code}N0{exchange_code}{suffix}/{strike_str}"
                put_bid = put_price - 0.015625
                put_ask = put_price + 0.015625
                
                rows.append({
                    'bloomberg': put_code,
                    'PX_SETTLE': round(put_price, 6),
                    'PX_LAST': round(put_price, 6),
                    'PX_BID': round(put_bid, 6),
                    'PX_ASK': round(put_ask, 6),
                    'OPT_EXPIRE_DT': expiry_str,
                    'MONEYNESS': put_moneyness
                })
    
    return rows

def generate_market_prices(base_date, time_of_day='17:00'):
    """Generate complete market price dataset."""
    all_rows = []
    
    # Add futures
    all_rows.extend(get_futures_prices())
    
    # Get futures prices for option generation
    futures_map = {row['bloomberg']: row['PX_SETTLE'] for row in all_rows}
    
    # Generate options for ZN (as an example)
    if 'ZN' in futures_map:
        expiries = get_next_expiry_dates(base_date, count=10)
        for expiry in expiries:
            option_rows = generate_option_chain('ZN', futures_map['ZN'], expiry, base_date)
            all_rows.extend(option_rows)
    
    # Create DataFrame
    df = pd.DataFrame(all_rows)
    
    # For 3pm files, modify PX_LAST slightly
    if time_of_day == '15:00':
        df['PX_LAST'] = df['PX_LAST'] + np.random.uniform(-0.01, 0.01, size=len(df))
        df['PX_LAST'] = df['PX_LAST'].round(6)
    
    return df

def main():
    """Generate mock market price files."""
    # Ensure directory exists
    os.makedirs('data/input/market_prices', exist_ok=True)
    
    # Generate for a few days
    dates = [
        (date(2025, 7, 11), '17:00'),  # Previous day 5pm
        (date(2025, 7, 12), '15:00'),  # Today 3pm
        (date(2025, 7, 12), '17:00'),  # Today 5pm
        (date(2025, 7, 13), '17:00'),  # Next day 5pm
        (date(2025, 7, 14), '15:00'),  # Current day 3pm
        (date(2025, 7, 14), '17:00'),  # Current day 5pm
    ]
    
    for price_date, time in dates:
        df = generate_market_prices(price_date, time)
        
        # Save to CSV
        filename = f"market_prices_{price_date.strftime('%Y%m%d')}_{time.replace(':', '')}.csv"
        filepath = os.path.join('data/input/market_prices', filename)
        df.to_csv(filepath, index=False)
        
        print(f"Generated {filename} with {len(df)} rows")
        print(f"  - Futures: {len(df[df['OPT_EXPIRE_DT'].isna()])}")
        print(f"  - Options: {len(df[df['OPT_EXPIRE_DT'].notna()])}")

if __name__ == "__main__":
    main() 