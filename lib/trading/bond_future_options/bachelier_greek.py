#!/usr/bin/env python
# coding: utf-8


import numpy as np
import pandas as pd
from scipy.stats import norm
import plotly.express as px
import matplotlib.pyplot as plt

# Bachelier option price
def bachelier_price(F, K, sigma, tau):
    d = (F - K) / (sigma * np.sqrt(tau))
    return (F - K) * norm.cdf(d) + sigma * np.sqrt(tau) * norm.pdf(d)

# Analytical Greeks
def analytical_greeks(F, K, sigma, tau):
    try:
        if sigma==0:
            moneyness = (F - K) 
            if moneyness > 0:
                phi = 0
                Phi = 1
            elif moneyness < 0:
                phi = 0
                Phi = 0

            delta = Phi
            gamma = 0
            theta = 0
            vega = 0
            rho = 0
            vanna = 0
            charm = 0
            vomma = 0
            veta = 0
            speed = 0
            zomma = 0
            color = 0
            ultima = 0
            return dict(
                delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho,
                vanna=vanna, charm=charm, vomma=vomma, volga=vomma, veta=veta,
                speed=speed, zomma=zomma, color=color, ultima=ultima
            )
        else:
            d = (F - K) / (sigma * np.sqrt(tau))
            phi = norm.pdf(d)
            Phi = norm.cdf(d)
            sqrtT = np.sqrt(tau)
            
            # First-order Greeks
            delta = Phi
            gamma = phi / (sigma * sqrtT)
            theta = -phi * sigma / (2 * sqrtT)
            vega = sqrtT * phi
            rho = 0
            
            # Second-order Greeks
            vanna = -phi * d / sigma
            charm = -phi * d / (2 * tau)
            vomma = phi * d * d * sqrtT / sigma  # Also called volga
            #veta = -phi * (1 + d * d) / (2 * sqrtT)  # Yaman: There should be no negative sign.
            veta = phi * (1 + d * d) / (2 * sqrtT)
            theta_dot = phi*sigma*(d*d -1)/(4*tau*sqrtT)
            #Third-order Greeks (moved here from separate function for consistency)
            #Speed = -phi * d * (d * d - 1) / (sigma**2 * tau) # Yaman: This is not correct
            speed = -phi * d / (sigma**2 * tau)

            # Yaman: Haven't checked these ones.
            zomma = phi * d * (d * d - 3) / (sigma * tau)
            color = phi * (d**3 - 3 * d) / (2 * tau * sigma * sqrtT)
            ultima = phi * d * (d**4 - 10 * d * d + 15) / (sigma**3 * tau * sqrtT)
            
            # Note: vomma is another name for volga
            return dict(
                delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho,
                vanna=vanna, charm=charm, vomma=vomma, volga=vomma, veta=veta,
                speed=speed, zomma=zomma, color=color, ultima=ultima, theta_dot=theta_dot
            )
    except:
        return dict.fromkeys(["delta", "gamma", "theta", "vega", "rho", 
                             "vanna", "charm", "vomma", "volga", "veta",
                             "speed", "zomma", "color", "ultima", "theta_dot"], 0)


# Analytical Greeks
def analytical_greeks_put(F, K, sigma, tau):
    try:
        if sigma==0:
            moneyness = (K - F) 
            if moneyness > 0:
                phi = 0
                Phi = 1
            elif moneyness < 0:
                phi = 0
                Phi = 0

            delta = -Phi
            gamma = 0
            theta = 0
            vega = 0
            rho = 0
            vanna = 0
            charm = 0
            vomma = 0
            veta = 0
            speed = 0
            zomma = 0
            color = 0
            ultima = 0
            return dict(
                delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho,
                vanna=vanna, charm=charm, vomma=vomma, volga=vomma, veta=veta,
                speed=speed, zomma=zomma, color=color, ultima=ultima
            )
        else:
            d = (K - F) / (sigma * np.sqrt(tau))
            phi = norm.pdf(d)
            Phi = norm.cdf(d)
            sqrtT = np.sqrt(tau)
            
            # First-order Greeks
            delta = -Phi
            gamma = phi / (sigma * sqrtT)
            theta = -phi * sigma / (2 * sqrtT)
            vega = sqrtT * phi
            rho = 0
            
            # Second-order Greeks
            vanna = phi * d / sigma
            charm = phi * d / (2 * tau)
            vomma = phi * d * d * sqrtT / sigma  # Also called volga
            #veta = -phi * (1 + d * d) / (2 * sqrtT)  # Yaman: There should be no negative sign.
            veta = phi * (1 + d * d) / (2 * sqrtT)
            theta_dot = phi*sigma*(d*d -1)/(4*tau*sqrtT)
            #Third-order Greeks (moved here from separate function for consistency)
            #Speed = -phi * d * (d * d - 1) / (sigma**2 * tau) # Yaman: This is not correct
            speed = phi * d / (sigma**2 * tau)

            # Yaman: Haven't checked these ones.
            zomma = phi * d * (d * d - 3) / (sigma * tau)
            color = phi * (d**3 - 3 * d) / (2 * tau * sigma * sqrtT)
            ultima = phi * d * (d**4 - 10 * d * d + 15) / (sigma**3 * tau * sqrtT)
            
            # Note: vomma is another name for volga
            return dict(
                delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho,
                vanna=vanna, charm=charm, vomma=vomma, volga=vomma, veta=veta,
                speed=speed, zomma=zomma, color=color, ultima=ultima, theta_dot=theta_dot
            )
    except:
        return dict.fromkeys(["delta", "gamma", "theta", "vega", "rho", 
                             "vanna", "charm", "vomma", "volga", "veta",
                             "speed", "zomma", "color", "ultima", "theta_dot"], 0)


# Numerical Greeks
def numerical_greeks(F, K, sigma, tau, eps=1e-4):
    P = lambda FF, SS, TT: bachelier_price(FF, K, SS, TT)
    base = P(F, sigma, tau)
    
    try:
        # First- and second-order
        delta = (P(F+eps, sigma, tau) - P(F-eps, sigma, tau)) / (2*eps)
        gamma = (P(F+eps, sigma, tau) - 2*base + P(F-eps, sigma, tau)) / eps**2
        theta = (P(F, sigma, tau+eps) - P(F, sigma, tau-eps)) / (2*eps)
        vega = (P(F, sigma+eps, tau) - P(F, sigma-eps, tau)) / (2*eps)
        vomma = (P(F, sigma+eps, tau) - 2*base + P(F, sigma-eps, tau)) / eps**2
        
        # Cross-derivative Greeks
        vanna = (
            P(F+eps, sigma+eps, tau) - P(F+eps, sigma-eps, tau)
            - P(F-eps, sigma+eps, tau) + P(F-eps, sigma-eps, tau)
        ) / (4*eps**2)
        charm = (
            P(F+eps, sigma, tau+eps) - P(F+eps, sigma, tau-eps)
            - P(F-eps, sigma, tau+eps) + P(F-eps, sigma, tau-eps)
        ) / (4*eps**2)
        veta = (
            P(F, sigma+eps, tau+eps) - P(F, sigma+eps, tau-eps)
            - P(F, sigma-eps, tau+eps) + P(F, sigma-eps, tau-eps)
        ) / (4*eps**2)
        
        # Third-order Greeks
        speed = (P(F+2*eps, sigma, tau) - 3*P(F+eps, sigma, tau) + 3*P(F-eps, sigma, tau) - P(F-2*eps, sigma, tau)) / (eps**3)
        zomma = (
            P(F+eps, sigma+eps, tau) - P(F+eps, sigma-eps, tau)
            - P(F-eps, sigma+eps, tau) + P(F-eps, sigma-eps, tau)
        ) / (4*eps**2)  # approx ∂Γ/∂σ
        color = (
            P(F+eps, sigma, tau+eps) - 2*P(F, sigma, tau+eps) + P(F-eps, sigma, tau+eps)
            - (P(F+eps, sigma, tau-eps) - 2*P(F, sigma, tau-eps) + P(F-eps, sigma, tau-eps))
        ) / (2*eps**3)
        ultima = (
            P(F, sigma+2*eps, tau) - 3*P(F, sigma+eps, tau)
            + 3*P(F, sigma-eps, tau) - P(F, sigma-2*eps, tau)
        ) / (eps**3)
        
        return dict(
            delta=delta, gamma=gamma, theta=theta, vega=vega, rho=0,
            vanna=vanna, charm=charm, vomma=vomma, volga=vomma, veta=veta,
            speed=speed, zomma=zomma, color=color, ultima=ultima
        )
    except:
        return dict.fromkeys(["delta", "gamma", "theta", "vega", "rho",
                             "vanna", "charm", "vomma", "volga", "veta",
                             "speed", "zomma", "color", "ultima"], 0)

# Third-order Greeks (kept for backward compatibility)
def third_order_greeks(F, K, sigma, tau):
    """
    Calculate third-order Greeks - now handled in analytical_greeks()
    Kept for backward compatibility
    """
    greeks = analytical_greeks(F, K, sigma, tau)
    return dict(ultima=greeks['ultima'], zomma=greeks['zomma'])

# Cross effects (kept for backward compatibility)
def cross_effects(F, K, sigma, tau, h=1e-4):
    """
    Calculate cross-Greeks - now handled in analytical_greeks()
    Kept for backward compatibility
    """
    greeks = analytical_greeks(F, K, sigma, tau)
    return dict(vanna=greeks['vanna'], charm=greeks['charm'], veta=greeks['veta'])

# Numerical third-order Greeks (kept for backward compatibility)
def numerical_third_order_greeks(F, K, sigma, tau, h=1e-4):
    """
    Calculate third-order Greeks numerically - now handled in numerical_greeks()
    Kept for backward compatibility
    """
    greeks = numerical_greeks(F, K, sigma, tau, eps=h)
    return dict(ultima=greeks['ultima'], zomma=greeks['zomma'])

# Taylor expansion with optional cross effects
def taylor_expand(g, dF, dSigma, dTau, cross=None):
    result = (
        g["delta"] * dF +
        g["vega"] * dSigma +
        g["theta"] * dTau +
        0.5 * (g["gamma"] * dF**2 + g["volga"] * dSigma**2 + g["color"] * dTau**2) +
        (1/6) * g["speed"] * dF**3
    )
    if cross:
        result += cross["vanna"] * dF * dSigma + cross["charm"] * dF * dTau + cross["veta"] * dSigma * dTau
    return result


# Data Generation Functions (no plotting)

def generate_taylor_summary_data(F0=112.0, K=112.0, sigma0=0.75, tau=0.25, 
                                 dF=0.1, dSigma=0.01, dTau=0.01,
                                 F_range=0.25, sigma_range=0.1, grid_size=5):
    """
    Generate data for Taylor approximation summary analysis
    
    Returns:
        pd.DataFrame with Taylor approximation comparisons
    """
    # Grid of F and Sigma values
    F_vals = np.linspace(F0 - F_range, F0 + F_range, grid_size)
    sigma_vals = np.linspace(sigma0 - sigma_range, sigma0 + sigma_range, grid_size)
    
    # Generate summary table
    records = []
    for F in F_vals:
        for sigma in sigma_vals:
            C0 = bachelier_price(F, K, sigma, tau)
            C1 = bachelier_price(F + dF, K, sigma + dSigma, tau + dTau)
            model_change = C1 - C0

            g_ana = analytical_greeks(F, K, sigma, tau)
            g_num = numerical_greeks(F, K, sigma, tau)
            cross = cross_effects(F, K, sigma, tau)

            taylor_ana = taylor_expand(g_ana, dF, dSigma, dTau)
            taylor_num = taylor_expand(g_num, dF, dSigma, dTau, cross)
            taylor_ana_cross = taylor_expand(g_ana, dF, dSigma, dTau, cross)

            records.append({
                "F": F,
                "Sigma": sigma,
                "Model Change": model_change,
                "Taylor (Analytical)": taylor_ana,
                "Taylor (Numerical + Cross)": taylor_num,
                "Taylor (Analytical + Cross)": taylor_ana_cross,
                "Error (Analytical)": abs(model_change - taylor_ana),
                "Error (Numerical + Cross)": abs(model_change - taylor_num),
                "Error (Analytical + Cross)": abs(model_change - taylor_ana_cross)
            })
    
    return pd.DataFrame(records)


def generate_greek_profiles_data(K=112, sigma=0.75, tau=0.25, F_range=(110, 114), num_points=100):
    """
    Generate Greek profiles data for analytical vs numerical comparison
    
    Returns:
        dict with F_vals and greeks_ana/greeks_num dictionaries
    """
    F_vals = np.linspace(F_range[0], F_range[1], num_points)
    
    # Storage - include all Greeks
    greeks_ana = {key: [] for key in ["delta", "vega", "theta", "gamma", "volga", "color", "speed", "ultima", "zomma", "vanna", "charm", "veta"]}
    greeks_num = {key: [] for key in greeks_ana}
    
    # Compute
    for F in F_vals:
        # Get all Greeks from unified functions
        g_ana = analytical_greeks(F, K, sigma, tau)
        g_num = numerical_greeks(F, K, sigma, tau)
        
        # Store all Greeks
        for key in ["delta", "gamma", "vega", "theta", "vanna", "charm", "veta", "speed", "zomma", "color", "ultima"]:
            greeks_ana[key].append(g_ana.get(key, 0))
            greeks_num[key].append(g_num.get(key, 0))
        
        # Map volga (another name for vomma)
        greeks_ana["volga"].append(g_ana.get("vomma", 0))
        greeks_num["volga"].append(g_num.get("vomma", 0))
    
    return {
        'F_vals': F_vals,
        'greeks_ana': greeks_ana,
        'greeks_num': greeks_num,
        'K': K,
        'sigma': sigma,
        'tau': tau
    }


def generate_taylor_error_data(K=112, sigma=0.75, tau=0.25, 
                              dF=0.1, dSigma=0.01, dTau=0.01,
                              F_range=(110, 114), num_points=200):
    """
    Generate Taylor approximation error data across F values
    
    Returns:
        dict with F_vals, model_changes, option_prices, and error arrays
    """
    F_vals = np.linspace(F_range[0], F_range[1], num_points)
    
    # Storage
    model_changes = []
    option_prices = []  # Add storage for option prices
    errors_ana = []
    errors_ana_cross = []
    errors_num_cross = []
    
    # Compute Errors Across F
    for F in F_vals:
        C0 = bachelier_price(F, K, sigma, tau)
        C1 = bachelier_price(F + dF, K, sigma + dSigma, tau + dTau)
        model_change = C1 - C0
        model_changes.append(model_change)
        option_prices.append(C0)  # Store the option price at current F

        g_ana = analytical_greeks(F, K, sigma, tau)
        g_num = numerical_greeks(F, K, sigma, tau)
        cross = cross_effects(F, K, sigma, tau)

        taylor_ana = taylor_expand(g_ana, dF, dSigma, dTau)
        taylor_ana_cross = taylor_expand(g_ana, dF, dSigma, dTau, cross)
        taylor_num_cross = taylor_expand(g_num, dF, dSigma, dTau, cross)

        errors_ana.append(abs(model_change - taylor_ana))
        errors_ana_cross.append(abs(model_change - taylor_ana_cross))
        errors_num_cross.append(abs(model_change - taylor_num_cross))
    
    return {
        'F_vals': F_vals,
        'model_changes': model_changes,
        'option_prices': option_prices,  # Include option prices in returned data
        'errors_ana': errors_ana,
        'errors_ana_cross': errors_ana_cross,
        'errors_num_cross': errors_num_cross,
        'K': K,
        'sigma': sigma,
        'tau': tau,
        'dF': dF,
        'dSigma': dSigma,
        'dTau': dTau
    }


# Optional: Example visualization functions (for reference only)
def plot_greek_profiles(profile_data):
    """Example function showing how to plot Greek profiles using matplotlib"""
    fig, axs = plt.subplots(4, 2, figsize=(14, 12))
    axs = axs.flatten()
    
    F_vals = profile_data['F_vals']
    greeks_ana = profile_data['greeks_ana']
    greeks_num = profile_data['greeks_num']
    
    for i, key in enumerate(greeks_ana.keys()):
        axs[i].plot(F_vals, greeks_ana[key], label='Analytical', color='blue', linewidth=2)
        axs[i].plot(F_vals, greeks_num[key], label='Numerical', color='red', linestyle='--')
        axs[i].set_title(f'{key.capitalize()} vs Forward Price (F)')
        axs[i].legend()
        axs[i].grid(True)
    
    axs[-1].axis('off')  # Hide unused subplot
    plt.suptitle("Comparison of Analytical vs Numerical Greeks", fontsize=16)
    plt.tight_layout()
    return fig


def plot_taylor_errors(error_data):
    """Example function showing how to plot Taylor approximation errors"""
    plt.figure(figsize=(12, 6))
    F_vals = error_data['F_vals']
    
    plt.plot(F_vals, error_data['errors_ana'], label="Analytical", color="blue", linewidth=2)
    plt.plot(F_vals, error_data['errors_ana_cross'], label="Analytical + Cross", color="green", linewidth=2)
    plt.plot(F_vals, error_data['errors_num_cross'], label="Numerical + Cross", color="red", linewidth=2)
    
    plt.title("Taylor Approximation Errors vs Forward Price (F)", fontsize=14)
    plt.xlabel("Forward Price (F)")
    plt.ylabel("Absolute Error")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    return plt.gcf()


# Remove the direct execution code that was at module level
if __name__ == "__main__":
    # Module can now be imported without side effects
    # Users can call the data generation functions as needed
    pass




