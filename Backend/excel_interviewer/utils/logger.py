"""
Logging configuration and utilities for Excel Mock Interviewer

This module provides centralized logging configuration with structured logging,
file rotation, and different log levels for different components.
"""
import logging
import logging.handlers
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import traceback

from excel_interviewer.utils.config import settings

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if present
        if hasattr(record, 'interview_id'):
            log_entry["interview_id"] = record.interview_id
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'response_time'):
            log_entry["response_time"] = record.response_time
        
        return json.dumps(log_entry)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        """Format with colors for console output"""
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Create formatted message
        formatted = f"{level_color}[{record.levelname}]{reset_color} {timestamp} - {record.name} - {record.getMessage()}"
        
        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted

def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    json_format: bool = False,
    enable_console: bool = True
) -> None:
    """
    Setup application logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file path (None to disable file logging)
        json_format: Use JSON formatting for structured logs
        enable_console: Enable console logging
    """
    # Use settings if not provided
    log_level = log_level or settings.log_level
    log_file = log_file or settings.log_file
    
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        
        if json_format:
            console_formatter = JSONFormatter()
        else:
            console_formatter = ColoredFormatter()
        
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        try:
            file_handler = logging.handlers.TimedRotatingFileHandler(
                filename=log_file,
                when='midnight',
                interval=1,
                backupCount=30,  # Keep 30 days of logs
                encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            
            # Always use JSON format for file logs
            file_formatter = JSONFormatter()
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")
    
    # Configure specific loggers
    configure_component_loggers()
    
    # Suppress noisy third-party loggers
    suppress_noisy_loggers()
    
    # Log initial message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}, JSON: {json_format}")

def configure_component_loggers():
    """Configure loggers for different application components"""
    
    # API request logger
    api_logger = logging.getLogger("excel_interviewer.api")
    api_logger.setLevel(logging.INFO)
    
    # Service loggers
    service_logger = logging.getLogger("excel_interviewer.services")
    service_logger.setLevel(logging.INFO)
    
    # Database logger
    db_logger = logging.getLogger("excel_interviewer.models")
    db_logger.setLevel(logging.WARNING)  # Only warnings and errors
    
    # SQLAlchemy logger (can be noisy)
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    if settings.database_echo:
        sqlalchemy_logger.setLevel(logging.INFO)
    else:
        sqlalchemy_logger.setLevel(logging.WARNING)

def suppress_noisy_loggers():
    """Suppress noisy third-party loggers"""
    noisy_loggers = [
        "urllib3.connectionpool",
        "requests.packages.urllib3",
        "openai._base_client",
        "httpx",
        "asyncio"
    ]
    
    for logger_name in noisy_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)

class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter for adding context information"""
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any]):
        super().__init__(logger, extra)
    
    def process(self, msg, kwargs):
        """Add extra context to log records"""
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        kwargs['extra'].update(self.extra)
        return msg, kwargs

def get_context_logger(name: str, **context) -> LoggerAdapter:
    """Get a logger with additional context information"""
    logger = get_logger(name)
    return LoggerAdapter(logger, context)

def log_performance(func):
    """Decorator for logging function performance"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = datetime.utcnow()
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.debug(
                f"Function {func.__name__} completed in {duration:.3f}s",
                extra={"function": func.__name__, "duration": duration}
            )
            return result
            
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.error(
                f"Function {func.__name__} failed after {duration:.3f}s: {e}",
                extra={"function": func.__name__, "duration": duration, "error": str(e)},
                exc_info=True
            )
            raise
    
    return wrapper

def log_api_request(request_id: str, method: str, path: str, status_code: int, duration: float):
    """Log API request with structured format"""
    logger = get_logger("excel_interviewer.api")
    
    log_level = logging.INFO
    if status_code >= 500:
        log_level = logging.ERROR
    elif status_code >= 400:
        log_level = logging.WARNING
    
    logger.log(
        log_level,
        f"{method} {path} - {status_code} ({duration:.3f}s)",
        extra={
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time": duration,
            "log_type": "api_request"
        }
    )

def log_interview_event(interview_id: str, event_type: str, message: str, **extra_data):
    """Log interview-related events"""
    logger = get_logger("excel_interviewer.interview")
    
    logger.info(
        message,
        extra={
            "interview_id": interview_id,
            "event_type": event_type,
            "log_type": "interview_event",
            **extra_data
        }
    )

def log_evaluation_event(interview_id: str, question_id: str, score: float, evaluation_time: float, **extra_data):
    """Log evaluation events"""
    logger = get_logger("excel_interviewer.evaluation")
    
    logger.info(
        f"Response evaluated - Score: {score}/100, Time: {evaluation_time:.3f}s",
        extra={
            "interview_id": interview_id,
            "question_id": question_id,
            "score": score,
            "evaluation_time": evaluation_time,
            "log_type": "evaluation_event",
            **extra_data
        }
    )

class ContextualLogger:
    """Logger with automatic context management"""
    
    def __init__(self, name: str, default_context: Dict[str, Any] = None):
        self.logger = get_logger(name)
        self.default_context = default_context or {}
    
    def _log_with_context(self, level: int, message: str, **context):
        """Log with merged context"""
        merged_context = {**self.default_context, **context}
        self.logger.log(level, message, extra=merged_context)
    
    def debug(self, message: str, **context):
        self._log_with_context(logging.DEBUG, message, **context)
    
    def info(self, message: str, **context):
        self._log_with_context(logging.INFO, message, **context)
    
    def warning(self, message: str, **context):
        self._log_with_context(logging.WARNING, message, **context)
    
    def error(self, message: str, **context):
        self._log_with_context(logging.ERROR, message, **context)

def get_contextual_logger(name: str, **default_context) -> ContextualLogger:
    """Get a contextual logger with default context"""
    return ContextualLogger(name, default_context)

def configure_production_logging():
    """Configure logging for production environment"""
    setup_logging(
        log_level="INFO",
        log_file="logs/excel_interviewer.log",
        json_format=True,
        enable_console=False
    )

def configure_development_logging():
    """Configure logging for development environment"""
    setup_logging(
        log_level="DEBUG",
        log_file="excel_interviewer_dev.log",
        json_format=False,
        enable_console=True
    )

def get_log_stats() -> Dict[str, Any]:
    """Get logging statistics"""
    stats = {
        "loggers": {},
        "handlers": [],
        "log_level": logging.getLevelName(logging.getLogger().level)
    }
    
    # Get all loggers
    for name, logger in logging.Logger.manager.loggerDict.items():
        if isinstance(logger, logging.Logger):
            stats["loggers"][name] = {
                "level": logging.getLevelName(logger.level),
                "handlers": len(logger.handlers),
                "disabled": logger.disabled
            }
    
    # Get root logger handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        stats["handlers"].append({
            "type": type(handler).__name__,
            "level": logging.getLevelName(handler.level),
            "formatter": type(handler.formatter).__name__ if handler.formatter else None
        })
    
    return stats

# Initialize logging on module import
if not logging.getLogger().handlers:
    try:
        if settings.environment == "production":
            configure_production_logging()
        else:
            configure_development_logging()
    except Exception as e:
        # Fallback to basic logging if configuration fails
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        print(f"Warning: Failed to configure logging: {e}")
