"""
Main GUI window for MAPopt Analysis Tool
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from ..core.data_loader import DataLoader
from ..core.signal_processing import SignalProcessor
from ..core.mapopt_calculator import MAPoptCalculator
from ..core.burden_metrics import BurdenCalculator
from ..visualization.plots import PlotManager
from ..utils.file_io import FileManager
from ..utils.logger import AnalysisLogger
from ..config import WINDOW_TITLE, WINDOW_SIZE
from .dialogs import CurveFitsDialog


class MAPoptAnalysisGUI:
    """Main GUI application for MAPopt Analysis"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.state('zoomed')  # Maximize window on Windows
        
        # Initialize components
        self.data_loader = DataLoader()
        self.mapopt_calculator = MAPoptCalculator()
        self.burden_calculator = BurdenCalculator()
        self.plot_manager = PlotManager()
        self.file_manager = FileManager()
        self.logger = AnalysisLogger("GUI")
        
        # Analysis data
        self.cox_time = None
        self.cox_values = None
        self.last_burden_results = None
        
        # GUI setup
        self.setup_gui()
        
        # Set logger callback
        self.logger.set_gui_callback(self.log_message)
        
        # Initial messages
        self.logger.info("MAPopt Analysis Tool initialized", "🔬")
        self.logger.info("Load a CSV/TXT file with columns: [time, MAP, rSO2]", "📁")
        
    def setup_gui(self):
        """Setup the main GUI interface"""
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Setup control panel
        self.setup_control_panel(main_frame)
        
        # Setup main content area
        self.setup_content_area(main_frame)
        
        # Setup status bar
        self.setup_status_bar(main_frame)
        
    def setup_control_panel(self, parent):
        """Setup the top control panel"""
        control_frame = ttk.LabelFrame(parent, text="Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # File selection row
        file_frame = ttk.Frame(control_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(file_frame, text="Data File:").pack(side=tk.LEFT)
        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_var, width=60)
        self.file_entry.pack(side=tk.LEFT, padx=(10, 10), fill=tk.X, expand=True)
        
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(file_frame, text="Load & Analyze", command=self.start_analysis).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(file_frame, text="Data Summary", command=self.show_data_summary).pack(side=tk.LEFT)
        
        # Analysis controls row
        analysis_frame = ttk.Frame(control_frame)
        analysis_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Time range controls
        self.setup_time_controls(analysis_frame)
        
        # Curve fits controls
        self.setup_curve_controls(analysis_frame)
        
        # Save controls
        self.setup_save_controls(analysis_frame)
        
    def setup_time_controls(self, parent):
        """Setup time range controls"""
        time_frame = ttk.LabelFrame(parent, text="Burden Analysis Time Range", padding=5)
        time_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(time_frame, text="Start (hr):").grid(row=0, column=0, padx=5, pady=2)
        self.start_var = tk.DoubleVar(value=0.0)
        self.start_entry = ttk.Entry(time_frame, textvariable=self.start_var, width=10)
        self.start_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(time_frame, text="End (hr):").grid(row=1, column=0, padx=5, pady=2)
        self.end_var = tk.DoubleVar(value=24.0)
        self.end_entry = ttk.Entry(time_frame, textvariable=self.end_var, width=10)
        self.end_entry.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Button(time_frame, text="Calculate Burden", 
                  command=self.calculate_burden).grid(row=2, column=0, columnspan=2, pady=5)
                  
    def setup_curve_controls(self, parent):
        """Setup curve fits controls"""
        fits_frame = ttk.LabelFrame(parent, text="Curve Fits Analysis", padding=5)
        fits_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(fits_frame, text="Time (hr):").grid(row=0, column=0, padx=5, pady=2)
        self.time_var = tk.DoubleVar(value=0.0)
        self.time_entry = ttk.Entry(fits_frame, textvariable=self.time_var, width=10)
        self.time_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Button(fits_frame, text="Show Curve Fits", 
                  command=self.show_curve_fits).grid(row=1, column=0, columnspan=2, pady=5)
                  
    def setup_save_controls(self, parent):
        """Setup save/export controls"""
        save_frame = ttk.LabelFrame(parent, text="Export Results", padding=5)
        save_frame.pack(side=tk.LEFT)
        
        ttk.Button(save_frame, text="Save Results", command=self.save_results).pack(pady=2)
        ttk.Button(save_frame, text="Save Figure", command=self.save_figure).pack(pady=2)
        
    def setup_content_area(self, parent):
        """Setup main content area with notebook"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Main plots tab
        self.plot_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.plot_frame, text="Analysis Plots")
        
        # Results tab
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="Results & Log")
        
        # Setup results text area
        self.results_text = scrolledtext.ScrolledText(self.results_frame, height=20)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def setup_status_bar(self, parent):
        """Setup status bar and progress indicator"""
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Select a data file to begin analysis")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Progress bar
        self.progress = ttk.Progressbar(parent, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(5, 0))
        
    def log_message(self, message: str):
        """Add message to results log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.results_text.see(tk.END)
        self.root.update()
        
    def browse_file(self):
        """Browse for data file"""
        filename = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.file_var.set(filename)
            
    def start_analysis(self):
        """Start the analysis in a separate thread"""
        if not self.file_var.get():
            messagebox.showerror("Error", "Please select a data file first")
            return
            
        # Start analysis in separate thread
        self.progress.start()
        self.status_var.set("Running analysis...")
        
        analysis_thread = threading.Thread(target=self.run_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()
        
    def run_analysis(self):
        """Run the complete analysis pipeline"""
        try:
            self.logger.info("Starting MAPopt analysis...", "🚀")
            
            # Load data
            data = self.data_loader.load_data(self.file_var.get())
            
            # Calculate COx correlations
            self.logger.info("Calculating COx correlations...", "📈")
            self.cox_time, self.cox_values = SignalProcessor.calculate_cox_correlations(data)
            
            # Calculate MAPopt series
            self.logger.info("Calculating MAPopt series (this may take a few minutes)...", "🎯")
            
            def progress_callback(pct):
                self.root.after(0, lambda: self.status_var.set(f"MAPopt calculation: {pct:.1f}%"))
                
            time_vector, mapopt_filled, all_fits_data = self.mapopt_calculator.calculate_mapopt_series(
                data, progress_callback
            )
            
            # Calculate deviation and burden
            self.logger.info("Calculating deviation and burden metrics...", "📊")
            self.burden_calculator.calculate_deviation_and_burden(data, time_vector, mapopt_filled)
            
            # Create plots
            self.logger.info("Creating visualization plots...", "🖼️")
            self.root.after(0, lambda: self.create_plots(data, time_vector, mapopt_filled))
            
            # Set initial time ranges
            self.root.after(0, lambda: self.start_var.set(time_vector[0]))
            self.root.after(0, lambda: self.end_var.set(time_vector[-1]))
            
            self.progress.stop()
            self.status_var.set("Analysis completed successfully")
            self.logger.success("Analysis completed successfully!")
            self.logger.info(f"Time range: {time_vector[0]:.2f} - {time_vector[-1]:.2f} hours", "📊")
            
        except Exception as e:
            self.progress.stop()
            self.status_var.set("Analysis failed")
            self.logger.error(f"Error during analysis: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Analysis Error", f"Error during analysis:\n{str(e)}"))
            
    def create_plots(self, data, time_vector, mapopt_filled):
        """Create the main analysis plots"""
        # Clear existing plots
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
            
        # Create plots using plot manager
        fig = self.plot_manager.create_main_analysis_plots(
            data, self.cox_time, self.cox_values, time_vector, mapopt_filled,
            self.burden_calculator.deviation,
            self.burden_calculator.outside_upper,
            self.burden_calculator.outside_lower,
            self.data_loader.subject_id
        )
        
        # Embed plot in GUI
        self.canvas = FigureCanvasTkAgg(fig, self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add navigation toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()
        
        # Initial burden calculation
        self.calculate_burden()
        
    def calculate_burden(self):
        """Calculate and display burden metrics"""
        if self.mapopt_calculator.time_vector is None:
            messagebox.showerror("Error", "No analysis data available")
            return
            
        try:
            t_start = self.start_var.get()
            t_end = self.end_var.get()
            
            # Validate inputs
            if t_start >= t_end:
                messagebox.showerror("Error", "Start time must be less than end time")
                return
                
            # Calculate burden metrics
            results = self.burden_calculator.calculate_burden_metrics(
                self.mapopt_calculator.time_vector, t_start, t_end
            )
            
            # Update plots with time indicators
            self.plot_manager.update_time_indicators(t_start, t_end)
            
            # Update title
            self.plot_manager.update_plot_title(
                self.data_loader.subject_id, t_start, t_end,
                results['time_burden'], results['area_burden_ratio']
            )
            
            # Log results
            self.logger.info("="*50)
            self.logger.info("BURDEN CALCULATION RESULTS", "📊")
            self.logger.info("="*50)
            self.logger.info(f"Time Period: {t_start:.2f} - {t_end:.2f} hours", "⏰")
            self.logger.info(f"Time Burden: {results['time_burden']:.1f}%", "📈")
            self.logger.info(f"Area Burden: {results['area_burden_ratio']:.1f}%", "📉")
            self.logger.info("="*50)
            
            # Store results
            self.last_burden_results = results
            
            # Refresh canvas
            self.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error calculating burden: {str(e)}")
            
    def show_curve_fits(self):
        """Show curve fits for a specific time point"""
        if self.mapopt_calculator.all_fits_data is None:
            messagebox.showerror("Error", "No analysis data available")
            return
            
        try:
            t_show = self.time_var.get()
            
            # Find nearest time point
            time_vector = self.mapopt_calculator.time_vector
            idx = np.argmin(np.abs(time_vector - t_show))
            actual_time = time_vector[idx]
            fits = self.mapopt_calculator.all_fits_data[idx]
            
            if not fits:
                messagebox.showwarning("Warning", f"No valid curve fits found at time {actual_time:.2f} hours.")
                return
                
            # Create curve fits dialog
            dialog = CurveFitsDialog(self.root, actual_time, fits, self.plot_manager)
            self.logger.info(f"Displayed curve fits for time {actual_time:.2f} hours ({len(fits)} fits)", "🔍")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error showing curve fits: {str(e)}")
            
    def show_data_summary(self):
        """Show data quality summary"""
        if self.data_loader.data is None:
            if not self.file_var.get():
                messagebox.showerror("Error", "Please select a data file first")
                return
            try:
                self.data_loader.load_data(self.file_var.get())
            except Exception as e:
                messagebox.showerror("Error", f"Error loading data: {str(e)}")
                return
                
        summary = self.data_loader.get_data_summary()
        
        self.logger.info("", "")
        self.logger.info("DATA SUMMARY", "📊")
        self.logger.info("="*50)
        self.logger.info(f"Duration: {summary['duration_hours']:.1f} hours", "📈")
        self.logger.info(f"Data points: {summary['data_points']}", "")
        self.logger.info(f"Sampling interval: {summary['sampling_interval_min']:.1f} minutes", "")
        
        map_min, map_max = summary['map_range']
        self.logger.info(f"MAP: {map_min:.1f}-{map_max:.1f} mmHg (σ={summary['map_std']:.1f})", "")
        
        rso2_min, rso2_max = summary['rso2_range']
        self.logger.info(f"rSO2: {rso2_min:.1f}-{rso2_max:.1f}% (σ={summary['rso2_std']:.1f})", "")
        
        if 'overall_correlation' in summary:
            self.logger.info(f"Overall MAP-rSO2 correlation: {summary['overall_correlation']:.3f}", "")
            
        self.logger.info("="*50)
        
    def save_results(self):
        """Save analysis results to files"""
        if self.last_burden_results is None:
            messagebox.showerror("Error", "No burden results to save. Calculate burden metrics first.")
            return
            
        try:
            # Get save directory
            save_dir = filedialog.askdirectory(title="Select directory to save results")
            if not save_dir:
                return
                
            saved_files = []
            
            # Save burden metrics
            burden_file = self.file_manager.save_burden_metrics(
                self.last_burden_results,
                self.data_loader.subject_id,
                self.data_loader.file_path,
                save_dir
            )
            saved_files.append(burden_file)
            
            # Save time series data
            timeseries_file = self.file_manager.save_timeseries_data(
                self.mapopt_calculator.time_vector,
                self.cox_time, self.cox_values,
                self.data_loader.data,
                self.mapopt_calculator.mapopt_filled,
                self.burden_calculator.deviation,
                self.burden_calculator.outside_bounds,
                self.data_loader.subject_id,
                save_dir
            )
            saved_files.append(timeseries_file)
            
            # Create manifest
            manifest_file = self.file_manager.create_results_manifest(
                save_dir, self.data_loader.subject_id, saved_files
            )
            
            self.logger.success(f"Results saved:", "💾")
            self.logger.info(f"   Burden metrics: {os.path.basename(burden_file)}", "📊")
            self.logger.info(f"   Time series: {os.path.basename(timeseries_file)}", "📈")
            
            messagebox.showinfo("Success", 
                f"Results saved successfully to:\n{save_dir}\n\nFiles:\n• {os.path.basename(burden_file)}\n• {os.path.basename(timeseries_file)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving results: {str(e)}")
            
    def save_figure(self):
        """Save current figure"""
        if not hasattr(self, 'canvas') or self.plot_manager.fig is None:
            messagebox.showerror("Error", "No figure to save")
            return
            
        try:
            filename = filedialog.asksaveasfilename(
                title="Save Figure",
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("PDF files", "*.pdf"),
                    ("SVG files", "*.svg"),
                    ("All files", "*.*")
                ]
            )
            
            if filename:
                self.plot_manager.save_figure(filename)
                self.logger.success(f"Figure saved: {os.path.basename(filename)}", "🖼️")
                messagebox.showinfo("Success", f"Figure saved successfully:\n{filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error saving figure: {str(e)}")


def run_gui():
    """Run the GUI application"""
    root = tk.Tk()
    app = MAPoptAnalysisGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop() 
