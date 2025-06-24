 
"""
Simple logging utilities for MAPopt Analysis Tool
"""

import logging
import sys
from datetime import datetime
from typing import Optional, Callable


class AnalysisLogger:
    """Simple logger for analysis operations"""
    
    def __init__(self, name: str = "MAPoptAnalysis", level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            self._setup_console_handler()
            
        self.gui_callback: Optional[Callable] = None
        
    def _setup_console_handler(self):
        """Setup console logging handler"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        
    def set_gui_callback(self, callback: Callable[[str], None]):
        """Set callback function for GUI logging"""
        self.gui_callback = callback
        
    def info(self, message: str, emoji: str = "ℹ️"):
        """Log info message"""
        formatted_message = f"{emoji} {message}"
        self.logger.info(message)
        
        if self.gui_callback:
            self.gui_callback(formatted_message)
            
    def error(self, message: str, emoji: str = "❌"):
        """Log error message"""
        formatted_message = f"{emoji} {message}"
        self.logger.error(message)
        
        if self.gui_callback:
            self.gui_callback(formatted_message)
            
    def warning(self, message: str, emoji: str = "⚠️"):
        """Log warning message"""
        formatted_message = f"{emoji} {message}"
        self.logger.warning(message)
        
        if self.gui_callback:
            self.gui_callback(formatted_message)
            
    def success(self, message: str, emoji: str = "✅"):
        """Log success message"""
        formatted_message = f"{emoji} {message}"
        self.logger.info(message)
        
        if self.gui_callback:
            self.gui_callback(formatted_message)
            
    def debug(self, message: str, emoji: str = "🔍"):
        """Log debug message"""
        formatted_message = f"{emoji} {message}"
        self.logger.debug(message)
        
        if self.gui_callback:
            self.gui_callback(formatted_message)


class ProgressTracker:
    """Simple progress tracking for long operations"""
    
    def __init__(self, total_steps: int, logger: AnalysisLogger):
        self.total_steps = total_steps
        self.current_step = 0
        self.logger = logger
        self.start_time = datetime.now()
        
    def update(self, step: int, message: str = ""):
        """Update progress"""
        self.current_step = step
        progress_pct = (step / self.total_steps) * 100
        
        if message:
            self.logger.info(f"{message} ({progress_pct:.1f}%)")
        else:
            self.logger.info(f"Progress: {progress_pct:.1f}%")
            
    def increment(self, message: str = ""):
        """Increment progress by one step"""
        self.update(self.current_step + 1, message)
        
    def finish(self, message: str = "Operation completed"):
        """Mark operation as finished"""
        elapsed = datetime.now() - self.start_time
        self.logger.success(f"{message} (took {elapsed.total_seconds():.1f}s)")


# Global logger instance
_logger = AnalysisLogger()

def get_logger() -> AnalysisLogger:
    """Get the global logger instance"""
    return _logger

def set_log_level(level: int):
    """Set logging level"""
    _logger.logger.setLevel(level)

def log_info(message: str, emoji: str = "ℹ️"):
    """Quick info logging function"""
    _logger.info(message, emoji)

def log_error(message: str, emoji: str = "❌"):
    """Quick error logging function"""
    _logger.error(message, emoji)

def log_success(message: str, emoji: str = "✅"):
    """Quick success logging function"""
    _logger.success(message, emoji)