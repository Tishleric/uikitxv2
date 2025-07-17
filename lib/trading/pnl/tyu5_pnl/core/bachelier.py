import numpy as np
import scipy.stats as stats
from scipy.stats import norm
from scipy.optimize import newton, brentq
import os

import pandas as pd
import pandas_market_calendars as mcal
from datetime import datetime
import pytz


import pandas as pd
import pandas_market_calendars as mcal
import pytz
from datetime import datetime

def compute_cme_T(now: datetime, option_symbol: str, calendar_path: str) -> float:
    chicago = pytz.timezone("America/Chicago")
    print(f"[INFO] Original NOW: {now}, Symbol: {option_symbol}")

    # Ensure timezone-aware 'now'
    if now.tzinfo is None:
        now = chicago.localize(now)
    else:
        now = now.astimezone(chicago)
    print(f"[INFO] Localized NOW (Chicago): {now}")

    # Load expiration calendar
    try:
        df = pd.read_csv(calendar_path)
    except Exception as e:
        raise RuntimeError(f"[ERROR] Failed to read CSV: {e}")

    # Get expiry for symbol
    row = df[df['Option Symbol'] == option_symbol]
    if row.empty:
        raise ValueError(f"[ERROR] Option symbol '{option_symbol}' not found.")

    expiry_str = row.iloc[0]['Option Expiration Date (CT)']
    expiry = pd.to_datetime(expiry_str, errors='coerce')
    if pd.isnull(expiry):
        raise ValueError(f"[ERROR] Could not parse expiry: '{expiry_str}'")

    # Ensure timezone-aware expiry
    if expiry.tzinfo is None:
        expiry = chicago.localize(expiry)
    else:
        expiry = expiry.astimezone(chicago)
    print(f"[INFO] Localized EXPIRY (Chicago): {expiry}")

    # Raw fallback delta
    delta_minutes = (expiry - now).total_seconds() / 60 + 1 * 60
    print(f"[INFO] Raw minutes to expiry: {delta_minutes:.2f}")

    cme = mcal.get_calendar("SIFMA_US")


    T_fallback = delta_minutes / (250.0 * 24 * 60)
    print(f"[WARN] Fallback T (year fraction): {T_fallback:.10f}")
    return T_fallback

class BachelierCombined:
    def __init__(self, F, K, T, sigma, r=0.0, option_type='call'):
        self.F = F
        self.K = K
        self.T = T
        self.sigma = sigma
        self.r = r
        self.option_type = option_type
        self._compute_common_terms()

    def _compute_common_terms(self):
        
        self.df = 1.0
        self.sqrtT = np.sqrt(self.T)
        self.d = (self.F - self.K) / (self.sigma * self.sqrtT)
        self.nd = norm.pdf(self.d)
        self.Nd = norm.cdf(self.d)
       
        
    def price(self):
        if self.option_type in ['c','call']:
            return self.df * ((self.F - self.K) * self.Nd + self.sigma * self.sqrtT * self.nd)
        else:
            return self.df * ((self.K - self.F) * norm.cdf(-self.d) + self.sigma * self.sqrtT * self.nd)

    def greeks(self):
        d = self.d
        pdf = self.nd
        sqrtT = self.sqrtT
        sigma = self.sigma
        T = self.T

        # First order
        delta = self.Nd
        vega = sqrtT * pdf
        theta = -sigma * pdf / (2 * sqrtT)
        # Second order
        gamma = pdf / (sigma * sqrtT)
        volga = pdf * d * (d**2 - 1) * sqrtT / sigma
        # Cross second order
        vanna = -d * pdf / sigma
        charm = -pdf * d / (2 * T)
        veta = pdf * (d**2 - 1) / (2 * sqrtT)
        # Third order
        speed = -d * pdf / (sigma**2 * T)
        ultima = pdf * sqrtT * d * (3 - d**2)

        return {
            'price': self.price(),
            'delta': delta,
            'vega': vega,
            'theta': theta,
            'gamma': gamma,
            'volga': volga,
            'vanna': vanna,
            'charm': charm,
            'veta': veta,
            'speed': speed,
            'ultima': ultima,
        }

class SafeBachelierVol:
    def __init__(self, F, K, T, r, P, option_type='call'):
        self.F = F
        self.K = K
        self.T = T
        self.r = r
        self.P = P
        self.option_type = option_type

    def price_diff(self, sigma):
        model = BachelierCombined(self.F, self.K, self.T, sigma, self.r, self.option_type)
        return model.price() - self.P

    def vega(self, sigma):
        model = BachelierCombined(self.F, self.K, self.T, sigma, self.r, self.option_type)
        return model.greeks()['vega']

    def __call__(self, initial_guess=5.0, tol=1e-8, maxiter=100):
        if self.T <= 0:
            raise ValueError("Time to expiry must be positive.")
        if self.P < 0:
            raise ValueError("Observed price must be non-negative.")

        try:
            sigma_newton = newton(
                func=self.price_diff,
                fprime=self.vega,
                x0=initial_guess,
                tol=tol,
                maxiter=maxiter
            )
            # Confirm result is usable
            if sigma_newton <= 0 or np.isnan(sigma_newton):
                raise RuntimeError("Newton result invalid.")
            return sigma_newton
        except (RuntimeError, ValueError, ZeroDivisionError, OverflowError):
            # Fallback: bracketed solver
            try:
                sigma_brentq = brentq(
                    self.price_diff,
                    1e-6,
                    5.0,
                    maxiter=maxiter,
                    xtol=tol
                )
                return sigma_brentq
            except Exception as e:
                raise RuntimeError(f"Vol solver failed completely: {e}")

def decompose_option_pnl(
    greeks: dict,
    dPx: float,
    dVol: float,
    dT: float,
    option_price_old: float,
    option_price_new: float
) -> dict:
    """
    Decomposes option PnL into Delta, Gamma, Vega, Theta, and Speed components.

    Parameters:
        greeks (dict): Output from model, must include delta, gamma, vega, theta, speed
        dPx (float): Change in futures price
        dVol (float): Change in implied vol
        dT (float): Change in time (year fraction)
        option_price_old (float): Previous option price
        option_price_new (float): New option price

    Returns:
        dict: Component-wise dollar attribution and residual
    """
    delta_pnl = greeks['delta'] * dPx
    gamma_pnl = 0.5 * greeks['gamma'] * dPx**2
    vega_pnl = greeks['vega'] * dVol
    theta_pnl = greeks['theta'] * dT
    speed_pnl = (1/6) * greeks.get('speed', 0.0) * dPx**3
    

    predicted_pnl = delta_pnl + gamma_pnl + vega_pnl + theta_pnl + speed_pnl 
    actual_pnl = option_price_new - option_price_old
    residual = actual_pnl - predicted_pnl

    return {
        'delta': delta_pnl,
        'gamma': gamma_pnl,
        'vega': vega_pnl,
        'theta': theta_pnl,
        'speed': speed_pnl,
        'predicted_pnl': predicted_pnl,
        'actual_pnl': actual_pnl,
        'residual': residual
    }
def run_pnl_attribution(
    now,
    option_symbol,
    calendar_csv,
    F,
    K,
    P,
    Prior,
    F_prior,
    dT,
    option_type='call',
    r=0.01
):
    """
    Computes full PnL attribution for a given Bond Future Option.

    Parameters:
        now (datetime): Current timestamp
        option_symbol (str): Option symbol code
        calendar_csv (str): Path to expiration calendar
        F (float): Current futures price
        K (float): Strike price
        P (float): Current option price
        Prior (float): Prior option settlement
        F_prior (float): Prior futures price
        dT (float): Time decay (year fraction)
        option_type (str): 'call' or 'put',
        r (float): Risk-free rate
    Returns:
        dict: Decomposed attribution results
    """
   
    # Compute expiry time
    T = compute_cme_T(now, option_symbol, calendar_csv)

    # Implied vol and Greeks for current
    iv_now = SafeBachelierVol(F=F, K=K, T=T, r=r, P=P, option_type=option_type)()
    model_now = BachelierCombined(F=F, K=K, T=T, sigma=iv_now, r=r, option_type=option_type)
    print(f"[INFO] Current Implied Vol: {iv_now:.6f}, Price: {model_now.price():.6f}")
    # Implied vol and Greeks for prior
    T_prior = T + dT
    iv_prior = SafeBachelierVol(F=F_prior, K=K, T=T_prior, r=r, P=Prior, option_type=option_type)()
    model_prior = BachelierCombined(F=F_prior, K=K, T=T_prior, sigma=iv_prior, r=r, option_type=option_type)
    print(f"[INFO] Prior Implied Vol: {iv_prior:.6f}, Price: {model_prior.price():.6f}")
    # PnL decomposition
    dPx = F - F_prior
    dVol = iv_now - iv_prior

    attribution = decompose_option_pnl(
        greeks=model_prior.greeks(),
        dPx=dPx,
        dVol=dVol,
        dT=dT,
        option_price_old=Prior,
        option_price_new=P
    )

    return {
        'symbol': option_symbol,
        'T': T,
        'iv_now': iv_now,
        'iv_prior': iv_prior,
        'price_now': model_now.price(),
        'price_prior': model_prior.price(),
        'greeks_now': model_now.greeks(),
        'greeks_prior': model_prior.greeks(),
        'attribution': attribution
    }
def main():
    from datetime import datetime

    # === Input parameters ===
    now = datetime.now()
    option_symbol = 'ZN3N5'
    # Get the path relative to this script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    calendar_csv = os.path.join(script_dir, 'ExpirationCalendar.csv')

    # Pricing & prior setup
    F = 110 + 9.0 / 32         # Current futures price
    K = 110.25                 # Option strike
    P =  0.140625               # Current option price
    Prior =  0.5625          # Prior settlement price
    F_prior = F + 15.5 / 32    # Previous futures level
    dT = 1 / 252.0             # Time decay (1 trading day)

    # === Call modular attribution function ===
    result = run_pnl_attribution(
        now=now,
        option_symbol=option_symbol,
        calendar_csv=calendar_csv,
        F=F,
        K=K,
        P=P,
        Prior=Prior,
        F_prior=F_prior,
        option_type='call',
        dT=dT
    )

    print(f"\n📊 PnL Attribution for {result['symbol']}:")
    print(f" - Time to expiry (T): {result['T']:.10f}")
    print(f" - Implied Vol (now): {result['iv_now']:.6f}")
    print(f" - Implied Vol (prior): {result['iv_prior']:.6f}")
    print(f" - Option Price (now): {result['price_now']:.6f}")
    print(f" - Option Price (prior): {result['price_prior']:.6f}\n")

    for k, v in result['attribution'].items():
        print(f" - {k:16}: {v:>8.6f}")

if __name__ == "__main__":
    main()
