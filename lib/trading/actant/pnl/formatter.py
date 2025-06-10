"""
Data Formatter Module for PnL Display

This module formats PnL calculation results for display in tables and charts,
matching the structure from the Excel workbook.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from .calculations import OptionGreeks, PnLCalculator, TaylorSeriesPricer


class PnLDataFormatter:
    """Format PnL data for display in Dash components."""
    
    @staticmethod
    def create_excel_style_dataframe(greeks: OptionGreeks, option_type: str = 'call') -> pd.DataFrame:
        """
        Create a DataFrame matching the Excel layout structure.
        
        Args:
            greeks: OptionGreeks object
            option_type: 'call' or 'put'
            
        Returns:
            DataFrame with rows matching Excel structure
        """
        # Calculate all prices
        if option_type.lower() == 'call':
            actant_prices = greeks.call_prices
        else:
            actant_prices = greeks.put_prices
            
        ts0_prices = TaylorSeriesPricer.from_atm(greeks, option_type)
        ts_neighbor_prices = TaylorSeriesPricer.from_neighbor(greeks, option_type)
        
        # Calculate PnLs
        atm_idx = greeks.atm_index
        actant_pnl = PnLCalculator.calculate_pnl(actant_prices, atm_idx)
        ts0_pnl = PnLCalculator.calculate_pnl(ts0_prices, atm_idx)
        ts_neighbor_pnl = PnLCalculator.calculate_pnl(ts_neighbor_prices, atm_idx)
        
        # Calculate differences
        ts0_diff = ts0_prices - actant_prices
        ts_neighbor_diff = ts_neighbor_prices - actant_prices
        
        # Create shock values in Excel format (0.25 increments)
        shock_values = greeks.shocks / 16  # Convert from bp to Excel format
        
        # Build DataFrame with rows as in Excel
        rows = []
        
        # Shock values row
        rows.append(['shift in bp'] + list(greeks.shocks))
        
        # Price rows
        rows.append([f'{option_type.title()} Price ACTANT'] + list(actant_prices))
        rows.append(['TS Predicted from 0'] + list(ts0_prices))
        rows.append(['TS Predicted from n-0.25'] + list(ts_neighbor_prices))
        
        # Difference rows
        rows.append([f'{option_type.title()} TS0vA Diff'] + list(ts0_diff))
        rows.append([f'{option_type.title()} TS-0.25vA Diff'] + list(ts_neighbor_diff))
        
        # Blank row (as in Excel)
        rows.append([''] * (len(greeks.shocks) + 1))
        
        # Repeat shock values
        rows.append(['shift in bp'] + list(greeks.shocks))
        
        # PnL rows
        rows.append(['ACTANT PNL'] + list(actant_pnl))
        rows.append(['TS0 PNL (cumlv)'] + list(ts0_pnl))
        rows.append(['TS-0.25 PNL (cumlv)'] + list(ts_neighbor_pnl))
        
        # PnL difference rows
        rows.append(['0DIFF'] + list(ts0_pnl - actant_pnl))
        rows.append(['-0.25DIFF'] + list(ts_neighbor_pnl - actant_pnl))
        
        # Create column headers (shock values in Excel format)
        columns = ['Metric'] + [f"{val:.2f}" for val in shock_values]
        
        # Create DataFrame
        df = pd.DataFrame(rows, columns=columns)
        
        return df
    
    @staticmethod
    def create_summary_table(greeks: OptionGreeks, 
                           call_pnl_df: pd.DataFrame,
                           put_pnl_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create a summary table with key metrics.
        
        Args:
            greeks: OptionGreeks object
            call_pnl_df: PnL DataFrame for calls
            put_pnl_df: PnL DataFrame for puts
            
        Returns:
            Summary DataFrame
        """
        summary_data = {
            'Metric': [
                'Underlying Price',
                'Strike',
                'Forward',
                'Time to Expiry (years)',
                'ATM Call Price',
                'ATM Put Price',
                'Call PnL Range (Actant)',
                'Put PnL Range (Actant)',
                'Max Call TS0 Error',
                'Max Put TS0 Error',
                'Max Call TS-0.25 Error',
                'Max Put TS-0.25 Error'
            ],
            'Value': [
                f"${greeks.underlying_price:.3f}",
                f"${greeks.strike:.3f}",
                f"${greeks.forward:.3f}",
                f"{greeks.time_to_expiry:.3f}",
                f"${greeks.call_prices[greeks.atm_index]:.2f}",
                f"${greeks.put_prices[greeks.atm_index]:.2f}",
                f"[{call_pnl_df['actant_pnl'].min():.2f}, {call_pnl_df['actant_pnl'].max():.2f}]",
                f"[{put_pnl_df['actant_pnl'].min():.2f}, {put_pnl_df['actant_pnl'].max():.2f}]",
                f"{abs(call_pnl_df['ts0_diff']).max():.2f}",
                f"{abs(put_pnl_df['ts0_diff']).max():.2f}",
                f"{abs(call_pnl_df['ts_neighbor_diff']).max():.2f}",
                f"{abs(put_pnl_df['ts_neighbor_diff']).max():.2f}"
            ]
        }
        
        return pd.DataFrame(summary_data)
    
    @staticmethod
    def prepare_graph_data(pnl_df: pd.DataFrame, 
                          option_type: str = 'call') -> Dict[str, pd.DataFrame]:
        """
        Prepare data for graphing PnL comparisons.
        
        Args:
            pnl_df: PnL DataFrame from PnLCalculator
            option_type: 'call' or 'put'
            
        Returns:
            Dictionary of DataFrames ready for plotting
        """
        # PnL comparison data
        pnl_comparison = pd.DataFrame({
            'Shock (bp)': pnl_df['shock_bp'],
            'Actant': pnl_df['actant_pnl'],
            'TS0': pnl_df['ts0_pnl'],
            'TS-0.25': pnl_df['ts_neighbor_pnl']
        })
        
        # Error comparison data
        error_comparison = pd.DataFrame({
            'Shock (bp)': pnl_df['shock_bp'],
            'TS0 vs Actant': pnl_df['ts0_diff'],
            'TS-0.25 vs Actant': pnl_df['ts_neighbor_diff']
        })
        
        # Price comparison data
        price_comparison = pd.DataFrame({
            'Shock (bp)': pnl_df['shock_bp'],
            'Actant': pnl_df['actant_price'],
            'TS0': pnl_df['ts0_price'],
            'TS-0.25': pnl_df['ts_neighbor_price']
        })
        
        return {
            'pnl': pnl_comparison,
            'error': error_comparison,
            'price': price_comparison
        }
    
    @staticmethod
    def format_for_display(value: float, format_type: str = 'currency') -> str:
        """
        Format numeric values for display.
        
        Args:
            value: Numeric value to format
            format_type: 'currency', 'percentage', 'decimal'
            
        Returns:
            Formatted string
        """
        if format_type == 'currency':
            return f"${value:,.2f}"
        elif format_type == 'percentage':
            return f"{value:.2%}"
        elif format_type == 'decimal':
            return f"{value:.4f}"
        else:
            return str(value)
    
    @staticmethod
    def get_display_columns(view_type: str = 'full') -> List[str]:
        """
        Get column configuration for different view types.
        
        Args:
            view_type: 'full', 'prices', 'pnl', 'errors'
            
        Returns:
            List of column names to display
        """
        if view_type == 'prices':
            return ['shift in bp', 'Call Price ACTANT', 'TS Predicted from 0', 
                   'TS Predicted from n-0.25']
        elif view_type == 'pnl':
            return ['shift in bp', 'ACTANT PNL', 'TS0 PNL (cumlv)', 
                   'TS-0.25 PNL (cumlv)']
        elif view_type == 'errors':
            return ['shift in bp', 'Call TS0vA Diff', 'Call TS-0.25vA Diff',
                   '0DIFF', '-0.25DIFF']
        else:
            return None  # Return all columns 