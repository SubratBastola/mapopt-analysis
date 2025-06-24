 
"""
Burden metrics calculation module for MAPopt Analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple

from ..config import BURDEN_BOUNDS, DEVIATION_MIN, DEVIATION_MAX


class BurdenCalculator:
    """Calculates deviation and burden metrics from MAPopt analysis"""
    
    def __init__(self):
        self.deviation = None
        self.lower_bound = None
        self.upper_bound = None
        self.outside_upper = None
        self.outside_lower = None
        self.outside_bounds = None
        self.excess_above = None
        self.excess_below = None
        
    def calculate_deviation_and_burden(
        self, 
        data: pd.DataFrame,
        time_vector: np.ndarray,
        mapopt_filled: np.ndarray
    ) -> None:
        """
        Calculate deviation from MAPopt and burden metrics
        
        Args:
            data: Original data DataFrame
            time_vector: Time vector for analysis
            mapopt_filled: Processed MAPopt series
        """
        # Interpolate MAP to time vector
        map_interp = np.interp(time_vector, data['time'], data['MAP'])
        
        # Calculate deviation
        self.deviation = map_interp - mapopt_filled
        self.deviation = np.clip(self.deviation, DEVIATION_MIN, DEVIATION_MAX)
        
        # Define bounds
        self.lower_bound = mapopt_filled - BURDEN_BOUNDS
        self.upper_bound = mapopt_filled + BURDEN_BOUNDS
        
        # Calculate periods outside bounds
        self.outside_upper = map_interp > self.upper_bound
        self.outside_lower = map_interp < self.lower_bound
        self.outside_bounds = self.outside_upper | self.outside_lower
        
        # Calculate excess deviations
        self.excess_above = np.where(self.outside_upper, map_interp - self.upper_bound, 0)
        self.excess_below = np.where(self.outside_lower, self.lower_bound - map_interp, 0)
        
    def calculate_burden_metrics(
        self, 
        time_vector: np.ndarray,
        t_start_hr: float, 
        t_end_hr: float
    ) -> Dict[str, float]:
        """
        Calculate burden metrics for specified time period
        
        Args:
            time_vector: Time vector
            t_start_hr: Start time in hours
            t_end_hr: End time in hours
            
        Returns:
            Dictionary with burden metrics
        """
        if self.outside_bounds is None:
            raise ValueError("Must call calculate_deviation_and_burden first")
            
        # Validate and adjust bounds
        t_start_hr = max(t_start_hr, time_vector[0])
        t_end_hr = min(t_end_hr, time_vector[-1])
        
        # Find indices for time period
        time_idx = (time_vector >= t_start_hr) & (time_vector <= t_end_hr)
        
        if not np.any(time_idx):
            return {
                't_start_hr': t_start_hr,
                't_end_hr': t_end_hr,
                'time_burden': 0.0,
                'area_burden_ratio': 0.0
            }
        
        # Calculate time burden (percentage of time outside bounds)
        time_burden = np.sum(self.outside_bounds[time_idx]) / np.sum(time_idx) * 100
        
        # Calculate area burden
        area_burden_ratio = self._calculate_area_burden(time_vector, time_idx)
        
        return {
            't_start_hr': t_start_hr,
            't_end_hr': t_end_hr,
            'time_burden': time_burden,
            'area_burden_ratio': area_burden_ratio
        }
        
    def _calculate_area_burden(
        self, 
        time_vector: np.ndarray, 
        time_idx: np.ndarray
    ) -> float:
        """Calculate area burden ratio"""
        # Area outside safe zone
        area_outside = np.trapz(
            (self.excess_above[time_idx] + self.excess_below[time_idx]),
            time_vector[time_idx]
        )
        
        # Total safe zone area
        area_safe_zone = np.trapz(
            (self.upper_bound[time_idx] - self.lower_bound[time_idx]),
            time_vector[time_idx]
        )
        
        if area_safe_zone > 0:
            return (area_outside / area_safe_zone) * 100
        else:
            return 0.0
            
    def get_deviation_statistics(self) -> Dict[str, float]:
        """Get statistical summary of deviation metrics"""
        if self.deviation is None:
            return {}
            
        return {
            'mean_deviation': np.mean(self.deviation),
            'std_deviation': np.std(self.deviation),
            'max_positive_deviation': np.max(self.deviation),
            'max_negative_deviation': np.min(self.deviation),
            'percent_time_above_bounds': np.mean(self.outside_upper) * 100,
            'percent_time_below_bounds': np.mean(self.outside_lower) * 100,
            'percent_time_outside_bounds': np.mean(self.outside_bounds) * 100
        }
        
    def calculate_burden_over_time(
        self, 
        time_vector: np.ndarray,
        window_hours: float = 4.0,
        step_hours: float = 1.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate burden metrics over sliding time windows
        
        Args:
            time_vector: Time vector
            window_hours: Window size in hours
            step_hours: Step size in hours
            
        Returns:
            Tuple of (time_centers, burden_values)
        """
        if self.outside_bounds is None:
            raise ValueError("Must call calculate_deviation_and_burden first")
            
        start_time = time_vector[0]
        end_time = time_vector[-1] - window_hours
        
        time_centers = []
        burden_values = []
        
        current_time = start_time
        while current_time <= end_time:
            window_start = current_time
            window_end = current_time + window_hours
            
            # Calculate burden for this window
            burden_result = self.calculate_burden_metrics(
                time_vector, window_start, window_end
            )
            
            time_centers.append(current_time + window_hours / 2)
            burden_values.append(burden_result['time_burden'])
            
            current_time += step_hours
            
        return np.array(time_centers), np.array(burden_values)
        
    def get_burden_summary(
        self, 
        time_vector: np.ndarray,
        full_period: bool = True
    ) -> Dict[str, float]:
        """
        Get comprehensive burden summary
        
        Args:
            time_vector: Time vector
            full_period: Whether to calculate for full time period
            
        Returns:
            Dictionary with burden summary metrics
        """
        if full_period:
            metrics = self.calculate_burden_metrics(
                time_vector, time_vector[0], time_vector[-1]
            )
        else:
            metrics = {}
            
        # Add deviation statistics
        dev_stats = self.get_deviation_statistics()
        metrics.update(dev_stats)
        
        # Add additional metrics
        if self.excess_above is not None and self.excess_below is not None:
            metrics.update({
                'total_excess_above': np.sum(self.excess_above),
                'total_excess_below': np.sum(self.excess_below),
                'mean_excess_above': np.mean(self.excess_above[self.outside_upper]),
                'mean_excess_below': np.mean(self.excess_below[self.outside_lower])
            })
            
        return metrics