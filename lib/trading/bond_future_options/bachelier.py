import datetime
from scipy.stats import norm
import scipy.optimize as opt
import numpy as np
from datetime import datetime, timedelta
import pytz

# Define CME holidays (adjust based on official dates)
CME_HOLIDAYS = {
    "2025-01-01", "2025-01-20", "2025-02-17", "2025-04-18", "2025-05-26",
    "2025-06-19", "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25"
}

# Set timezone to Central Time (CT)
CT_ZONE = pytz.timezone("America/Chicago")

def minutes_until_expiry_excluding_cme_holidays(expiry_str, fmt_str="%Y%m%d %H:%M"):
    now = datetime.now(pytz.utc).astimezone(CT_ZONE)  # Convert current time to CT
    expiry_datetime = CT_ZONE.localize(datetime.strptime(expiry_str, fmt_str))  # Convert expiry date to CT
    total_minutes = 0
    current_datetime = now

    while current_datetime < expiry_datetime:
        date_str = current_datetime.strftime("%Y-%m-%d")
        if current_datetime.weekday() < 5 and date_str not in CME_HOLIDAYS:  # Only business days
            minutes_to_next_midnight = (1440 - current_datetime.hour * 60 - current_datetime.minute)
            total_minutes += min(minutes_to_next_midnight, (expiry_datetime - current_datetime).total_seconds() // 60)
        current_datetime += timedelta(days=1)
        current_datetime = current_datetime.replace(hour=0, minute=0)  # Reset to midnight for the next day
    
    return int(total_minutes)+1


def time_to_expiry_years(expiry_str, evaluation_datetime=None, fmt_str="%Y%m%d %H:%M"):
    """
    Calculate time to expiry in years from evaluation datetime.
    
    Args:
        expiry_str: Expiry datetime string (e.g., "20250716 14:00")
        evaluation_datetime: Starting datetime (default: current time in CT)
        fmt_str: Format string for expiry_str
        
    Returns:
        float: Time to expiry in years (business year fraction)
    """
    if evaluation_datetime is None:
        evaluation_datetime = datetime.now(pytz.utc).astimezone(CT_ZONE)
    else:
        # Ensure evaluation_datetime is in CT timezone
        if evaluation_datetime.tzinfo is None:
            evaluation_datetime = CT_ZONE.localize(evaluation_datetime)
        else:
            evaluation_datetime = evaluation_datetime.astimezone(CT_ZONE)
    
    expiry_datetime = CT_ZONE.localize(datetime.strptime(expiry_str, fmt_str))
    total_minutes = 0
    current_datetime = evaluation_datetime

    while current_datetime < expiry_datetime:
        date_str = current_datetime.strftime("%Y-%m-%d")
        if current_datetime.weekday() < 5 and date_str not in CME_HOLIDAYS:  # Only business days
            minutes_to_next_midnight = (1440 - current_datetime.hour * 60 - current_datetime.minute)
            total_minutes += min(minutes_to_next_midnight, (expiry_datetime - current_datetime).total_seconds() // 60)
        current_datetime += timedelta(days=1)
        current_datetime = current_datetime.replace(hour=0, minute=0)  # Reset to midnight for the next day
    
    minutes = int(total_minutes) + 1
    days = minutes / 1440.0
    years = days / 252.0  # Business year fraction
    return years
class OptionBachelier: 
    def __init__(self, S0, K, T, sigma, call_put='call'):
        self.S0 = S0  # Current stock price
        self.K = K    # Strike price
        self.T = T    # Time to maturity in years
        self.sigma = sigma  # Volatility of the underlying asset
        self.call_put = call_put

    def d1(self):
        return (self.S0 - self.K) / (self.sigma * (self.T ** 0.5))

    def call_price(self):
        d1 = self.d1()
        return (self.S0 - self.K) * norm.cdf(d1) + (self.sigma * (self.T ** 0.5)) * norm.pdf(d1) 
    def put_price(self):    
        d1 = self.d1()
        return (self.K - self.S0) * norm.cdf(-d1) + (self.sigma * (self.T ** 0.5)) * norm.pdf(-d1)
    def price(self):
        if self.call_put == 'call':
            return self.call_price()
        elif self.call_put == 'put':
            return self.put_price()
        else:
            raise ValueError("call_put must be either 'call' or 'put'")
    def solve_for_sigma(self, market_price):
        def objective_function(sigma):
            self.sigma = sigma
            return self.price() - market_price
        
        # Initial guess for sigma
        initial_guess = 5
        
        # Use a numerical solver to find the root
        result = opt.root_scalar(objective_function, method='secant',  x0=initial_guess)
        
        if result.converged:
            return result.root
        else:
            raise ValueError("Could not find a solution for sigma")
    def implied_volatility(self, market_price):
        try:
            return self.solve_for_sigma(market_price)
        except ValueError as e:
            print(f"Error in calculating implied volatility: {e}")
            return None
def calculate_implied_volatility(S, K, days, price, call_put='put', initial_vol=5):
    """
    Calculate implied volatility and option price using Bachelier model.

    Args:
        S (float): Spot price
        K (float): Strike price 
        days (float): Days to expiry
        price (float): 
        call_put (str): 'put' or 'call'
        initial_vol (float): Initial volatility estimate (default=5)

    Returns:
        tuple: (Implied volatility, Option price)
    """
    S_float = S
    K_float = K
    price_float = price

    x = OptionBachelier(S0=S_float, K=K_float, T=days/252.0, sigma=initial_vol, call_put=call_put)
    vol = x.solve_for_sigma(price_float)

    return vol, x.price()
def main():
    
    # Example usage
    expiry_str = "20250618 14:00"  # Expiry date in YYYYMMDD HH:MM format using Central Time
    days = minutes_until_expiry_excluding_cme_holidays(expiry_str) / 1440.0  # Convert minutes to days

    S = 110+19.5/32  # Spot price in 32nds
    K = 110+0/32  # Strike price in 32nds
    market_price = 0+5/64  # Price in 64ths

    vol, opt_price = calculate_implied_volatility(S, K, days, market_price)

    print(f"Days to expiry: {days:.3f}")
    print(f"Implied volatility: {vol:.4f}")
    print(f"Option price using Bachelier model: {opt_price:.4f}")
    print(f"Market price : {market_price:.4f}")
if __name__ == "__main__":
    main()