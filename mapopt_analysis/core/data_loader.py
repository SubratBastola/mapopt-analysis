"""
Data loading and preprocessing module for MAPopt Analysis Tool
"""

import os
import re
import numpy as np
import pandas as pd
from scipy import signal
from typing import Tuple, Optional

from ..config import MAP_MIN, MAP_MAX, OUTLIER_THRESHOLD, MEDIAN_FILTER_SIZE, ROLLING_WINDOW_SIZE


class DataLoader:
    """Handles loading and preprocessing of biomedical signal data"""
    
    def __init__(self):
        self.data = None
        self.subject_id = None
        self.file_path = None
        
    def load_data(self, file_path: str) -> pd.DataFrame:
        """
        Load and preprocess data from file
        
        Args:
            file_path: Path to data file (CSV or TXT)
            
        Returns:
            Processed DataFrame with columns: time, MAP, rSO2
            
        Raises:
            ValueError: If file format is invalid or data is insufficient
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        self.file_path = file_path
        self.subject_id = self._extract_subject_id(file_path)
        
        # Load data based on file extension
        try:
            if file_path.lower().endswith('.csv'):
                data = pd.read_csv(file_path)
            else:
                data = pd.read_csv(file_path, delimiter='\t')
        except Exception as e:
            raise ValueError(f"Error loading file: {e}")
            
        # Validate data structure
        if data.shape[1] < 3:
            raise ValueError("Data file must have at least 3 columns: time, MAP, rSO2")
            
        # Assign standard column names and convert time to hours
        data.columns = ['time', 'MAP', 'rSO2']
        data['time'] = data['time'] / 60  # Convert to hours
        
        # Process data
        data = self._handle_duplicates(data)
        data = self._clean_data(data)
        
        self.data = data
        return data
        
    def _extract_subject_id(self, filename: str) -> str:
        """Extract subject ID from filename using regex"""
        matches = re.findall(r'(\d+)', os.path.basename(filename))
        return matches[0] if matches else "001"
        
    def _handle_duplicates(self, data: pd.DataFrame) -> pd.DataFrame:
        """Handle duplicate time points by averaging values"""
        # Check for duplicates
        duplicates = data.duplicated(subset=['time'], keep=False)
        
        if duplicates.any():
            # Average duplicate values
            data = data.groupby('time').agg({
                'MAP': 'mean', 
                'rSO2': 'mean'
            }).reset_index()
            
        # Ensure monotonic time
        data = data.sort_values('time').reset_index(drop=True)
        
        # Fix any remaining non-monotonic issues
        self._fix_monotonic_time(data)
        
        return data
        
    def _fix_monotonic_time(self, data: pd.DataFrame) -> None:
        """Ensure time vector is strictly monotonic"""
        time_diff = np.diff(data['time'])
        if np.any(time_diff <= 0):
            for i in range(1, len(data)):
                if data.loc[i, 'time'] <= data.loc[i-1, 'time']:
                    data.loc[i, 'time'] = data.loc[i-1, 'time'] + 1e-6
                    
    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and filter data"""
        # Clamp MAP values to physiological range
        data['MAP'] = np.clip(data['MAP'], MAP_MIN, MAP_MAX)
        
        # Remove NaN values
        original_length = len(data)
        data = data.dropna().reset_index(drop=True)
        
        # Outlier detection and correction
        data = self._detect_and_correct_outliers(data)
        
        # Apply smoothing filters
        data = self._apply_filters(data)
        
        return data
        
    def _detect_and_correct_outliers(self, data: pd.DataFrame) -> pd.DataFrame:
        """Detect and correct outliers using rolling statistics"""
        # Calculate time step for window sizing
        time_step = np.mean(np.diff(data['time']))
        window_size = max(3, int(0.5 / time_step))
        
        # Rolling statistics for outlier detection
        rolling_mean = data['MAP'].rolling(window=window_size, center=True).mean()
        rolling_std = data['MAP'].rolling(window=window_size, center=True).std()
        
        # Calculate Z-scores
        z_scores = np.abs((data['MAP'] - rolling_mean) / rolling_std)
        
        # Replace outliers with NaN and interpolate
        outliers = z_scores > OUTLIER_THRESHOLD
        data.loc[outliers, 'MAP'] = np.nan
        data['MAP'] = data['MAP'].interpolate(method='linear')
        
        return data
        
    def _apply_filters(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply smoothing filters to the data"""
        # Median filter for spike removal
        data['MAP'] = signal.medfilt(data['MAP'], kernel_size=MEDIAN_FILTER_SIZE)
        data['rSO2'] = signal.medfilt(data['rSO2'], kernel_size=MEDIAN_FILTER_SIZE)
        
        # Rolling average for smoothing
        data['MAP'] = data['MAP'].rolling(window=ROLLING_WINDOW_SIZE, center=True).mean()
        
        return data
        
    def get_data_summary(self) -> dict:
        """Get summary statistics of loaded data"""
        if self.data is None:
            return {}
            
        duration = self.data['time'].iloc[-1] - self.data['time'].iloc[0]
        median_interval = np.median(np.diff(self.data['time'])) * 60  # Convert to minutes
        
        summary = {
            'subject_id': self.subject_id,
            'file_path': self.file_path,
            'duration_hours': duration,
            'data_points': len(self.data),
            'sampling_interval_min': median_interval,
            'map_range': (self.data['MAP'].min(), self.data['MAP'].max()),
            'rso2_range': (self.data['rSO2'].min(), self.data['rSO2'].max()),
            'map_std': self.data['MAP'].std(),
            'rso2_std': self.data['rSO2'].std()
        }
        
        # Calculate overall correlation
        try:
            mask = np.isfinite(self.data['MAP']) & np.isfinite(self.data['rSO2'])
            if np.sum(mask) > 3:
                overall_corr = np.corrcoef(
                    self.data['MAP'][mask], 
                    self.data['rSO2'][mask]
                )[0, 1]
                summary['overall_correlation'] = overall_corr
        except:
            summary['overall_correlation'] = np.nan
            
        return summary 
