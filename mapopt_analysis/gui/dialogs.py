 
"""
Dialog windows for MAPopt Analysis GUI
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from typing import List, Dict, Any

from ..visualization.plots import PlotManager


class CurveFitsDialog:
    """Dialog window for displaying curve fits analysis"""
    
    def __init__(self, parent, actual_time: float, fits: List[Dict[str, Any]], plot_manager: PlotManager):
        self.window = tk.Toplevel(parent)
        self.window.title(f"Curve Fits at {actual_time:.2f} hours")
        self.window.geometry("1200x800")
        
        self.actual_time = actual_time
        self.fits = fits
        self.plot_manager = plot_manager
        
        self.create_widgets()
        self.create_plot()
        
    def create_widgets(self):
        """Create dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Info frame
        info_frame = ttk.LabelFrame(main_frame, text="Curve Fits Information", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Calculate statistics
        all_mapopts = [fit['mapopt'] for fit in self.fits]
        all_weights = [fit['weight'] for fit in self.fits]
        weighted_mapopt = np.sum(np.array(all_mapopts) * np.array(all_weights)) / np.sum(all_weights)
        
        # Display information
        ttk.Label(info_frame, text=f"Time Point: {self.actual_time:.2f} hours", 
                 font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=0, sticky='w', padx=5)
        ttk.Label(info_frame, text=f"Number of Fits: {len(self.fits)}", 
                 font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=1, sticky='w', padx=5)
        ttk.Label(info_frame, text=f"Weighted MAPopt: {weighted_mapopt:.1f} mmHg", 
                 font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=2, sticky='w', padx=5)
        
        # Plot frame
        self.plot_frame = ttk.Frame(main_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Save Figure", command=self.save_figure).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Export Data", command=self.export_data).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(side=tk.RIGHT)
        
    def create_plot(self):
        """Create curve fits plot"""
        try:
            fig = self.plot_manager.create_curve_fits_plot(self.actual_time, self.fits)
            
            # Embed plot in dialog
            canvas = FigureCanvasTkAgg(fig, self.plot_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Add navigation toolbar
            toolbar = NavigationToolbar2Tk(canvas, self.plot_frame)
            toolbar.update()
            
            self.canvas = canvas
            self.fig = fig
            
        except Exception as e:
            error_label = ttk.Label(self.plot_frame, text=f"Error creating plot: {str(e)}")
            error_label.pack(expand=True)
            
    def save_figure(self):
        """Save the curve fits figure"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                title="Save Curve Fits Figure",
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("PDF files", "*.pdf"),
                    ("SVG files", "*.svg"),
                    ("All files", "*.*")
                ]
            )
            
            if filename and hasattr(self, 'fig'):
                self.fig.savefig(filename, dpi=300, bbox_inches='tight')
                tk.messagebox.showinfo("Success", f"Figure saved successfully:\n{filename}")
                
        except Exception as e:
            tk.messagebox.showerror("Error", f"Error saving figure: {str(e)}")
            
    def export_data(self):
        """Export curve fits data to CSV"""
        try:
            from tkinter import filedialog
            import pandas as pd
            
            filename = filedialog.asksaveasfilename(
                title="Export Curve Fits Data",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                # Prepare data for export
                export_data = []
                for i, fit in enumerate(self.fits):
                    record = {
                        'Fit_Index': i,
                        'Window_minutes': fit['win_hr'] * 60,
                        'History_hours': fit['hist_hr'],
                        'MAPopt_mmHg': fit['mapopt'],
                        'Nadir_COx': fit['nadir_cox'],
                        'R_squared': fit['r2'],
                        'Weight': fit['weight']
                    }
                    export_data.append(record)
                    
                df = pd.DataFrame(export_data)
                df.to_csv(filename, index=False)
                tk.messagebox.showinfo("Success", f"Data exported successfully:\n{filename}")
                
        except Exception as e:
            tk.messagebox.showerror("Error", f"Error exporting data: {str(e)}")


class ProgressDialog:
    """Dialog for showing progress of long operations"""
    
    def __init__(self, parent, title: str = "Processing...", message: str = "Please wait..."):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("400x150")
        self.window.resizable(False, False)
        
        # Center the dialog
        self.window.transient(parent)
        self.window.grab_set()
        
        self.create_widgets(message)
        
    def create_widgets(self, message: str):
        """Create progress dialog widgets"""
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Message label
        self.message_var = tk.StringVar(value=message)
        message_label = ttk.Label(main_frame, textvariable=self.message_var, font=('TkDefaultFont', 10))
        message_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=300)
        self.progress.pack(pady=(0, 10))
        self.progress.start()
        
        # Status label
        self.status_var = tk.StringVar(value="Initializing...")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, font=('TkDefaultFont', 9))
        status_label.pack()
        
    def update_status(self, status: str):
        """Update the status message"""
        self.status_var.set(status)
        self.window.update()
        
    def update_message(self, message: str):
        """Update the main message"""
        self.message_var.set(message)
        self.window.update()
        
    def close(self):
        """Close the progress dialog"""
        self.progress.stop()
        self.window.destroy()


class AboutDialog:
    """About dialog with application information"""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("About MAPopt Analysis Tool")
        self.window.geometry("500x400")
        self.window.resizable(False, False)
        
        # Center the dialog
        self.window.transient(parent)
        self.window.grab_set()
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create about dialog widgets"""
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="MAPopt Analysis Tool", 
                               font=('TkDefaultFont', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Version
        version_label = ttk.Label(main_frame, text="Version 1.0.0", 
                                 font=('TkDefaultFont', 12))
        version_label.pack(pady=(0, 20))
        
        # Description
        description = """
A biomedical signal analysis tool for calculating optimal Mean Arterial Pressure (MAP) 
and burden metrics from cerebral autoregulation data.

Features:
• Automated MAPopt calculation using curve fitting
• COx correlation analysis
• Burden metrics calculation
• Interactive visualization
• Results export functionality

This tool analyzes MAP and rSO2 data to determine optimal blood pressure targets 
for individual patients based on cerebral autoregulation patterns.
        """
        
        desc_text = tk.Text(main_frame, wrap=tk.WORD, height=12, width=50)
        desc_text.insert(tk.END, description.strip())
        desc_text.config(state=tk.DISABLED, bg=main_frame.cget('bg'))
        desc_text.pack(pady=(0, 20), fill=tk.BOTH, expand=True)
        
        # Credits
        credits_label = ttk.Label(main_frame, text="Developed for biomedical research applications", 
                                 font=('TkDefaultFont', 10, 'italic'))
        credits_label.pack(pady=(0, 20))
        
        # Close button
        ttk.Button(main_frame, text="Close", command=self.window.destroy).pack()


class SettingsDialog:
    """Settings dialog for application preferences"""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("400x300")
        self.window.resizable(False, False)
        
        # Center the dialog
        self.window.transient(parent)
        self.window.grab_set()
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create settings dialog widgets"""
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Analysis Settings
        analysis_frame = ttk.LabelFrame(main_frame, text="Analysis Settings", padding=10)
        analysis_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Parallel processing
        ttk.Label(analysis_frame, text="Max CPU Cores:").grid(row=0, column=0, sticky='w', pady=2)
        self.cores_var = tk.IntVar(value=8)
        cores_spin = ttk.Spinbox(analysis_frame, from_=1, to=16, textvariable=self.cores_var, width=10)
        cores_spin.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=2)
        
        # Outlier threshold
        ttk.Label(analysis_frame, text="Outlier Threshold (σ):").grid(row=1, column=0, sticky='w', pady=2)
        self.outlier_var = tk.DoubleVar(value=3.0)
        outlier_spin = ttk.Spinbox(analysis_frame, from_=1.0, to=5.0, increment=0.1, 
                                  textvariable=self.outlier_var, width=10)
        outlier_spin.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)
        
        # Plot Settings
        plot_frame = ttk.LabelFrame(main_frame, text="Plot Settings", padding=10)
        plot_frame.pack(fill=tk.X, pady=(0, 10))
        
        # DPI
        ttk.Label(plot_frame, text="Figure DPI:").grid(row=0, column=0, sticky='w', pady=2)
        self.dpi_var = tk.IntVar(value=300)
        dpi_combo = ttk.Combobox(plot_frame, textvariable=self.dpi_var, 
                                values=[150, 300, 600], width=10, state="readonly")
        dpi_combo.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=2)
        
        # File Settings
        file_frame = ttk.LabelFrame(main_frame, text="File Settings", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Auto-save
        self.autosave_var = tk.BooleanVar(value=False)
        autosave_check = ttk.Checkbutton(file_frame, text="Auto-save results", 
                                        variable=self.autosave_var)
        autosave_check.pack(anchor='w')
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="OK", command=self.apply_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_defaults).pack(side=tk.LEFT)
        
    def apply_settings(self):
        """Apply the settings"""
        # Here you would typically save settings to a config file
        # and apply them to the application
        tk.messagebox.showinfo("Settings", "Settings applied successfully!")
        self.window.destroy()
        
    def reset_defaults(self):
        """Reset settings to defaults"""
        self.cores_var.set(8)
        self.outlier_var.set(3.0)
        self.dpi_var.set(300)
        self.autosave_var.set(False)