import os
import sys
import logging
import time
import datetime
from typing import Dict, Optional, Any, List, Union
import json
import traceback
import threading

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to console output."""
    
    # ANSI color codes
    COLORS = {
        'RESET': '\033[0m',
        'BLACK': '\033[30m',
        'RED': '\033[31m',
        'GREEN': '\033[32m',
        'YELLOW': '\033[33m',
        'BLUE': '\033[34m',
        'MAGENTA': '\033[35m',
        'CYAN': '\033[36m',
        'WHITE': '\033[37m',
        'BOLD': '\033[1m',
        'UNDERLINE': '\033[4m'
    }
    
    # Color mapping for log levels
    LEVEL_COLORS = {
        logging.DEBUG: COLORS['BLUE'],
        logging.INFO: COLORS['GREEN'],
        logging.WARNING: COLORS['YELLOW'],
        logging.ERROR: COLORS['RED'],
        logging.CRITICAL: COLORS['RED'] + COLORS['BOLD']
    }
    
    def format(self, record):
        """Format log record with colors."""
        # Save original format
        orig_format = self._style._fmt
        
        # Add color based on level
        if record.levelno in self.LEVEL_COLORS:
            color = self.LEVEL_COLORS[record.levelno]
            reset = self.COLORS['RESET']
            
            # Add color to levelname
            colored_levelname = f"{color}{record.levelname}{reset}"
            record.levelname = colored_levelname
            
            # Use color for entire message in case of error/critical
            if record.levelno >= logging.ERROR:
                self._style._fmt = f"{color}{orig_format}{reset}"
        
        # Format the record
        result = super().format(record)
        
        # Restore original format
        self._style._fmt = orig_format
        
        return result

class JsonFormatter(logging.Formatter):
    """Formatter that outputs log records as JSON objects."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'lineno': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if present
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data)

class AinaLogger:
    """
    Advanced logging system for Aina.
    Provides structured logging with multiple outputs and formats.
    """
    
    def __init__(self, 
                name: str = 'aina', 
                log_dir: str = 'logs',
                console_level: int = logging.INFO,
                file_level: int = logging.DEBUG,
                use_json: bool = False,
                use_colors: bool = True):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
            log_dir: Directory for log files
            console_level: Logging level for console output
            file_level: Logging level for file output
            use_json: Whether to use JSON format for file logs
            use_colors: Whether to use colored output in console
        """
        self.name = name
        self.log_dir = log_dir
        self.console_level = console_level
        self.file_level = file_level
        self.use_json = use_json
        self.use_colors = use_colors
        
        # Create log directory
        os.makedirs(log_dir, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)  # Capture all levels
        self.logger.propagate = False  # Don't propagate to parent loggers
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Setup handlers
        self._setup_console_handler()
        self._setup_file_handler()
        
        self.logger.info(f"Logger initialized: {name}")
    
    def _setup_console_handler(self):
        """Setup console handler."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.console_level)
        
        # Format: [2023-03-15 14:30:45] [INFO] Message
        if self.use_colors:
            formatter = ColoredFormatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self):
        """Setup file handler."""
        # Generate filename with date
        date_str = time.strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"{self.name}_{date_str}.log")
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(self.file_level)
        
        # Choose formatter based on configuration
        if self.use_json:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] [%(name)s.%(module)s:%(lineno)d] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def get_logger(self):
        """Get the configured logger instance."""
        return self.logger
    
    def debug(self, message, *args, **kwargs):
        """Log a debug message."""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        """Log an info message."""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        """Log a warning message."""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        """Log an error message."""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        """Log a critical message."""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message, *args, **kwargs):
        """Log an exception."""
        self.logger.exception(message, *args, **kwargs)
    
    def log_with_context(self, level, message, context=None, *args, **kwargs):
        """
        Log a message with additional context.
        
        Args:
            level: Logging level
            message: Log message
            context: Additional context dictionary
        """
        if context:
            # Create a copy of the record to add extra context
            extra = {'extra': context}
            self.logger.log(level, message, extra=extra, *args, **kwargs)
        else:
            self.logger.log(level, message, *args, **kwargs)

# Global logger instance
_default_logger = None

def get_logger(name: str = 'aina', **kwargs) -> AinaLogger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name
        **kwargs: Additional configuration parameters
        
    Returns:
        AinaLogger instance
    """
    global _default_logger
    
    if _default_logger is None or _default_logger.name != name:
        _default_logger = AinaLogger(name=name, **kwargs)
    
    return _default_logger

# Module-level convenience functions
def debug(message, *args, **kwargs):
    """Log a debug message using the default logger."""
    get_logger().debug(message, *args, **kwargs)

def info(message, *args, **kwargs):
    """Log an info message using the default logger."""
    get_logger().info(message, *args, **kwargs)

def warning(message, *args, **kwargs):
    """Log a warning message using the default logger."""
    get_logger().warning(message, *args, **kwargs)

def error(message, *args, **kwargs):
    """Log an error message using the default logger."""
    get_logger().error(message, *args, **kwargs)

def critical(message, *args, **kwargs):
    """Log a critical message using the default logger."""
    get_logger().critical(message, *args, **kwargs)

def exception(message, *args, **kwargs):
    """Log an exception using the default logger."""
    get_logger().exception(message, *args, **kwargs)