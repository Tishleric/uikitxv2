import numpy as np

 

def compute_derivatives(f, S, sigma, t, h_S=None, h_sigma=None, h_t=None):

    """

    Compute 1st, 2nd, and 3rd derivatives using finite differences with optimal step sizes

   

    Parameters:

    f: function that takes (S, sigma, t) as arguments

    S, sigma, t: point at which to evaluate derivatives

    h_S: step size for S perturbations (default: adaptive based on S)

    h_sigma: step size for sigma perturbations (default: adaptive based on sigma)

    h_t: step size for t perturbations (default: adaptive based on t)

   

    Returns:

    Dictionary containing all derivatives

    """

   

    # Adaptive step sizes based on parameter magnitude and type

    if h_S is None:

        h_S = max(0.01, S * 1e-4)  # 0.01 absolute minimum, or 0.01% of S

    if h_sigma is None:

        h_sigma = max(0.001, sigma * 1e-3)  # 0.001 absolute minimum, or 0.1% of sigma

    if h_t is None:

        h_t = max(1e-6, t * 1e-4)  # Very small for time, or 0.01% of t

   

    print(f"Using step sizes: h_S={h_S:.6f}, h_sigma={h_sigma:.6f}, h_t={h_t:.8f}")

   

    

    greeks = {}

   

    # First derivatives (The Greeks) - using parameter-specific step sizes

    greeks['delta'] = (f(S+h_S, sigma, t) - f(S-h_S, sigma, t)) / (2*h_S)          # ∂f/∂S

    greeks['vega'] = (f(S, sigma+h_sigma, t) - f(S, sigma-h_sigma, t)) / (2*h_sigma)           # ∂f/∂σ

    greeks['theta'] = (f(S, sigma, t+h_t) - f(S, sigma, t-h_t)) / (2*h_t)          # ∂f/∂t

   

    # Second derivatives

    greeks['gamma'] = (f(S+h_S, sigma, t) - 2*f(S, sigma, t) + f(S-h_S, sigma, t)) / (h_S**2)        # ∂²f/∂S²

    greeks['vomma'] = (f(S, sigma+h_sigma, t) - 2*f(S, sigma, t) + f(S, sigma-h_sigma, t)) / (h_sigma**2)        # ∂²f/∂σ²

    greeks['charm'] = (f(S, sigma, t+h_t) - 2*f(S, sigma, t) + f(S, sigma, t-h_t)) / (h_t**2)        # ∂²f/∂t²

   

    # Second cross derivatives

    greeks['vanna'] = (f(S+h_S, sigma+h_sigma, t) - f(S+h_S, sigma-h_sigma, t) - f(S-h_S, sigma+h_sigma, t) + f(S-h_S, sigma-h_sigma, t)) / (4*h_S*h_sigma)  # ∂²f/∂S∂σ

    greeks['speed'] = (f(S+h_S, sigma, t+h_t) - f(S+h_S, sigma, t-h_t) - f(S-h_S, sigma, t+h_t) + f(S-h_S, sigma, t-h_t)) / (4*h_S*h_t)    # ∂²f/∂S∂t

    greeks['veta'] = (f(S, sigma+h_sigma, t+h_t) - f(S, sigma+h_sigma, t-h_t) - f(S, sigma-h_sigma, t+h_t) + f(S, sigma-h_sigma, t-h_t)) / (4*h_sigma*h_t)     # ∂²f/∂σ∂t

   

    # Third derivatives (higher-order Greeks)

    greeks['speed'] = (f(S+2*h_S, sigma, t) - 2*f(S+h_S, sigma, t) + 2*f(S-h_S, sigma, t) - f(S-2*h_S, sigma, t)) / (2*h_S**3)    # ∂³f/∂S³

    greeks['ultima'] = (f(S, sigma+2*h_sigma, t) - 2*f(S, sigma+h_sigma, t) + 2*f(S, sigma-h_sigma, t) - f(S, sigma-2*h_sigma, t)) / (2*h_sigma**3)  # ∂³f/∂σ³

    greeks['color'] = (f(S, sigma, t+2*h_t) - 2*f(S, sigma, t+h_t) + 2*f(S, sigma, t-h_t) - f(S, sigma, t-2*h_t)) / (2*h_t**3)   # ∂³f/∂t³

   

    # Third cross derivatives (mixed higher-order Greeks)

    # zomma = ∂³f/∂S²∂σ (also called gamma/vega cross)

    vanna_plus = (f(S+h_S+h_S, sigma+h_sigma, t) - f(S+h_S+h_S, sigma-h_sigma, t) - f(S+h_S-h_S, sigma+h_sigma, t) + f(S+h_S-h_S, sigma-h_sigma, t)) / (4*h_S*h_sigma)

    vanna_minus = (f(S-h_S+h_S, sigma+h_sigma, t) - f(S-h_S+h_S, sigma-h_sigma, t) - f(S-h_S-h_S, sigma+h_sigma, t) + f(S-h_S-h_S, sigma-h_sigma, t)) / (4*h_S*h_sigma)

    greeks['zomma'] = (vanna_plus - vanna_minus) / (2*h_S)

   

    # ∂³f/∂S²∂t (gamma/time cross)

    speed_S_plus = (f(S+h_S+h_S, sigma, t+h_t) - f(S+h_S+h_S, sigma, t-h_t) - f(S+h_S-h_S, sigma, t+h_t) + f(S+h_S-h_S, sigma, t-h_t)) / (4*h_S*h_t)

    speed_S_minus = (f(S-h_S+h_S, sigma, t+h_t) - f(S-h_S+h_S, sigma, t-h_t) - f(S-h_S-h_S, sigma, t+h_t) + f(S-h_S-h_S, sigma, t-h_t)) / (4*h_S*h_t)

    greeks['DgammaDtime'] = (speed_S_plus - speed_S_minus) / (2*h_S)

   

    # ∂³f/∂σ²∂S (vomma/delta cross)

    vanna_sigma_plus = (f(S+h_S, sigma+h_sigma+h_sigma, t) - f(S+h_S, sigma+h_sigma-h_sigma, t) - f(S-h_S, sigma+h_sigma+h_sigma, t) + f(S-h_S, sigma+h_sigma-h_sigma, t)) / (4*h_S*h_sigma)

    vanna_sigma_minus = (f(S+h_S, sigma-h_sigma+h_sigma, t) - f(S+h_S, sigma-h_sigma-h_sigma, t) - f(S-h_S, sigma-h_sigma+h_sigma, t) + f(S-h_S, sigma-h_sigma-h_sigma, t)) / (4*h_S*h_sigma)

    greeks['DvommaDelta'] = (vanna_sigma_plus - vanna_sigma_minus) / (2*h_sigma)

   

    # ∂³f/∂σ²∂t (vomma/time cross)

    veta_sigma_plus = (f(S, sigma+h_sigma+h_sigma, t+h_t) - f(S, sigma+h_sigma+h_sigma, t-h_t) - f(S, sigma+h_sigma-h_sigma, t+h_t) + f(S, sigma+h_sigma-h_sigma, t-h_t)) / (4*h_sigma*h_t)

    veta_sigma_minus = (f(S, sigma-h_sigma+h_sigma, t+h_t) - f(S, sigma-h_sigma+h_sigma, t-h_t) - f(S, sigma-h_sigma-h_sigma, t+h_t) + f(S, sigma-h_sigma-h_sigma, t-h_t)) / (4*h_sigma*h_t)

    greeks['DvommaDtime'] = (veta_sigma_plus - veta_sigma_minus) / (2*h_sigma)

   

    # ∂³f/∂t²∂S (charm/delta cross)

    speed_t_plus = (f(S+h_S, sigma, t+h_t+h_t) - f(S+h_S, sigma, t+h_t-h_t) - f(S-h_S, sigma, t+h_t+h_t) + f(S-h_S, sigma, t+h_t-h_t)) / (4*h_S*h_t)

    speed_t_minus = (f(S+h_S, sigma, t-h_t+h_t) - f(S+h_S, sigma, t-h_t-h_t) - f(S-h_S, sigma, t-h_t+h_t) + f(S-h_S, sigma, t-h_t-h_t)) / (4*h_S*h_t)

    greeks['DcharmDdelta'] = (speed_t_plus - speed_t_minus) / (2*h_t)

   

    # ∂³f/∂t²∂σ (charm/vega cross)

    veta_t_plus = (f(S, sigma+h_sigma, t+h_t+h_t) - f(S, sigma+h_sigma, t+h_t-h_t) - f(S, sigma-h_sigma, t+h_t+h_t) + f(S, sigma-h_sigma, t+h_t-h_t)) / (4*h_sigma*h_t)

    veta_t_minus = (f(S, sigma+h_sigma, t-h_t+h_t) - f(S, sigma+h_sigma, t-h_t-h_t) - f(S, sigma-h_sigma, t-h_t+h_t) + f(S, sigma-h_sigma, t-h_t-h_t)) / (4*h_sigma*h_t)

    greeks['DcharmDvega'] = (veta_t_plus - veta_t_minus) / (2*h_t)

   

    # dvanna_dt = ∂³f/∂S∂σ∂t (mixed cross derivative)

    vanna_t_plus = (f(S+h_S, sigma+h_sigma, t+h_t) - f(S+h_S, sigma-h_sigma, t+h_t) - f(S-h_S, sigma+h_sigma, t+h_t) + f(S-h_S, sigma-h_sigma, t+h_t)) / (4*h_S*h_sigma)

    vanna_t_minus = (f(S+h_S, sigma+h_sigma, t-h_t) - f(S+h_S, sigma-h_sigma, t-h_t) - f(S-h_S, sigma+h_sigma, t-h_t) + f(S-h_S, sigma-h_sigma, t-h_t)) / (4*h_S*h_sigma)

    greeks['DvannaDtime'] = (vanna_t_plus - vanna_t_minus) / (2*h_t)

   

    return greeks

 

# Example usage:

import math

 

def bachelier_call(S, sigma, t, K=100, r=0.05):

    """

    Bachelier model for European call option (normal model)

   

    Parameters:

    S: Current asset price

    sigma: Volatility (normal volatility, not lognormal)

    t: Time to expiration

    K: Strike price (default 100)

    r: Risk-free rate (default 5%)

   

    Formula: C = e^(-rt) * [(S-K)*N(d) + sigma*sqrt(t)*phi(d)]

    where d = (S-K)/(sigma*sqrt(t))

    """

    if t <= 0:

        return max(S - K, 0)

   

    # Standard normal CDF and PDF

    def norm_cdf(x):

        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

   

    def norm_pdf(x):

        return math.exp(-0.5 * x**2) / math.sqrt(2 * math.pi)

   

    # Bachelier d parameter

    d = (S - K) / (sigma * math.sqrt(t))

   

    # Bachelier call price

    discount = math.exp(-r * t)

    intrinsic = (S - K) * norm_cdf(d)

    time_value = sigma * math.sqrt(t) * norm_pdf(d)

   

    return discount * (intrinsic + time_value)

 

# Test at point (100, 0.2, 0.25)

point = (100.0, 0.2, 0.25)

greeks = compute_derivatives(example_function, *point)

 

print("Greeks at point (S=100, σ=0.2, t=0.25):")

print("="*50)

print("First-order Greeks:")

print(f"Delta (∂f/∂S) = {greeks['delta']:.6f}")

print(f"Vega (∂f/∂σ) = {greeks['vega']:.6f}")

print(f"Theta (∂f/∂t) = {greeks['theta']:.6f}")

 

print("\nSecond-order Greeks:")

print(f"Gamma (∂²f/∂S²) = {greeks['gamma']:.6f}")

print(f"Vomma (∂²f/∂σ²) = {greeks['vomma']:.6f}")

print(f"Charm (∂²f/∂t²) = {greeks['charm']:.6f}")

print(f"Vanna (∂²f/∂S∂σ) = {greeks['vanna']:.6f}")

print(f"Speed (∂²f/∂S∂t) = {greeks['speed']:.6f}")

print(f"Veta (∂²f/∂σ∂t) = {greeks['veta']:.6f}")

 

print("\nThird-order Greeks:")

print(f"Speed (∂³f/∂S³) = {greeks['speed']:.6f}")

print(f"Ultima (∂³f/∂σ³) = {greeks['ultima']:.6f}")

print(f"Color (∂³f/∂t³) = {greeks['color']:.6f}")

print(f"Zomma (∂³f/∂S²∂σ) = {greeks['zomma']:.6f}")

print(f"∂³f/∂S²∂t = {greeks['DgammaDtime']:.6f}")

print(f"∂³f/∂σ²∂S = {greeks['DvommaDelta']:.6f}")

print(f"∂³f/∂σ²∂t = {greeks['DvommaDtime']:.6f}")

print(f"∂³f/∂t²∂S = {greeks['DcharmDdelta']:.6f}")

print(f"∂³f/∂t²∂σ = {greeks['DcharmDvega']:.6f}")

print(f"∂³f/∂S∂σ∂t = {greeks['DvannaDtime']:.6f}")

 

# Analytical derivatives for comparison

print("\n" + "="*50)

print("Analytical Greeks for comparison:")

print("f(S,σ,t) = S³ + 2S*σ² + t²*S + σ*t")

S, sigma, t = point

print(f"Delta (analytical) = {3*S**2 + 2*sigma**2 + t**2:.6f}")

print(f"Vega (analytical) = {4*S*sigma + t:.6f}")

print(f"Theta (analytical) = {2*t*S + sigma:.6f}")

print(f"Gamma (analytical) = {6*S:.6f}")

print(f"Vomma (analytical) = {4*S:.6f}")

print(f"Charm (analytical) = {2*S:.6f}")

print(f"Vanna (analytical) = {4*sigma:.6f}")

print(f"Speed (analytical) = {2*t:.6f}")

print(f"Veta (analytical) = {1:.6f}")

print(f"Speed (∂³f/∂S³) (analytical) = {6:.6f}")