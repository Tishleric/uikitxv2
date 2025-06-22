"""
Greek-based PnL Prediction Validator for Bond Future Options.

This module tests how well our analytical Greeks predict actual option price changes
for small market moves, focusing on near-ATM scenarios where accuracy matters most.
"""

import numpy as np
from typing import Dict, Tuple, Optional
import matplotlib.pyplot as plt
from scipy import stats

from .pricing_engine import BondFutureOption
from .analysis import calculate_all_greeks


class GreekPnLValidator:
    """Validates Greek-based PnL predictions against actual price changes."""
    
    def __init__(self, option_model: BondFutureOption):
        """
        Initialize validator with a bond future option model.
        
        Args:
            option_model: BondFutureOption instance with DV01/convexity parameters
        """
        self.option_model = option_model
    
    def generate_scenarios(self, F: float, K: float, sigma: float, t: float, 
                         n_samples: int = 200) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate random market scenarios focused on near-ATM moves.
        
        Args:
            F: Current future price
            K: Strike price
            sigma: Current price volatility
            t: Time to expiry (years)
            n_samples: Number of scenarios to generate
            
        Returns:
            Tuple of (F_changes, sigma_changes, t_changes) arrays
        """
        # Set random seed for reproducibility
        np.random.seed(42)
        
        # F perturbations: ±0.5% to ±2% (small moves)
        F_pct_changes = np.random.uniform(-0.02, 0.02, n_samples)
        F_changes = F_pct_changes * F
        
        # Sigma perturbations: ±5% to ±20% (relative changes)
        sigma_pct_changes = np.random.uniform(-0.20, 0.20, n_samples)
        sigma_changes = sigma_pct_changes * sigma
        
        # Time decay: -1 to -5 days (always negative for theta decay)
        t_changes = np.random.uniform(-5/252, -1/252, n_samples)
        
        return F_changes, sigma_changes, t_changes
    
    def calculate_taylor_pnl(self, greeks: Dict[str, float], 
                           dF: np.ndarray, dsigma: np.ndarray, dt: np.ndarray,
                           order: int = 2) -> np.ndarray:
        """
        Calculate predicted PnL using Taylor expansion with Greeks up to specified order.
        
        Args:
            greeks: Dictionary of Greek values at current market point
            dF: Array of future price changes
            dsigma: Array of volatility changes  
            dt: Array of time changes
            order: Taylor expansion order (0, 1, 2, or 3)
            
        Returns:
            Array of predicted PnL values
        """
        # Order 0: Just constant (option value)
        if order == 0:
            return np.zeros_like(dF)
        
        # Order 1: First-order terms
        # Note: check scaling carefully - some Greeks are pre-scaled by 1000 in calculate_all_greeks
        pnl = (
            greeks['delta_F'] * dF +  # NOT scaled
            greeks['vega_price'] * dsigma +  # NOT scaled 
            greeks['theta_F'] * dt  # Already scaled by 1000 and divided by 252
        )
        
        if order >= 2:
            # Order 2: Second-order terms
            pnl += (
                0.5 * greeks['gamma_F'] * dF**2 +  # NOT scaled
                0.5 * greeks['volga_price'] * dsigma**2 / 1000.0 +  # volga IS scaled by 1000
                greeks['vanna_F_price'] * dF * dsigma / 1000.0 +  # vanna IS scaled by 1000
                greeks['charm_F'] * dF * dt / 1000.0  # charm IS scaled by 1000
            )
        
        if order >= 3:
            # Order 3: Third-order terms
            pnl += (
                (1/6) * greeks['speed_F'] * dF**3 / 1000.0 +  # speed IS scaled by 1000
                (1/6) * greeks['ultima'] * dsigma**3 / 1000.0 +  # ultima IS scaled by 1000
                greeks['color_F'] * dF * dt**2 / 1000.0 +  # color IS scaled by 1000
                greeks['zomma'] * dF**2 * dsigma / 1000.0  # zomma IS scaled by 1000
            )
        
        return pnl
    
    def calculate_actual_pnl(self, F: float, K: float, t: float, sigma: float,
                           dF: np.ndarray, dsigma: np.ndarray, dt: np.ndarray,
                           option_type: str = 'put') -> np.ndarray:
        """
        Calculate actual PnL by repricing options at new market conditions.
        
        Args:
            F, K, t, sigma: Current market parameters
            dF, dsigma, dt: Arrays of parameter changes
            option_type: 'call' or 'put'
            
        Returns:
            Array of actual PnL values
        """
        # Current option value
        V0 = self.option_model.bachelier_future_option_price(F, K, t, sigma, option_type)
        
        # New option values
        actual_pnl = np.zeros(len(dF))
        for i in range(len(dF)):
            F_new = F + dF[i]
            sigma_new = sigma + dsigma[i]
            t_new = max(0, t + dt[i])  # Ensure non-negative time
            
            V_new = self.option_model.bachelier_future_option_price(
                F_new, K, t_new, sigma_new, option_type
            )
            actual_pnl[i] = V_new - V0
        
        return actual_pnl
    
    def analyze_predictions(self, predicted_pnl: np.ndarray, actual_pnl: np.ndarray) -> Dict:
        """
        Calculate statistics comparing predicted vs actual PnL.
        
        Args:
            predicted_pnl: Array of Taylor expansion predictions
            actual_pnl: Array of actual repricing results
            
        Returns:
            Dictionary with R², RMSE, max error, and other statistics
        """
        # R-squared
        slope, intercept, r_value, p_value, std_err = stats.linregress(actual_pnl, predicted_pnl)
        r_squared = r_value**2
        
        # RMSE
        errors = predicted_pnl - actual_pnl
        rmse = np.sqrt(np.mean(errors**2))
        
        # Max absolute error
        max_error = np.max(np.abs(errors))
        
        # Mean absolute error
        mae = np.mean(np.abs(errors))
        
        return {
            'r_squared': r_squared,
            'rmse': rmse,
            'max_error': max_error,
            'mae': mae,
            'slope': slope,
            'intercept': intercept,
            'mean_actual_pnl': np.mean(actual_pnl),
            'std_actual_pnl': np.std(actual_pnl),
            'mean_predicted_pnl': np.mean(predicted_pnl),
            'std_predicted_pnl': np.std(predicted_pnl)
        }
    
    def calculate_greek_contributions(self, greeks: Dict[str, float],
                                    dF: np.ndarray, dsigma: np.ndarray, dt: np.ndarray) -> Dict:
        """
        Calculate average contribution of each Greek to total PnL.
        
        Args:
            greeks: Dictionary of Greek values
            dF, dsigma, dt: Arrays of parameter changes
            
        Returns:
            Dictionary with percentage contribution of each Greek
        """
        # Calculate individual Greek contributions (with correct scaling)
        delta_contrib = np.abs(greeks['delta_F'] * dF)
        gamma_contrib = np.abs(0.5 * greeks['gamma_F'] * dF**2)
        vega_contrib = np.abs(greeks['vega_price'] * dsigma)  # vega_price NOT scaled
        theta_contrib = np.abs(greeks['theta_F'] * dt)  # theta_F already scaled
        
        # Total contribution
        total_contrib = delta_contrib + gamma_contrib + vega_contrib + theta_contrib
        
        # Avoid division by zero
        total_contrib = np.where(total_contrib == 0, 1e-10, total_contrib)
        
        # Calculate average percentages
        contributions = {
            'delta': np.mean(delta_contrib / total_contrib) * 100,
            'gamma': np.mean(gamma_contrib / total_contrib) * 100,
            'vega': np.mean(vega_contrib / total_contrib) * 100,
            'theta': np.mean(theta_contrib / total_contrib) * 100
        }
        
        return contributions
    
    def create_scatter_plot(self, actual_pnl: np.ndarray, predicted_pnl: np.ndarray,
                          title: str = "Greek PnL Prediction vs Actual") -> plt.Figure:
        """
        Create scatter plot comparing predicted vs actual PnL.
        
        Args:
            actual_pnl: Array of actual PnL values
            predicted_pnl: Array of predicted PnL values
            title: Plot title
            
        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # Scatter plot
        ax.scatter(actual_pnl, predicted_pnl, alpha=0.5, s=20)
        
        # Perfect prediction line
        min_val = min(np.min(actual_pnl), np.min(predicted_pnl))
        max_val = max(np.max(actual_pnl), np.max(predicted_pnl))
        ax.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect Prediction')
        
        # Linear regression line
        slope, intercept, r_value, _, _ = stats.linregress(actual_pnl, predicted_pnl)
        x_fit = np.linspace(min_val, max_val, 100)
        y_fit = slope * x_fit + intercept
        ax.plot(x_fit, y_fit, 'g-', 
                label=f'Fit: y = {slope:.3f}x + {intercept:.3e}, R² = {r_value**2:.3f}')
        
        ax.set_xlabel('Actual PnL')
        ax.set_ylabel('Predicted PnL (Taylor)')
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Equal aspect ratio
        ax.set_aspect('equal', adjustable='box')
        
        return fig
    
    def run_validation(self, F: float, K: float, t: float, sigma: float,
                      option_type: str = 'put', n_samples: int = 200) -> Dict:
        """
        Run complete validation analysis.
        
        Args:
            F: Current future price
            K: Strike price
            t: Time to expiry (years)
            sigma: Current price volatility
            option_type: 'call' or 'put'
            n_samples: Number of scenarios
            
        Returns:
            Dictionary with all results and statistics
        """
        # Generate scenarios
        dF, dsigma, dt = self.generate_scenarios(F, K, sigma, t, n_samples)
        
        # Calculate Greeks at current market point
        greeks = calculate_all_greeks(self.option_model, F, K, t, sigma, option_type)
        
        # Calculate actual PnL
        actual_pnl = self.calculate_actual_pnl(F, K, t, sigma, dF, dsigma, dt, option_type)
        
        # Calculate predicted PnL for different Taylor orders
        predicted_pnl = {}
        stats_by_order = {}
        
        for order in [0, 1, 2, 3]:
            predicted_pnl[order] = self.calculate_taylor_pnl(greeks, dF, dsigma, dt, order=order)
            stats_by_order[order] = self.analyze_predictions(predicted_pnl[order], actual_pnl)
        
        # Calculate Greek contributions
        contributions = self.calculate_greek_contributions(greeks, dF, dsigma, dt)
        
        # Create scatter plots for key orders
        figures = {}
        figures['order_1'] = self.create_scatter_plot(
            actual_pnl, predicted_pnl[1], 
            "First-Order Taylor (Δ, V, Θ)"
        )
        figures['order_2'] = self.create_scatter_plot(
            actual_pnl, predicted_pnl[2],
            "Second-Order Taylor (+Γ, Volga, Vanna, Charm)"
        )
        figures['order_3'] = self.create_scatter_plot(
            actual_pnl, predicted_pnl[3],
            "Third-Order Taylor (+Speed, Color, Ultima, Zomma)"
        )
        
        return {
            'scenarios': {
                'n_samples': n_samples,
                'F_range_pct': (np.min(dF/F)*100, np.max(dF/F)*100),
                'sigma_range_pct': (np.min(dsigma/sigma)*100, np.max(dsigma/sigma)*100),
                'time_range_days': (np.min(dt)*252, np.max(dt)*252)
            },
            'greeks': greeks,
            'stats_by_order': stats_by_order,
            'contributions': contributions,
            'figures': figures,
            'data': {
                'actual_pnl': actual_pnl,
                'predicted_pnl': predicted_pnl,
                'dF': dF,
                'dsigma': dsigma,
                'dt': dt
            }
        } 