import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if hasattr(record, 'levelname') and record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'exc_info', 'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)

class Logger:
    """Enhanced logger with multiple handlers and configurations"""
    
    _instances = {}
    
    def __new__(cls, name: str = __name__):
        if name not in cls._instances:
            cls._instances[name] = super().__new__(cls)
        return cls._instances[name]
    
    def __init__(self, name: str = __name__):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup different log handlers"""
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = CustomFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for general logs
        self._setup_file_handler()
        
        # Error file handler
        self._setup_error_handler()
        
        # JSON file handler for structured logs
        self._setup_json_handler()
    
    def _setup_file_handler(self):
        """Setup general file handler"""
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(
            logs_dir / f'app_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def _setup_error_handler(self):
        """Setup error-specific file handler"""
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        error_handler = logging.FileHandler(
            logs_dir / f'errors_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n'
            'Exception: %(exc_info)s\n' + '-'*50,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)
    
    def _setup_json_handler(self):
        """Setup JSON file handler for structured logging"""
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        json_handler = logging.FileHandler(
            logs_dir / f'structured_{datetime.now().strftime("%Y%m%d")}.jsonl',
            encoding='utf-8'
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(json_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        extra = kwargs
        self.logger.debug(message, extra=extra)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        extra = kwargs
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        extra = kwargs
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        extra = kwargs
        self.logger.error(message, extra=extra, exc_info=True)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        extra = kwargs
        self.logger.critical(message, extra=extra, exc_info=True)
    
    def log_scraper_activity(self, scraper_name: str, query: str, results_count: int, duration: float):
        """Log scraper activity with structured data"""
        self.info(
            f"Scraper completed: {scraper_name}",
            scraper=scraper_name,
            query=query,
            results_count=results_count,
            duration_seconds=duration,
            activity_type="scraping"
        )
    
    def log_sentiment_analysis(self, text_length: int, sentiment: str, score: float, processing_time: float):
        """Log sentiment analysis activity"""
        self.info(
            f"Sentiment analysis completed",
            text_length=text_length,
            sentiment=sentiment,
            sentiment_score=score,
            processing_time_ms=processing_time * 1000,
            activity_type="sentiment_analysis"
        )
    
    def log_database_operation(self, operation: str, table: str, records_affected: int):
        """Log database operations"""
        self.info(
            f"Database operation: {operation}",
            operation=operation,
            table=table,
            records_affected=records_affected,
            activity_type="database"
        )
    
    def log_api_call(self, api_name: str, endpoint: str, status_code: int, response_time: float):
        """Log API call details"""
        self.info(
            f"API call: {api_name}",
            api_name=api_name,
            endpoint=endpoint,
            status_code=status_code,
            response_time_ms=response_time * 1000,
            activity_type="api_call"
        )

def setup_logger(name: str = __name__, level: int = logging.INFO) -> Logger:
    """Setup and return logger instance"""
    return Logger(name)

def get_logger(name: str = __name__) -> Logger:
    """Get existing logger instance"""
    return Logger(name)

# Performance monitoring decorator
def log_performance(logger_name: str = __name__):
    """Decorator to log function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            logger = get_logger(logger_name)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"Function completed: {func.__name__}",
                    function=func.__name__,
                    duration_seconds=duration,
                    success=True,
                    activity_type="performance"
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Function failed: {func.__name__}",
                    function=func.__name__,
                    duration_seconds=duration,
                    error=str(e),
                    success=False,
                    activity_type="performance"
                )
                raise
        return wrapper
    return decorator