"""
MAPopt calculation module - core algorithm for optimal MAP determination
"""

import numpy as np
import pandas as pd
from scipy import signal
from multiprocessing import Pool, cpu_count
from typing import Tuple, List, Dict, Any

from .signal_processing import SignalProcessor
from ..config import (
    MAP_BINS, MAP_BIN_CENTERS, COX_WINDOWS_MIN, HISTORY_WINDOWS_HR,
    MAP_OPT_MIN, MAP_OPT_MAX, COX_WEIGHT_THRESHOLD, 
    MAX_CORES, CHUNK_SIZE, TIME_STEP_MIN,
    SAVGOL_WINDOW, SAVGOL_ORDER
)


class MAPoptCalculator:
    """Calculates optimal MAP using parallel curve fitting analysis"""
    
    def __init__(self):
        self.time_vector = None
        self.mapopt_series = None
        self.mapopt_filled = None
        self.all_fits_data = None
        
    def calculate_mapopt_series(
        self, 
        data: pd.DataFrame,
        progress_callback=None
    ) -> Tuple[np.ndarray, np.ndarray, List[List[Dict]]]:
        """
        Calculate MAPopt series using parallel processing
        
        Args:
            data: DataFrame with columns [time, MAP, rSO2]
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (time_vector, mapopt_series, all_fits_data)
        """
        t = data['time'].values
        MAP = data['MAP'].values
        rSO2 = data['rSO2'].values
        
        # Create time vector (1-minute intervals)
        self.time_vector = np.arange(t[0], t[-1], TIME_STEP_MIN)
        
        # Prepare arguments for parallel processing
        args_list = self._prepare_processing_args(t, MAP, rSO2)
        
        # Process in parallel
        mapopt_series, all_fits_data = self._process_parallel(
            args_list, progress_callback
        )
        
        # Post-process results
        self.mapopt_series = mapopt_series
        self.mapopt_filled = self._post_process_mapopt(mapopt_series)
        self.all_fits_data = all_fits_data
        
        return self.time_vector, self.mapopt_filled, self.all_fits_data
        
    def _prepare_processing_args(
        self, 
        t: np.ndarray, 
        MAP: np.ndarray, 
        rSO2: np.ndarray
    ) -> List[Tuple]:
        """Prepare arguments for parallel processing"""
        args_list = []
        
        for k, t_now in enumerate(self.time_vector):
            args_list.append((
                k, t_now, t, MAP, rSO2, 
                MAP_BINS, MAP_BIN_CENTERS, 
                COX_WINDOWS_MIN, HISTORY_WINDOWS_HR
            ))
            
        return args_list
        
    def _process_parallel(
        self, 
        args_list: List[Tuple],
        progress_callback=None
    ) -> Tuple[np.ndarray, List[List[Dict]]]:
        """Process MAPopt calculation in parallel"""
        mapopt_series = np.full(len(self.time_vector), np.nan)
        all_fits_data = [[] for _ in range(len(self.time_vector))]
        
        num_cores = min(cpu_count(), MAX_CORES)
        
        try:
            # Process in chunks for progress updates
            total_chunks = len(args_list) // CHUNK_SIZE + 1
            
            with Pool(processes=num_cores) as pool:
                for chunk_idx in range(total_chunks):
                    start_idx = chunk_idx * CHUNK_SIZE
                    end_idx = min((chunk_idx + 1) * CHUNK_SIZE, len(args_list))
                    
                    if start_idx >= len(args_list):
                        break
                        
                    chunk_args = args_list[start_idx:end_idx]
                    
                    # Process chunk
                    results = pool.map(self._process_time_point, chunk_args)
                    
                    # Store results
                    for k, weighted_mapopt, local_fits in results:
                        mapopt_series[k] = weighted_mapopt
                        all_fits_data[k] = local_fits
                    
                    # Update progress
                    if progress_callback:
                        progress_pct = ((chunk_idx + 1) / total_chunks) * 100
                        progress_callback(progress_pct)
                        
        except Exception as e:
            # Fallback to single-threaded processing
            for i, args in enumerate(args_list):
                k, weighted_mapopt, local_fits = self._process_time_point(args)
                mapopt_series[k] = weighted_mapopt
                all_fits_data[k] = local_fits
                
                if progress_callback and i % 25 == 0:
                    progress_pct = (i / len(args_list)) * 100
                    progress_callback(progress_pct)
                    
        return mapopt_series, all_fits_data
        
    @staticmethod
    def _process_time_point(args: Tuple) -> Tuple[int, float, List[Dict]]:
        """Process single time point with full parameter space"""
        (k, t_now, t, MAP, rSO2, bins, bin_centers, 
         cox_windows_min, history_windows_hr) = args
        
        mapopts = []
        weights = []
        local_fits = []
        
        for cox_win_min in cox_windows_min:
            win_hr = cox_win_min / 60
            
            for hist_hr in history_windows_hr:
                fit_result = MAPoptCalculator._calculate_single_fit(
                    t_now, t, MAP, rSO2, win_hr, hist_hr, 
                    bins, bin_centers
                )
                
                if fit_result is not None:
                    mapopt, weight, fit_data = fit_result
                    mapopts.append(mapopt)
                    weights.append(weight)
                    local_fits.append(fit_data)
        
        if mapopts and len(weights) > 0:
            weighted_mapopt = np.sum(np.array(mapopts) * np.array(weights)) / np.sum(weights)
            return k, weighted_mapopt, local_fits
        else:
            return k, np.nan, []
            
    @staticmethod
    def _calculate_single_fit(
        t_now: float,
        t: np.ndarray,
        MAP: np.ndarray, 
        rSO2: np.ndarray,
        win_hr: float,
        hist_hr: float,
        bins: np.ndarray,
        bin_centers: np.ndarray
    ) -> Tuple[float, float, Dict]:
        """Calculate single curve fit for given parameters"""
        t_start = t_now - hist_hr
        if t_start < t[0]:
            return None
            
        # Get correlations and MAP values
        cox_vals, map_vals = SignalProcessor.calculate_sliding_window_correlations(
            t, MAP, rSO2, win_hr, hist_hr, t_now
        )
        
        if len(map_vals) < 5:
            return None
            
        # Bin correlations
        binned_cox = SignalProcessor.bin_correlations(cox_vals, map_vals, bins)
        
        # Apply Fisher transform
        with np.errstate(divide='ignore', invalid='ignore'):
            binned_cox_fisher = SignalProcessor.fisher_transform(binned_cox)
        
        valid = ~np.isnan(binned_cox_fisher) & np.isfinite(binned_cox_fisher)
        
        if np.sum(valid) >= 3:
            try:
                # Polynomial fitting
                coeffs = np.polyfit(bin_centers[valid], binned_cox_fisher[valid], 2)
                
                if coeffs[0] > 0:  # Upward parabola (minimum exists)
                    # Calculate MAPopt
                    mapopt_theoretical = -coeffs[1] / (2 * coeffs[0])
                    
                    # Constrain to data range
                    data_min = np.min(bin_centers[valid])
                    data_max = np.max(bin_centers[valid])
                    mapopt = np.clip(mapopt_theoretical, data_min, data_max)
                    
                    if MAP_OPT_MIN <= mapopt <= MAP_OPT_MAX:
                        # Calculate R-squared
                        yfit = np.polyval(coeffs, bin_centers[valid])
                        SSE = np.sum((binned_cox_fisher[valid] - yfit) ** 2)
                        SST = np.sum((binned_cox_fisher[valid] - np.mean(binned_cox_fisher[valid])) ** 2)
                        R2 = 1 - (SSE / SST)
                        
                        # Calculate nadir COx
                        nadir_cox_fisher = np.polyval(coeffs, mapopt)
                        nadir_cox = SignalProcessor.inverse_fisher_transform(nadir_cox_fisher)
                        
                        # Calculate weight
                        weight = MAPoptCalculator._calculate_weight(nadir_cox, R2)
                        
                        if weight > 1e-6:
                            fit_data = {
                                'win_hr': win_hr,
                                'hist_hr': hist_hr,
                                'bin_centers': bin_centers[valid],
                                'binned_cox': binned_cox[valid],
                                'binned_cox_fisher': binned_cox_fisher[valid],
                                'coeffs': coeffs,
                                'mapopt': mapopt,
                                'nadir_cox': nadir_cox,
                                'r2': R2,
                                'weight': weight
                            }
                            return mapopt, weight, fit_data
            except:
                pass
                
        return None
        
    @staticmethod
    def _calculate_weight(nadir_cox: float, r2: float) -> float:
        """Calculate weight for curve fit based on COx value and R-squared"""
        if nadir_cox < 0:
            # Negative COx - good autoregulation
            cox_weight = -nadir_cox
        elif nadir_cox <= COX_WEIGHT_THRESHOLD:
            # Positive but low COx - scaled weight
            cox_weight = (COX_WEIGHT_THRESHOLD - nadir_cox) / COX_WEIGHT_THRESHOLD
        else:
            # High positive correlation - poor autoregulation
            cox_weight = 0
            
        return r2 * cox_weight
        
    def _post_process_mapopt(self, mapopt_series: np.ndarray) -> np.ndarray:
        """Post-process MAPopt series with interpolation and smoothing"""
        # Fill missing values with interpolation
        mapopt_filled = pd.Series(mapopt_series).interpolate(method='pchip').values
        
        # Clamp values to physiological range
        mapopt_filled = np.clip(mapopt_filled, MAP_OPT_MIN, MAP_OPT_MAX)
        
        # Fill any remaining NaN
        mapopt_series_clean = pd.Series(mapopt_filled)
        mapopt_series_clean = mapopt_series_clean.ffill().bfill()
        mapopt_filled = mapopt_series_clean.values
        
        # Apply Savitzky-Golay filter for smoothing
        if len(mapopt_filled) > SAVGOL_WINDOW:
            mapopt_filled = signal.savgol_filter(
                mapopt_filled, SAVGOL_WINDOW, SAVGOL_ORDER
            )
            
        return mapopt_filled
        
    def get_calculation_summary(self) -> Dict[str, Any]:
        """Get summary of MAPopt calculation"""
        if self.mapopt_series is None:
            return {}
            
        valid_points = np.sum(~np.isnan(self.mapopt_series))
        total_points = len(self.mapopt_series)
        
        return {
            'total_time_points': total_points,
            'valid_mapopt_points': valid_points,
            'validity_percentage': (valid_points / total_points) * 100,
            'mapopt_range': (np.nanmin(self.mapopt_filled), np.nanmax(self.mapopt_filled)),
            'mapopt_mean': np.nanmean(self.mapopt_filled),
            'mapopt_std': np.nanstd(self.mapopt_filled)
        } 
