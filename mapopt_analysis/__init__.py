 
"""
MAPopt Analysis Tool

A biomedical signal analysis application for analyzing MAP and rSO2 data
to calculate optimal MAP and burden metrics.
"""

__version__ = "1.0.0"
__author__ = "Subrat Bastola"
__email__ = "subratbastola@gmail.com"

from .core.data_loader import DataLoader
from .core.signal_processing import SignalProcessor
from .core.mapopt_calculator import MAPoptCalculator
from .core.burden_metrics import BurdenCalculator
from .visualization.plots import PlotManager
from .utils.file_io import FileManager

__all__ = [
    "DataLoader",
    "SignalProcessor", 
    "MAPoptCalculator",
    "BurdenCalculator",
    "PlotManager",
    "FileManager"
]