"""
Configuration constants for MAPopt Analysis Tool
"""

import numpy as np

# Analysis Parameters
MAP_BINS = np.arange(40, 105, 5)
MAP_BIN_CENTERS = MAP_BINS[:-1] + 2.5
COX_WINDOWS_MIN = [3, 5, 10, 20, 30, 60, 90, 120]
HISTORY_WINDOWS_HR = [1, 2, 3, 4, 5, 6, 7, 8, 12]

# Data Validation
MAP_MIN = 0
MAP_MAX = 150
MAP_OPT_MIN = 40
MAP_OPT_MAX = 90
DEVIATION_MIN = -50
DEVIATION_MAX = 50

# Time Parameters
TIME_STEP_MIN = 1/60  # 1 minute in hours
BURDEN_BOUNDS = 5  # mmHg deviation bounds

# Filtering Parameters
OUTLIER_THRESHOLD = 3  # Z-score threshold
MEDIAN_FILTER_SIZE = 3
ROLLING_WINDOW_SIZE = 5
SAVGOL_WINDOW = 11
SAVGOL_ORDER = 3

# Parallel Processing
MAX_CORES = 8
CHUNK_SIZE = 25

# GUI Settings
WINDOW_TITLE = "MAPopt Analysis Tool - v1.0"
WINDOW_SIZE = "1400x900"
PLOT_DPI = 300

# File Extensions
SUPPORTED_EXTENSIONS = [".csv", ".txt"]
OUTPUT_FORMATS = [".png", ".pdf", ".svg"]

# Correlation Thresholds
COX_UPPER_THRESHOLD = 0.3
COX_LOWER_THRESHOLD = -0.3
COX_WEIGHT_THRESHOLD = 0.3
MIN_CORRELATION_POINTS = 3
MIN_DATA_POINTS = 10
MIN_SEGMENT_POINTS = 60

# Fisher Transform Bounds
FISHER_BOUNDS = 0.999 
