"""
Main entry point for MAPopt Analysis Tool
"""

import sys
import argparse
import tkinter as tk
from pathlib import Path

# Add the package directory to Python path
package_dir = Path(__file__).parent.parent
sys.path.insert(0, str(package_dir))

from mapopt_analysis.gui.main_window import run_gui
from mapopt_analysis.core.data_loader import DataLoader
from mapopt_analysis.core.signal_processing import SignalProcessor
from mapopt_analysis.core.mapopt_calculator import MAPoptCalculator
from mapopt_analysis.core.burden_metrics import BurdenCalculator
from mapopt_analysis.utils.file_io import FileManager
from mapopt_analysis.utils.logger import get_logger, set_log_level
import mapopt_analysis


def run_cli_analysis(data_file: str, output_dir: str = None, time_start: float = None, time_end: float = None):
    """
    Run analysis in command-line mode
    
    Args:
        data_file: Path to input data file
        output_dir: Directory to save results (optional)
        time_start: Start time for burden analysis (optional)
        time_end: End time for burden analysis (optional)
    """
    logger = get_logger()
    
    try:
        logger.info("Starting command-line MAPopt analysis...", "🚀")
        
        # Initialize components
        data_loader = DataLoader()
        mapopt_calculator = MAPoptCalculator()
        burden_calculator = BurdenCalculator()
        file_manager = FileManager()
        
        # Load data
        logger.info(f"Loading data from: {data_file}", "📂")
        data = data_loader.load_data(data_file)
        
        # Calculate COx correlations
        logger.info("Calculating COx correlations...", "📈")
        cox_time, cox_values = SignalProcessor.calculate_cox_correlations(data)
        
        # Calculate MAPopt series
        logger.info("Calculating MAPopt series...", "🎯")
        time_vector, mapopt_filled, all_fits_data = mapopt_calculator.calculate_mapopt_series(data)
        
        # Calculate deviation and burden
        logger.info("Calculating deviation and burden metrics...", "📊")
        burden_calculator.calculate_deviation_and_burden(data, time_vector, mapopt_filled)
        
        # Set time range for burden calculation
        if time_start is None:
            time_start = time_vector[0]
        if time_end is None:
            time_end = time_vector[-1]
            
        # Calculate burden metrics
        burden_results = burden_calculator.calculate_burden_metrics(time_vector, time_start, time_end)
        
        # Display results
        logger.info("="*50)
        logger.info("ANALYSIS RESULTS", "📊")
        logger.info("="*50)
        logger.info(f"Subject ID: {data_loader.subject_id}", "👤")
        logger.info(f"Time Range: {time_start:.2f} - {time_end:.2f} hours", "⏰")
        logger.info(f"Time Burden: {burden_results['time_burden']:.1f}%", "📈")
        logger.info(f"Area Burden: {burden_results['area_burden_ratio']:.1f}%", "📉")
        logger.info("="*50)
        
        # Save results if output directory specified
        if output_dir:
            logger.info(f"Saving results to: {output_dir}", "💾")
            
            # Create output directory if it doesn't exist
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Save files
            burden_file = file_manager.save_burden_metrics(
                burden_results, data_loader.subject_id, data_file, output_dir
            )
            
            timeseries_file = file_manager.save_timeseries_data(
                time_vector, cox_time, cox_values, data, mapopt_filled,
                burden_calculator.deviation, burden_calculator.outside_bounds,
                data_loader.subject_id, output_dir
            )
            
            logger.success(f"Results saved successfully!", "✅")
            logger.info(f"   Burden metrics: {Path(burden_file).name}", "📊")
            logger.info(f"   Time series: {Path(timeseries_file).name}", "📈")
            
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="MAPopt Analysis Tool - Biomedical signal analysis for optimal MAP calculation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run GUI mode
  mapopt-analysis
  
  # Run CLI analysis
  mapopt-analysis --file data.csv --output results/
  
  # Run CLI with specific time range
  mapopt-analysis --file data.csv --output results/ --start 2.0 --end 20.0
  
  # Enable debug logging
  mapopt-analysis --file data.csv --verbose
        """
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version=f'MAPopt Analysis Tool v{mapopt_analysis.__version__}'
    )
    
    parser.add_argument(
        '--file', '-f',
        type=str,
        help='Input data file (CSV or TXT format)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output directory for results'
    )
    
    parser.add_argument(
        '--start', '-s',
        type=float,
        help='Start time for burden analysis (hours)'
    )
    
    parser.add_argument(
        '--end', '-e',
        type=float,
        help='End time for burden analysis (hours)'
    )
    
    parser.add_argument(
        '--gui',
        action='store_true',
        help='Force GUI mode (default when no file specified)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose debug logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        import logging
        set_log_level(logging.DEBUG)
    
    # Determine mode
    if args.file and not args.gui:
        # Command-line mode
        run_cli_analysis(
            data_file=args.file,
            output_dir=args.output,
            time_start=args.start,
            time_end=args.end
        )
    else:
        # GUI mode
        try:
            run_gui()
        except KeyboardInterrupt:
            print("\nApplication terminated by user")
            sys.exit(0)
        except Exception as e:
            print(f"Error starting GUI: {e}")
            print("Make sure you have tkinter installed and a display available")
            sys.exit(1)


if __name__ == "__main__":
    main() 
