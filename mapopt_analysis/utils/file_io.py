 
"""
File I/O utilities for MAPopt Analysis Tool
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional


class FileManager:
    """Handles file input/output operations"""
    
    @staticmethod
    def save_burden_metrics(
        results: Dict[str, float],
        subject_id: str,
        file_path: str,
        save_dir: str
    ) -> str:
        """
        Save burden metrics to CSV file
        
        Args:
            results: Burden calculation results
            subject_id: Subject identifier
            file_path: Original data file path
            save_dir: Directory to save results
            
        Returns:
            Path to saved file
        """
        burden_df = pd.DataFrame([{
            'Subject_ID': subject_id,
            'StartTime_hr': results['t_start_hr'],
            'EndTime_hr': results['t_end_hr'],
            'TimeBurden_percent': results['time_burden'],
            'AreaBurdenRatio_percent': results['area_burden_ratio'],
            'Analysis_DateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'DataFile': os.path.basename(file_path)
        }])
        
        burden_file = os.path.join(save_dir, f'Burden_metrics_Sub{subject_id}.csv')
        burden_df.to_csv(burden_file, index=False)
        
        return burden_file
        
    @staticmethod
    def save_timeseries_data(
        time_vector: np.ndarray,
        cox_time: np.ndarray,
        cox_values: np.ndarray,
        data: pd.DataFrame,
        mapopt_filled: np.ndarray,
        deviation: np.ndarray,
        outside_bounds: np.ndarray,
        subject_id: str,
        save_dir: str
    ) -> str:
        """
        Save time series data to CSV file
        
        Args:
            time_vector: Analysis time vector
            cox_time: COx time points
            cox_values: COx correlation values
            data: Original data DataFrame
            mapopt_filled: Processed MAPopt series
            deviation: Deviation from MAPopt
            outside_bounds: Boolean array for bound violations
            subject_id: Subject identifier
            save_dir: Directory to save results
            
        Returns:
            Path to saved file
        """
        # Interpolate COx and MAP to analysis time vector
        cox_interp = np.interp(time_vector, cox_time, cox_values) if len(cox_time) > 0 else np.full_like(time_vector, np.nan)
        map_interp = np.interp(time_vector, data['time'], data['MAP'])
        
        timeseries_df = pd.DataFrame({
            'Time_hr': time_vector,
            'COx': cox_interp,
            'MAP_mmHg': map_interp,
            'MAPopt_mmHg': mapopt_filled,
            'Deviation_mmHg': deviation,
            'OutsideBounds': outside_bounds.astype(int)
        })
        
        timeseries_file = os.path.join(save_dir, f'COx_MAPopt_timeseries_Sub{subject_id}.csv')
        timeseries_df.to_csv(timeseries_file, index=False)
        
        return timeseries_file
        
    @staticmethod
    def save_analysis_summary(
        data_summary: Dict[str, Any],
        calculation_summary: Dict[str, Any],
        burden_summary: Dict[str, Any],
        subject_id: str,
        save_dir: str
    ) -> str:
        """
        Save comprehensive analysis summary
        
        Args:
            data_summary: Data loading summary
            calculation_summary: MAPopt calculation summary
            burden_summary: Burden metrics summary
            subject_id: Subject identifier
            save_dir: Directory to save results
            
        Returns:
            Path to saved file
        """
        summary = {
            'Subject_ID': subject_id,
            'Analysis_DateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Add data summary with prefix
        for key, value in data_summary.items():
            summary[f'Data_{key}'] = value
            
        # Add calculation summary with prefix
        for key, value in calculation_summary.items():
            summary[f'Calc_{key}'] = value
            
        # Add burden summary with prefix
        for key, value in burden_summary.items():
            summary[f'Burden_{key}'] = value
            
        summary_df = pd.DataFrame([summary])
        summary_file = os.path.join(save_dir, f'Analysis_summary_Sub{subject_id}.csv')
        summary_df.to_csv(summary_file, index=False)
        
        return summary_file
        
    @staticmethod
    def save_curve_fits_data(
        all_fits_data: list,
        time_vector: np.ndarray,
        subject_id: str,
        save_dir: str
    ) -> str:
        """
        Save curve fitting data for detailed analysis
        
        Args:
            all_fits_data: List of fits data for each time point
            time_vector: Analysis time vector
            subject_id: Subject identifier
            save_dir: Directory to save results
            
        Returns:
            Path to saved file
        """
        fits_records = []
        
        for t_idx, time_point in enumerate(time_vector):
            fits = all_fits_data[t_idx]
            
            for fit_idx, fit in enumerate(fits):
                record = {
                    'Time_hr': time_point,
                    'Fit_Index': fit_idx,
                    'Window_hr': fit['win_hr'],
                    'History_hr': fit['hist_hr'],
                    'MAPopt': fit['mapopt'],
                    'Nadir_COx': fit['nadir_cox'],
                    'R_squared': fit['r2'],
                    'Weight': fit['weight']
                }
                fits_records.append(record)
                
        if fits_records:
            fits_df = pd.DataFrame(fits_records)
            fits_file = os.path.join(save_dir, f'Curve_fits_Sub{subject_id}.csv')
            fits_df.to_csv(fits_file, index=False)
            return fits_file
        else:
            return ""
            
    @staticmethod
    def load_previous_results(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load previously saved results
        
        Args:
            file_path: Path to results file
            
        Returns:
            Dictionary with loaded results or None if loading fails
        """
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
                return df.to_dict('records')[0] if len(df) > 0 else None
            else:
                return None
        except Exception:
            return None
            
    @staticmethod
    def validate_save_directory(save_dir: str) -> bool:
        """
        Validate that save directory exists and is writable
        
        Args:
            save_dir: Directory path to validate
            
        Returns:
            True if directory is valid and writable
        """
        try:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            # Test write permissions
            test_file = os.path.join(save_dir, 'test_write.tmp')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            
            return True
        except Exception:
            return False
            
    @staticmethod
    def get_supported_formats() -> Dict[str, list]:
        """Get supported file formats for import and export"""
        return {
            'import': ['.csv', '.txt'],
            'export_data': ['.csv'],
            'export_figures': ['.png', '.pdf', '.svg', '.eps']
        }
        
    @staticmethod
    def create_results_manifest(
        save_dir: str,
        subject_id: str,
        saved_files: list
    ) -> str:
        """
        Create a manifest file listing all saved results
        
        Args:
            save_dir: Directory containing results
            subject_id: Subject identifier
            saved_files: List of saved file paths
            
        Returns:
            Path to manifest file
        """
        manifest_data = {
            'Subject_ID': subject_id,
            'Analysis_DateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Total_Files': len(saved_files),
            'Files': saved_files
        }
        
        manifest_file = os.path.join(save_dir, f'Results_manifest_Sub{subject_id}.txt')
        
        with open(manifest_file, 'w') as f:
            f.write(f"MAPopt Analysis Results Manifest\n")
            f.write(f"Subject ID: {subject_id}\n")
            f.write(f"Analysis Date/Time: {manifest_data['Analysis_DateTime']}\n")
            f.write(f"Total Files: {manifest_data['Total_Files']}\n\n")
            f.write("Generated Files:\n")
            
            for i, file_path in enumerate(saved_files, 1):
                f.write(f"{i}. {os.path.basename(file_path)}\n")
                
        return manifest_file