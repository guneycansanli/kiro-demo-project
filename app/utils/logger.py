"""
Logging Utilities

This module provides logging configuration and middleware.
"""

import logging
import json
import uuid
import sys
import traceback
from datetime import datetime, timezone
from flask import g, request


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON.
        
        Args:
            record: LogRecord instance
            
        Returns:
            str: JSON-formatted log entry
        """
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'level': record.levelname,
            'message': record.getMessage(),
        }
        
        # Add request ID if available (only when in Flask app context)
        try:
            if hasattr(g, 'request_id'):
                log_entry['request_id'] = g.request_id
        except RuntimeError:
            # Outside of application context, skip request ID
            pass
        
        # Add extra fields from record
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'path'):
            log_entry['path'] = record.path
        if hasattr(record, 'remote_addr'):
            log_entry['remote_addr'] = record.remote_addr
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': ''.join(traceback.format_exception(*record.exc_info))
            }
        
        return json.dumps(log_entry)


def setup_logging(app):
    """Configure logging for the application.
    
    Args:
        app: Flask application instance
    """
    log_level = getattr(logging, app.config['LOG_LEVEL'].upper(), logging.INFO)
    
    # Create handler that writes to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(JSONFormatter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = []  # Clear existing handlers
    root_logger.addHandler(handler)
    
    # Configure app logger
    app.logger.setLevel(log_level)
    app.logger.handlers = []  # Clear existing handlers
    app.logger.addHandler(handler)
    app.logger.propagate = False


def request_id_middleware():
    """Generate unique request ID for each request."""
    g.request_id = str(uuid.uuid4())
    g.request_start_time = datetime.now(timezone.utc)


def request_logging_middleware():
    """Log incoming requests with details."""
    logger = logging.getLogger(__name__)
    logger.info(
        'Incoming request',
        extra={
            'request_id': g.get('request_id', 'unknown'),
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr
        }
    )


def log_error(error, context=None):
    """Log errors with stack traces and context.
    
    Args:
        error: Exception instance
        context: Optional dictionary with additional context
    """
    logger = logging.getLogger(__name__)
    
    extra = {
        'request_id': g.get('request_id', 'unknown'),
    }
    
    # Add request context if available
    if hasattr(request, 'method'):
        extra['method'] = request.method
        extra['path'] = request.path
        extra['remote_addr'] = request.remote_addr
    
    # Add custom context
    if context:
        extra.update(context)
    
    logger.error(
        f'Error occurred: {str(error)}',
        exc_info=True,
        extra=extra
    )
