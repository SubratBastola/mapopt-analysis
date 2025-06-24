"""
Signal processing module for correlation calculations and transforms
"""

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from typing import Tuple, List

from ..config import (
    COX_WINDOWS_MIN, MIN_DATA_POINTS, FISHER_BOUNDS,
    MIN_CORRELATION_POINTS
)


class SignalProcessor:
    """Handles signal processing operations for biomedical data"""
    
    @staticmethod
    def calculate_cox_correlations(data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate COx correlation values using sliding windows
        
        Args:
            data: DataFrame with columns [time, MAP, rSO2]
            
        Returns:
            Tuple of (cox_time, cox_values) arrays
        """
        cox_windows_min = [w for w in COX_WINDOWS_MIN if w <= 30]  # Use shorter windows for COx
        all_corr_time = []
        all_corr_val = []
        
        t = data['time'].values
        MAP = data['MAP'].values
        rSO2 = data['rSO2'].values
        
        for w in cox_windows_min:
            win_hr = w / 60
            if win_hr > 0.5:  # Skip windows longer than 30 minutes
                continue
                
            step_size = win_hr / 2
            num_steps = int((t[-1] - t[0] - win_hr) / step_size) + 1
            
            for s in range(num_steps):
                win_start = t[0] + s * step_size
                win_end = win_start + win_hr
                
                idx = (t >= win_start) & (t < win_end)
                if np.sum(idx) < MIN_DATA_POINTS:
                    continue
                    
                map_seg = MAP[idx]
                rso2_seg = rSO2[idx]
                
                if len(map_seg) > 1:
                    corr = SignalProcessor.fast_correlation(map_seg, rso2_seg)
                    if not np.isnan(corr):
                        all_corr_time.append((win_start + win_end) / 2)
                        all_corr_val.append(corr)
        
        if all_corr_time:
            # Average correlations at same time points
            corr_df = pd.DataFrame({'time': all_corr_time, 'cox': all_corr_val})
            corr_df = corr_df.groupby('time')['cox'].mean().reset_index()
            return corr_df['time'].values, corr_df['cox'].values
        else:
            return np.array([]), np.array([])
            
    @staticmethod
    def fast_correlation(x: np.ndarray, y: np.ndarray) -> float:
        """
        Fast correlation calculation matching MATLAB's corr function
        
        Args:
            x, y: Input arrays
            
        Returns:
            Correlation coefficient or NaN if calculation fails
        """
        if len(x) < MIN_CORRELATION_POINTS or len(y) < MIN_CORRELATION_POINTS:
            return np.nan
            
        try:
            # Remove NaN values (like MATLAB's 'rows','complete')
            mask = np.isfinite(x) & np.isfinite(y)
            if np.sum(mask) < MIN_CORRELATION_POINTS:
                return np.nan
            
            x_clean = x[mask]
            y_clean = y[mask]
            
            # Calculate correlation
            return np.corrcoef(x_clean, y_clean)[0, 1]
                
        except:
            return np.nan
            
    @staticmethod
    def fisher_transform(r: np.ndarray) -> np.ndarray:
        """
        Apply Fisher's Z transformation
        
        Args:
            r: Correlation coefficients
            
        Returns:
            Fisher-transformed values
        """
        r_clipped = np.clip(r, -FISHER_BOUNDS, FISHER_BOUNDS)
        return 0.5 * np.log((1 + r_clipped) / (1 - r_clipped))
        
    @staticmethod
    def inverse_fisher_transform(z: np.ndarray) -> np.ndarray:
        """
        Apply inverse Fisher transformation
        
        Args:
            z: Fisher-transformed values
            
        Returns:
            Original correlation scale values
        """
        return np.tanh(z)
        
    @staticmethod
    def calculate_sliding_window_correlations(
        time: np.ndarray, 
        MAP: np.ndarray, 
        rSO2: np.ndarray,
        win_hr: float,
        hist_hr: float,
        t_now: float
    ) -> Tuple[List[float], List[float]]:
        """
        Calculate correlations in sliding windows within a history period
        
        Args:
            time: Time vector
            MAP: MAP values
            rSO2: rSO2 values
            win_hr: Window size in hours
            hist_hr: History period in hours
            t_now: Current time point
            
        Returns:
            Tuple of (cox_values, map_values) lists
        """
        t_start = t_now - hist_hr
        
        # Get data segment
        idx = (time >= t_start) & (time < t_now)
        if np.sum(idx) < 60:  # Need minimum data points
            return [], []
            
        time_seg = time[idx]
        map_seg = MAP[idx]
        rso2_seg = rSO2[idx]
        
        cox_vals = []
        map_vals = []
        
        # Sliding window analysis
        step_size = win_hr / 2
        num_steps = int((hist_hr - win_hr) / step_size) + 1
        
        for s in range(num_steps):
            win_start = t_now - hist_hr + s * step_size
            win_end = win_start + win_hr
            
            win_idx = (time_seg >= win_start) & (time_seg < win_end)
            if np.sum(win_idx) < MIN_DATA_POINTS:
                continue
                
            map_win = map_seg[win_idx]
            rso2_win = rso2_seg[win_idx]
            
            if len(map_win) > 1:
                corr = SignalProcessor.fast_correlation(map_win, rso2_win)
                if not np.isnan(corr):
                    cox_vals.append(corr)
                    map_vals.append(np.mean(map_win))
                    
        return cox_vals, map_vals
        
    @staticmethod
    def bin_correlations(
        cox_vals: List[float], 
        map_vals: List[float], 
        bins: np.ndarray
    ) -> np.ndarray:
        """
        Bin correlation values by MAP ranges
        
        Args:
            cox_vals: Correlation values
            map_vals: Corresponding MAP values
            bins: MAP bin edges
            
        Returns:
            Binned correlation values
        """
        if len(cox_vals) < 5:
            return np.full(len(bins) - 1, np.nan)
            
        cox_vals = np.array(cox_vals)
        map_vals = np.array(map_vals)
        bin_centers = bins[:-1] + np.diff(bins) / 2
        
        binned_cox = np.full(len(bin_centers), np.nan)
        
        for b in range(len(bin_centers)):
            bin_mask = (map_vals >= bins[b]) & (map_vals < bins[b+1])
            if np.any(bin_mask):
                binned_cox[b] = np.mean(cox_vals[bin_mask])
                
        return binned_cox 
