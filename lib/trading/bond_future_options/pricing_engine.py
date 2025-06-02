import numpy as np

from scipy.stats import norm

import pandas as pd

import matplotlib.pyplot as plt

from math import exp

 

class BondFutureOption:

    """

    Bond Future Option pricing using Bachelier model with Future DV01 and Convexity adjustments

   

    This class specifically handles bond future options by:

    1. Converting yield volatility to future price volatility using Future DV01

    2. Adjusting Greeks for Future Convexity effects

    3. Accounting for the unique risk characteristics of bond futures

    4. Providing comprehensive Greeks analysis across moneyness spectrum

    """

   

    def __init__(self, future_dv01, future_convexity, yield_level=0.05):

        """

        Initialize Bond Future Option model

       

        Parameters:

        future_dv01: DV01 of the bond future (price change per 1bp yield change)

        future_convexity: Convexity of the bond future

        yield_level: Current yield level (used for convexity adjustments)

        """

        self.future_dv01 = future_dv01

        self.future_convexity = future_convexity

        self.yield_level = yield_level

       

        # Store both DV01 and convexity for calculations

        print(f"Bond Future Characteristics:")

        print(f"  Future DV01: {self.future_dv01:.6f}")

        print(f"  Future Convexity: {self.future_convexity:.6f}")

        print(f"  Yield Level: {self.yield_level:.4f}")

   

    def convert_price_to_yield_volatility(self, price_volatility):

        """Convert price volatility to yield volatility using Future DV01"""

        return price_volatility / self.future_dv01

   

    def convert_yield_to_future_price_volatility(self, yield_volatility):

        """Convert yield volatility to future price volatility using Future DV01"""

        return self.future_dv01 * yield_volatility

   

    def bachelier_future_option_price(self, F, K, T, price_volatility, option_type='call'):

        """Price bond future option using Bachelier model with price volatility input"""

        if T <= 0:

            return max(F - K, 0) if option_type == 'call' else max(K - F, 0)

       

        # Use price volatility directly (futures trade in price terms)

        future_price_volatility = price_volatility

       

        # Standard Bachelier pricing

        sigma_sqrt_T = future_price_volatility * np.sqrt(T)

        d = (F - K) / sigma_sqrt_T

        print(d)

        if option_type == 'call':

            price = (F - K) * norm.cdf(d) + sigma_sqrt_T * norm.pdf(d)

        else:  # put

            price = (K - F) * norm.cdf(-d) + sigma_sqrt_T * norm.pdf(d)

        return price

   

    # --- F-SPACE GREEKS (Price Greeks) ---

 

    def delta_F(self, F, K, T, price_volatility, option_type='call'):

        if T <= 0:

            return 1.0 if (option_type == 'call' and F > K) else (0.0 if option_type == 'call' else (-1.0 if F < K else 0.0))

        sigma_sqrt_T = price_volatility * np.sqrt(T)

        d = (F - K) / sigma_sqrt_T

        return norm.cdf(d) if option_type == 'call' else norm.cdf(d) - 1.0

 

    def gamma_F(self, F, K, T, price_volatility):

        if T <= 0:

            return 0.0

        sigma_sqrt_T = price_volatility * np.sqrt(T)

        d = (F - K) / sigma_sqrt_T

        return norm.pdf(d) / sigma_sqrt_T

 

    def vega_price(self, F, K, T, price_volatility):

        if T <= 0:

            return 0.0

        sigma_sqrt_T = price_volatility * np.sqrt(T)

        d = (F - K) / sigma_sqrt_T

        return np.sqrt(T) * norm.pdf(d)

 

    def theta_F(self, F, K, T, price_volatility):

        if T <= 0:

            return 0.0

        sigma_sqrt_T = price_volatility * np.sqrt(T)

        d = (F - K) / sigma_sqrt_T

        return -price_volatility * norm.pdf(d) / (2 * np.sqrt(T))/252.0

 

    def volga_price(self, F, K, T, price_volatility):

        if T <= 0 or price_volatility == 0:

            return 0.0

        sigma_sqrt_T = price_volatility * np.sqrt(T)

        d = (F - K) / sigma_sqrt_T

        vega = self.vega_price(F, K, T, price_volatility)

        return vega * d * (d**2 - 1) / price_volatility

 

    def vanna_F_price(self, F, K, T, price_volatility):

        if T <= 0:

            return 0.0

        sigma_sqrt_T = price_volatility * np.sqrt(T)

        d = (F - K) / sigma_sqrt_T

        return -norm.pdf(d) * d / sigma_sqrt_T if sigma_sqrt_T != 0 else 0.0

 

    def charm_F(self, F, K, T, price_volatility):

        if T <= 0:

            return 0.0

        sigma_sqrt_T = price_volatility * np.sqrt(T)

        d = (F - K) / sigma_sqrt_T

        return norm.pdf(d) * (2*price_volatility*T - d*sigma_sqrt_T) / (2*T*sigma_sqrt_T) if T != 0 and sigma_sqrt_T != 0 else 0.0

 

    def speed_F(self, F, K, T, price_volatility):

        if T <= 0:

            return 0.0

        gamma = self.gamma_F(F, K, T, price_volatility)

        sigma_sqrt_T = price_volatility * np.sqrt(T)

        d = (F - K) / sigma_sqrt_T

        return -gamma * (d/sigma_sqrt_T + 1/sigma_sqrt_T) if sigma_sqrt_T != 0 else 0.0

 

    def color_F(self, F, K, T, price_volatility):

        if T <= 0:

            return 0.0

        sigma_sqrt_T = price_volatility * np.sqrt(T)

        d = (F - K) / sigma_sqrt_T

        return -norm.pdf(d) / (2*T*sigma_sqrt_T) * (2*price_volatility*T + 1 - d**2) if T != 0 and sigma_sqrt_T != 0 else 0.0

 

    # --- Y-SPACE GREEKS (Yield Greeks) ---

 

    def delta_y(self, F, K, T, price_volatility, option_type='call'):

        return self.delta_F(F, K, T, price_volatility, option_type) * self.future_dv01

 

    def gamma_y(self, F, K, T, price_volatility, option_type='call'):

        gamma_F = self.gamma_F(F, K, T, price_volatility)

        delta_F = self.delta_F(F, K, T, price_volatility, option_type)

        dF_dy = -self.future_dv01

        d2F_dy2 = self.future_convexity

        return gamma_F * (dF_dy**2) + delta_F * d2F_dy2

 

    def vega_y(self, F, K, T, price_volatility):

        return self.vega_price(F, K, T, price_volatility) * self.future_dv01

 

    def cross_gamma_F_y(self, F, K, T, price_volatility):

        return self.gamma_F(F, K, T, price_volatility) * -self.future_dv01

 

    def vanna_y_yield(self, F, K, T, price_volatility):

        return self.vanna_F_price(F, K, T, price_volatility) * (-self.future_dv01) * self.future_dv01

 

    def charm_y(self, F, K, T, price_volatility):

        return self.charm_F(F, K, T, price_volatility) * -self.future_dv01

 

    def speed_y(self, F, K, T, price_volatility):

        return self.speed_F(F, K, T, price_volatility) * ((-self.future_dv01) ** 3)

 

    def color_y(self, F, K, T, price_volatility):

        return self.color_F(F, K, T, price_volatility) * ((-self.future_dv01) ** 2)

 

    def volga_y(self, F, K, T, price_volatility):

        return self.volga_price(F, K, T, price_volatility) * (self.future_dv01 ** 2)

 

    # --- Adjusted Greeks ---

 

    def delta_F_adjusted(self, F, K, T, price_volatility, option_type='call'):

        dv01_adjustment = 1 + self.future_dv01 * self.yield_level * 0.1

        return self.delta_F(F, K, T, price_volatility, option_type) * dv01_adjustment

 

    def gamma_F_adjusted(self, F, K, T, price_volatility):

        yield_volatility = self.convert_price_to_yield_volatility(price_volatility)

        convexity_adjustment = 1 + self.future_convexity * (yield_volatility / 10000) ** 2

        return self.gamma_F(F, K, T, price_volatility) * convexity_adjustment

 

    def delta_y_adjusted(self, F, K, T, price_volatility, option_type='call'):

        return self.delta_F_adjusted(F, K, T, price_volatility, option_type) * -self.future_dv01

 

    def gamma_y_adjusted(self, F, K, T, price_volatility, option_type='call'):

        gamma_F_adj = self.gamma_F_adjusted(F, K, T, price_volatility)

        delta_F_adj = self.delta_F_adjusted(F, K, T, price_volatility, option_type)

        dF_dy = -self.future_dv01

        d2F_dy2 = self.future_convexity

        return gamma_F_adj * (dF_dy**2) + delta_F_adj * d2F_dy2

def solve_bond_future_option(future_dv01=.063, future_convexity=0.002404, yield_level=.05, F=110+25.25/32.0 , K=110+24./32. , T=4.7/252., price=23./64, option_type='put'):

    # Example parameters

   

   

    # Create BondFutureOption instance

    option_model = BondFutureOption(future_dv01, future_convexity, yield_level)

    # Calculate option price

    # Using Bachelier model with price volatility    

    price_volatility = 100.0  # Price volatility

    option_price = option_model.bachelier_future_option_price(F, K, T, price_volatility, option_type)

   

    dx= 1

    while abs(option_price ) > 1e-9:

        option_price = option_model.bachelier_future_option_price(F, K, T, price_volatility, option_type)-price

        if abs(option_price) > 1e-9:

            option_implied_2 = option_model.bachelier_future_option_price(F, K, T, price_volatility+dx, option_type)-price

            price_volatility = price_volatility- option_price * dx / (option_implied_2 - option_price)

        print(f"Current Price Volatility: {price_volatility:.6f}", option_price)

    print(option_model.convert_price_to_yield_volatility(price_volatility))

    print(f"Final Price Volatility: {price_volatility:.6f}")

    print(f"Final Option Price: {option_price:.6f}")    

    for greek in ['delta_F', 'delta_y']:

 

        greek_value = getattr(option_model, greek)(F, K, T, price_volatility, option_type) * 1000 if greek != 'delta_F' else getattr(option_model, greek)(F, K, T, price_volatility, option_type)

        print(f"{greek}: {greek_value:.6f}")    

    for greek in ['gamma_y','vega_y', 'theta_F', 'volga_price', 'vanna_F_price', 'charm_F', 'speed_F', 'color_F']:  

        greek_value = getattr(option_model, greek)(F, K, T, price_volatility) * 1000.

        print(f"{greek}: {greek_value:.6f}")          

 

solve_bond_future_option()      