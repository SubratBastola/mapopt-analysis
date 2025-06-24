 
"""
Plotting and visualization module for MAPopt Analysis
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.figure import Figure
from typing import Optional, Tuple, List, Dict, Any

from ..config import COX_UPPER_THRESHOLD, COX_LOWER_THRESHOLD, PLOT_DPI


class PlotManager:
    """Manages plotting and visualization for MAPopt analysis"""
    
    def __init__(self):
        self.fig = None
        self.axes = None
        
    def create_main_analysis_plots(
        self,
        data: pd.DataFrame,
        cox_time: np.ndarray,
        cox_values: np.ndarray,
        time_vector: np.ndarray,
        mapopt_filled: np.ndarray,
        deviation: np.ndarray,
        outside_upper: np.ndarray,
        outside_lower: np.ndarray,
        subject_id: str
    ) -> Figure:
        """
        Create the main 4-panel analysis plot
        
        Args:
            data: Original data DataFrame
            cox_time: COx time vector
            cox_values: COx correlation values
            time_vector: Analysis time vector
            mapopt_filled: Processed MAPopt series
            deviation: Deviation from MAPopt
            outside_upper/lower: Boolean arrays for bound violations
            subject_id: Subject identifier
            
        Returns:
            Matplotlib Figure object
        """
        # Create figure
        self.fig = Figure(figsize=(14, 10))
        self.axes = []
        
        for i in range(4):
            ax = self.fig.add_subplot(4, 1, i+1)
            self.axes.append(ax)
        
        # Plot 1: COx vs Time
        self._plot_cox_correlations(cox_time, cox_values)
        
        # Plot 2: MAP vs Time
        self._plot_map_timeseries(data)
        
        # Plot 3: MAPopt vs Time
        self._plot_mapopt_timeseries(time_vector, mapopt_filled)
        
        # Plot 4: Deviation from MAPopt
        self._plot_deviation(time_vector, deviation, outside_upper, outside_lower)
        
        # Set common x-axis limits
        x_min, x_max = data['time'].iloc[0], data['time'].iloc[-1]
        for ax in self.axes:
            ax.set_xlim([x_min, x_max])
            
        # Set title
        self.fig.suptitle(f'Subject {subject_id} - MAPopt Analysis', fontsize=14)
        self.fig.tight_layout()
        
        return self.fig
        
    def _plot_cox_correlations(self, cox_time: np.ndarray, cox_values: np.ndarray):
        """Plot COx correlations vs time"""
        ax = self.axes[0]
        
        if len(cox_time) > 0:
            ax.plot(cox_time, cox_values, '-ok', linewidth=1, markersize=2)
            
        # Add threshold lines
        ax.axhline(y=COX_UPPER_THRESHOLD, color='r', linestyle='--', alpha=0.7)
        ax.axhline(y=-COX_UPPER_THRESHOLD, color='r', linestyle='--', alpha=0.7)
        
        ax.set_ylabel('COx')
        ax.set_title('(a) COx vs Time')
        ax.set_ylim([-1, 1])
        ax.grid(True, alpha=0.3)
        
    def _plot_map_timeseries(self, data: pd.DataFrame):
        """Plot MAP time series"""
        ax = self.axes[1]
        
        ax.plot(data['time'], data['MAP'], '-b', linewidth=1)
        ax.set_ylabel('MAP [mmHg]')
        ax.set_title('(b) MAP vs Time')
        ax.grid(True, alpha=0.3)
        
    def _plot_mapopt_timeseries(self, time_vector: np.ndarray, mapopt_filled: np.ndarray):
        """Plot MAPopt time series"""
        ax = self.axes[2]
        
        ax.plot(time_vector, mapopt_filled, '-r', linewidth=1.5)
        ax.set_ylabel('MAPopt [mmHg]')
        ax.set_title('(c) Optimal MAP vs Time')
        ax.set_ylim([40, 100])
        ax.grid(True, alpha=0.3)
        
    def _plot_deviation(
        self, 
        time_vector: np.ndarray, 
        deviation: np.ndarray,
        outside_upper: np.ndarray,
        outside_lower: np.ndarray
    ):
        """Plot deviation from MAPopt with burden areas"""
        ax = self.axes[3]
        
        # Main deviation line
        ax.plot(time_vector, deviation, '-g', linewidth=1)
        
        # Threshold lines
        ax.axhline(y=5, color='r', linestyle='--', alpha=0.7)
        ax.axhline(y=-5, color='r', linestyle='--', alpha=0.7)
        
        # Fill areas outside bounds
        self._fill_burden_areas(ax, time_vector, deviation, outside_upper, outside_lower)
        
        ax.set_xlabel('Time [hr]')
        ax.set_ylabel('Deviation [mmHg]')
        ax.set_title('(d) Deviation from MAPopt')
        ax.set_ylim([-30, 30])
        ax.grid(True, alpha=0.3)
        
    def _fill_burden_areas(
        self,
        ax,
        time_vector: np.ndarray,
        deviation: np.ndarray, 
        outside_upper: np.ndarray,
        outside_lower: np.ndarray
    ):
        """Fill areas representing burden outside safe bounds"""
        for i in range(len(time_vector)-1):
            if outside_upper[i]:
                x = [time_vector[i], time_vector[i+1], 
                     time_vector[i+1], time_vector[i]]
                y = [5, 5, deviation[i+1], deviation[i]]
                ax.fill(x, y, 'r', alpha=0.3)
                
            if outside_lower[i]:
                x = [time_vector[i], time_vector[i+1], 
                     time_vector[i+1], time_vector[i]]
                y = [-5, -5, deviation[i+1], deviation[i]]
                ax.fill(x, y, 'b', alpha=0.3)
                
    def update_time_indicators(self, t_start: float, t_end: float):
        """Update time indicator lines on all plots"""
        if self.axes is None:
            return
            
        for ax in self.axes:
            # Remove existing indicator lines
            lines_to_remove = [line for line in ax.lines if hasattr(line, '_time_indicator')]
            for line in lines_to_remove:
                line.remove()
            
            # Add new indicator lines
            line1 = ax.axvline(x=t_start, color='blue', linestyle='--', linewidth=2, alpha=0.7)
            line2 = ax.axvline(x=t_end, color='blue', linestyle='--', linewidth=2, alpha=0.7)
            line1._time_indicator = True
            line2._time_indicator = True
            
    def create_curve_fits_plot(
        self, 
        actual_time: float, 
        fits: List[Dict[str, Any]]
    ) -> Figure:
        """
        Create detailed curve fits visualization
        
        Args:
            actual_time: Time point for analysis
            fits: List of curve fit data dictionaries
            
        Returns:
            Matplotlib Figure object
        """
        # Calculate weighted average
        all_mapopts = [fit['mapopt'] for fit in fits]
        all_weights = [fit['weight'] for fit in fits]
        weighted_mapopt = np.sum(np.array(all_mapopts) * np.array(all_weights)) / np.sum(all_weights)
        
        # Sort fits by weight
        fits_sorted = sorted(fits, key=lambda x: x['weight'], reverse=True)
        
        # Create figure
        fig = Figure(figsize=(15, 10))
        
        # Individual fit subplots
        max_fits = min(15, len(fits_sorted))
        rows, cols = 3, 5
        
        for i in range(max_fits):
            ax = fig.add_subplot(rows, cols, i+1)
            self._plot_single_curve_fit(ax, fits_sorted[i])
            
        # Summary plots
        if max_fits == 15:
            self._plot_curve_summary(fig, fits_sorted, weighted_mapopt, all_mapopts, all_weights)
            
        fig.suptitle(
            f'Curve Fits at {actual_time:.2f} hours | Weighted MAPopt = {weighted_mapopt:.1f} mmHg',
            fontsize=14
        )
        fig.tight_layout()
        
        return fig
        
    def _plot_single_curve_fit(self, ax, fit: Dict[str, Any]):
        """Plot individual curve fit"""
        # Plot data points
        ax.scatter(fit['bin_centers'], fit['binned_cox'], s=30, c='blue', alpha=0.6)
        
        # Plot fitted curve
        x_range = np.linspace(
            max(40, np.min(fit['bin_centers']) - 5),
            min(90, np.max(fit['bin_centers']) + 5), 
            100
        )
        y_fisher = np.polyval(fit['coeffs'], x_range)
        y_orig = np.tanh(y_fisher)  # Inverse Fisher transform
        ax.plot(x_range, y_orig, 'r-', linewidth=2)
        
        # Mark optimal point
        ax.scatter(fit['mapopt'], fit['nadir_cox'], s=60, c='red', marker='d', zorder=5)
        
        # Formatting
        ax.set_xlim([40, 90])
        ax.set_ylim([-1, 1])
        ax.grid(True, alpha=0.3)
        ax.set_title(f"W={fit['win_hr']*60:.0f}min, H={fit['hist_hr']:.1f}hr", fontsize=9)
        
        # Add statistics
        ax.text(42, 0.8, f"MAPopt={fit['mapopt']:.1f}", fontsize=7,
               bbox=dict(boxstyle="round,pad=0.2", facecolor="yellow", alpha=0.7))
        ax.text(42, 0.6, f"R²={fit['r2']:.2f}", fontsize=7)
        ax.text(42, 0.4, f"W={fit['weight']:.3f}", fontsize=7)
        
    def _plot_curve_summary(
        self, 
        fig: Figure, 
        fits_sorted: List[Dict],
        weighted_mapopt: float,
        all_mapopts: List[float],
        all_weights: List[float]
    ):
        """Plot summary curves and histogram"""
        rows, cols = 3, 5
        
        # All curves overlay
        ax_summary = fig.add_subplot(rows, cols, rows*cols-1)
        colors = plt.cm.viridis(np.linspace(0, 1, min(8, len(fits_sorted))))
        
        for i, fit in enumerate(fits_sorted[:8]):
            x_range = np.linspace(
                max(40, np.min(fit['bin_centers']) - 5),
                min(90, np.max(fit['bin_centers']) + 5), 
                100
            )
            y_fisher = np.polyval(fit['coeffs'], x_range)
            y_orig = np.tanh(y_fisher)
            
            alpha = 0.4 + 0.6 * (fit['weight'] / max(all_weights))
            ax_summary.plot(x_range, y_orig, color=colors[i], linewidth=2, alpha=alpha)
        
        ax_summary.axvline(x=weighted_mapopt, color='black', linewidth=3,
                         label=f'Weighted MAPopt = {weighted_mapopt:.1f}')
        ax_summary.set_xlim([40, 90])
        ax_summary.set_ylim([-1, 1])
        ax_summary.grid(True, alpha=0.3)
        ax_summary.set_title('Top Curves', fontsize=10)
        ax_summary.legend(fontsize=8)
        ax_summary.set_xlabel('MAP (mmHg)')
        ax_summary.set_ylabel('COx')
        
        # MAPopt histogram
        ax_hist = fig.add_subplot(rows, cols, rows*cols)
        weights_normalized = np.array(all_weights) / np.sum(all_weights)
        ax_hist.hist(all_mapopts, bins=np.arange(40, 95, 5), 
                    weights=weights_normalized, alpha=0.7, 
                    color='skyblue', edgecolor='black')
        ax_hist.axvline(x=weighted_mapopt, color='red', linewidth=2)
        ax_hist.set_xlabel('MAPopt (mmHg)')
        ax_hist.set_ylabel('Weighted Frequency')
        ax_hist.set_title('MAPopt Distribution', fontsize=10)
        ax_hist.grid(True, alpha=0.3)
        
    def update_plot_title(
        self, 
        subject_id: str, 
        t_start: float, 
        t_end: float,
        time_burden: float,
        area_burden: float
    ):
        """Update main plot title with burden metrics"""
        if self.fig is None:
            return
            
        title = (f"Subject {subject_id} | "
                f"Period ({t_start:.2f} - {t_end:.2f} hr) | "
                f"Time Burden: {time_burden:.1f}% | "
                f"Area Burden: {area_burden:.1f}%")
        self.fig.suptitle(title, fontsize=12)
        
    def save_figure(self, filename: str, **kwargs):
        """Save current figure to file"""
        if self.fig is None:
            raise ValueError("No figure to save")
            
        save_kwargs = {'dpi': PLOT_DPI, 'bbox_inches': 'tight'}
        save_kwargs.update(kwargs)
        
        self.fig.savefig(filename, **save_kwargs)