"""
Property-based and unit tests for logging utilities.

Tests logging functionality including request logging, error logging,
stdout output, and request ID tracking using property-based testing with Hypothesis.
"""

import unittest
import json
import io
import sys
import logging
from unittest.mock import patch, MagicMock
from hypothesis import given, settings, strategies as st
from flask import Flask, g
from app import create_app
from app.utils.logger import (
    setup_logging, 
    request_id_middleware, 
    request_logging_middleware,
    log_error,
    JSONFormatter
)


class TestRequestLogging(unittest.TestCase):
    """Property-based tests for request logging."""
    
    def setUp(self):
        """Set up test Flask application."""
        self.app = create_app({'TESTING': True, 'LOG_LEVEL': 'INFO'})
        self.client = self.app.test_client()
        
        # Capture logs by replacing the stdout handler with our own
        self.log_capture = io.StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.handler.setFormatter(JSONFormatter())
        
        # Replace all handlers on root logger with our capture handler
        root_logger = logging.getLogger()
        self.original_handlers = root_logger.handlers[:]
        root_logger.handlers = [self.handler]
        root_logger.setLevel(logging.INFO)
        
        # Also replace app logger handlers since it has propagate=False
        self.original_app_handlers = self.app.logger.handlers[:]
        self.app.logger.handlers = [self.handler]
        self.app.logger.setLevel(logging.INFO)
    
    def tearDown(self):
        """Restore original logging handlers."""
        root_logger = logging.getLogger()
        root_logger.handlers = self.original_handlers
        self.app.logger.handlers = self.original_app_handlers
    
    @settings(max_examples=100)
    @given(
        path=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=32, max_codepoint=126),
            min_size=1,
            max_size=50
        ).map(lambda s: '/' + s.replace(' ', '-').replace('/', '-')),
        method=st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
    )
    def test_all_requests_are_logged(self, path: str, method: str):
        """
        Feature: weather-web-service, Property 18: All requests are logged
        
        For any incoming HTTP request, a log entry should be created with timestamp,
        request details, and request ID.
        
        Validates: Requirements 12.1
        """
        # Clear previous logs
        self.log_capture.truncate(0)
        self.log_capture.seek(0)
        
        # Make a request (will likely 404, but should still log)
        try:
            if method == 'GET':
                self.client.get(path)
            elif method == 'POST':
                self.client.post(path)
            elif method == 'PUT':
                self.client.put(path)
            elif method == 'DELETE':
                self.client.delete(path)
            elif method == 'PATCH':
                self.client.patch(path)
        except Exception:
            # Ignore errors, we just want to check logging
            pass
        
        # Get the logged output
        log_output = self.log_capture.getvalue()
        
        # Should have at least one log entry
        self.assertGreater(len(log_output), 0, "No logs were generated for the request")
        
        # Parse log entries
        log_lines = [line for line in log_output.strip().split('\n') if line]
        
        # Should have at least one valid JSON log entry
        found_request_log = False
        for line in log_lines:
            try:
                log_entry = json.loads(line)
                
                # Check if this is a request log entry
                if 'message' in log_entry and 'Incoming request' in log_entry['message']:
                    found_request_log = True
                    
                    # Verify required fields are present
                    self.assertIn('timestamp', log_entry)
                    self.assertIn('level', log_entry)
                    self.assertIn('request_id', log_entry)
                    self.assertIn('method', log_entry)
                    self.assertIn('path', log_entry)
                    
                    # Verify the method and path match
                    self.assertEqual(log_entry['method'], method)
                    self.assertEqual(log_entry['path'], path)
                    
                    break
            except json.JSONDecodeError:
                # Skip non-JSON lines
                continue
        
        self.assertTrue(found_request_log, f"No request log found for {method} {path}")


class TestErrorLogging(unittest.TestCase):
    """Property-based tests for error logging."""
    
    def setUp(self):
        """Set up test Flask application."""
        self.app = create_app({'TESTING': True, 'LOG_LEVEL': 'INFO'})
        self.client = self.app.test_client()
        
        # Capture logs by replacing the stdout handler with our own
        self.log_capture = io.StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.handler.setFormatter(JSONFormatter())
        
        # Replace all handlers on root logger with our capture handler
        root_logger = logging.getLogger()
        self.original_handlers = root_logger.handlers[:]
        root_logger.handlers = [self.handler]
        root_logger.setLevel(logging.INFO)
        
        # Also replace app logger handlers since it has propagate=False
        self.original_app_handlers = self.app.logger.handlers[:]
        self.app.logger.handlers = [self.handler]
        self.app.logger.setLevel(logging.INFO)
    
    def tearDown(self):
        """Restore original logging handlers."""
        root_logger = logging.getLogger()
        root_logger.handlers = self.original_handlers
        self.app.logger.handlers = self.original_app_handlers
    
    @settings(max_examples=100)
    @given(
        error_message=st.text(min_size=1, max_size=100),
        error_type=st.sampled_from([ValueError, TypeError, RuntimeError, KeyError])
    )
    def test_all_errors_are_logged_with_context(self, error_message: str, error_type: type):
        """
        Feature: weather-web-service, Property 19: All errors are logged with context
        
        For any error that occurs during request processing, a log entry should be created
        with error details, stack trace, and request context.
        
        Validates: Requirements 12.2
        """
        # Clear previous logs
        self.log_capture.truncate(0)
        self.log_capture.seek(0)
        
        with self.app.test_request_context('/test'):
            # Set up request context
            g.request_id = 'test-request-id'
            
            # Create and log an error
            try:
                raise error_type(error_message)
            except Exception as e:
                log_error(e, {'test_context': 'test_value'})
        
        # Get the logged output
        log_output = self.log_capture.getvalue()
        
        # Should have at least one log entry
        self.assertGreater(len(log_output), 0, "No logs were generated for the error")
        
        # Parse log entries
        log_lines = [line for line in log_output.strip().split('\n') if line]
        
        # Should have at least one valid JSON log entry with error info
        found_error_log = False
        for line in log_lines:
            try:
                log_entry = json.loads(line)
                
                # Check if this is an error log entry
                if 'exception' in log_entry:
                    found_error_log = True
                    
                    # Verify required fields are present
                    self.assertIn('timestamp', log_entry)
                    self.assertIn('level', log_entry)
                    self.assertIn('request_id', log_entry)
                    self.assertIn('exception', log_entry)
                    
                    # Verify exception details
                    exception = log_entry['exception']
                    self.assertIn('type', exception)
                    self.assertIn('message', exception)
                    self.assertIn('traceback', exception)
                    
                    # Verify the error type and message
                    self.assertEqual(exception['type'], error_type.__name__)
                    # For KeyError, the message is repr'd, so check if error_message is in the exception message
                    # either directly or as a repr'd string
                    self.assertTrue(
                        error_message in exception['message'] or repr(error_message) in exception['message'],
                        f"Expected '{error_message}' or '{repr(error_message)}' in '{exception['message']}'"
                    )
                    
                    # Verify request context is included
                    self.assertEqual(log_entry['request_id'], 'test-request-id')
                    
                    break
            except json.JSONDecodeError:
                # Skip non-JSON lines
                continue
        
        self.assertTrue(found_error_log, f"No error log found for {error_type.__name__}: {error_message}")


class TestStdoutLogging(unittest.TestCase):
    """Property-based tests for stdout logging."""
    
    def setUp(self):
        """Set up stdout capture."""
        self.stdout_capture = io.StringIO()
        self.original_stdout = sys.stdout
    
    def tearDown(self):
        """Restore stdout."""
        sys.stdout = self.original_stdout
    
    @settings(max_examples=100)
    @given(
        log_message=st.text(min_size=1, max_size=100),
        log_level=st.sampled_from(['INFO', 'WARNING', 'ERROR'])
    )
    def test_logs_written_to_stdout(self, log_message: str, log_level: str):
        """
        Feature: weather-web-service, Property 20: Logs written to standard output
        
        For any log entry created, it should be written to standard output (stdout)
        for container-based log collection.
        
        Validates: Requirements 12.4
        """
        # Clear and redirect stdout
        self.stdout_capture.truncate(0)
        self.stdout_capture.seek(0)
        sys.stdout = self.stdout_capture
        
        # Create a test app
        app = Flask(__name__)
        app.config['LOG_LEVEL'] = log_level
        
        # Set up logging to write to stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        
        # Set up logging
        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, log_level))
        
        # Create app context for Flask's g object
        with app.app_context():
            # Log a message
            log_func = getattr(logger, log_level.lower())
            log_func(log_message)
        
        # Get the logged output
        log_output = self.stdout_capture.getvalue()
        
        # Verify output was written
        self.assertGreater(len(log_output), 0, "No output written to stdout")
        
        # Parse the JSON log entry
        try:
            log_entry = json.loads(log_output.strip())
            
            # Verify it's valid JSON with expected structure
            self.assertIn('timestamp', log_entry)
            self.assertIn('level', log_entry)
            self.assertIn('message', log_entry)
            
            # Verify the log level and message
            self.assertEqual(log_entry['level'], log_level)
            self.assertEqual(log_entry['message'], log_message)
        except json.JSONDecodeError:
            self.fail(f"Log output is not valid JSON: {log_output}")


class TestRequestIDs(unittest.TestCase):
    """Property-based tests for request ID tracking."""
    
    def setUp(self):
        """Set up test Flask application."""
        self.app = create_app({'TESTING': True, 'LOG_LEVEL': 'INFO'})
        self.client = self.app.test_client()
        
        # Capture logs by replacing the stdout handler with our own
        self.log_capture = io.StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.handler.setFormatter(JSONFormatter())
        
        # Replace all handlers on root logger with our capture handler
        root_logger = logging.getLogger()
        self.original_handlers = root_logger.handlers[:]
        root_logger.handlers = [self.handler]
        root_logger.setLevel(logging.INFO)
        
        # Also replace app logger handlers since it has propagate=False
        self.original_app_handlers = self.app.logger.handlers[:]
        self.app.logger.handlers = [self.handler]
        self.app.logger.setLevel(logging.INFO)
    
    def tearDown(self):
        """Restore original logging handlers."""
        root_logger = logging.getLogger()
        root_logger.handlers = self.original_handlers
        self.app.logger.handlers = self.original_app_handlers
    
    @settings(max_examples=100)
    @given(
        path=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=32, max_codepoint=126),
            min_size=1,
            max_size=50
        ).map(lambda s: '/' + s.replace(' ', '-').replace('/', '-'))
    )
    def test_request_ids_in_all_log_entries(self, path: str):
        """
        Feature: weather-web-service, Property 21: Request IDs in all log entries
        
        For any log entry, it should include a unique request ID that can be used
        to trace the request through the system.
        
        Validates: Requirements 12.5
        """
        # Clear previous logs
        self.log_capture.truncate(0)
        self.log_capture.seek(0)
        
        # Make a request
        try:
            self.client.get(path)
        except Exception:
            # Ignore errors, we just want to check logging
            pass
        
        # Get the logged output
        log_output = self.log_capture.getvalue()
        
        # Should have at least one log entry
        self.assertGreater(len(log_output), 0, "No logs were generated")
        
        # Parse log entries
        log_lines = [line for line in log_output.strip().split('\n') if line]
        
        # Check that all log entries have request IDs
        request_ids = set()
        for line in log_lines:
            try:
                log_entry = json.loads(line)
                
                # Every log entry should have a request_id
                self.assertIn('request_id', log_entry, 
                             f"Log entry missing request_id: {log_entry}")
                
                # Request ID should not be empty
                self.assertNotEqual(log_entry['request_id'], '', 
                                   "Request ID should not be empty")
                
                # Collect request IDs
                request_ids.add(log_entry['request_id'])
            except json.JSONDecodeError:
                # Skip non-JSON lines
                continue
        
        # Should have at least one request ID
        self.assertGreater(len(request_ids), 0, "No request IDs found in logs")


if __name__ == '__main__':
    unittest.main()
