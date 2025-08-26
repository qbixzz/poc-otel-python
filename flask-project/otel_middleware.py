"""
OpenTelemetry Middleware for Flask Application
Automatically captures traces, metrics, and logs for all requests
"""
import time
import logging
from functools import wraps
from typing import Dict, Any, Optional

from flask import Flask, request, g, jsonify
from werkzeug.exceptions import HTTPException

from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.semconv.metrics import MetricInstruments
from opentelemetry.propagate import extract
from opentelemetry.util.http import get_excluded_urls, remove_url_credentials

logger = logging.getLogger(__name__)

class OpenTelemetryMiddleware:
    """
    OpenTelemetry middleware for Flask applications.
    Automatically instruments all HTTP requests with traces and metrics.
    """
    
    def __init__(self, app: Flask, tracer_provider=None, meter_provider=None):
        self.app = app
        self.tracer = trace.get_tracer(__name__, tracer_provider=tracer_provider)
        self.meter = metrics.get_meter(__name__, meter_provider=meter_provider)
        
        # Create metrics instruments
        self._setup_metrics()
        
        # Setup middleware hooks
        self._setup_middleware()
        
        # Excluded URLs (health checks, etc.)
        self.excluded_urls = get_excluded_urls("OTEL_PYTHON_FLASK_EXCLUDED_URLS")
        
        logger.info("OpenTelemetry middleware initialized")

    def _setup_metrics(self):
        """Setup OpenTelemetry metrics instruments"""
        # HTTP request counter
        self.http_requests_total = self.meter.create_counter(
            name="http_requests_total",
            description="Total number of HTTP requests",
            unit="1"
        )
        
        # HTTP request duration histogram
        self.http_request_duration = self.meter.create_histogram(
            name="http_request_duration_seconds",
            description="HTTP request duration in seconds",
            unit="s"
        )
        
        # HTTP request size histogram
        self.http_request_size = self.meter.create_histogram(
            name="http_request_size_bytes",
            description="HTTP request size in bytes",
            unit="By"
        )
        
        # HTTP response size histogram
        self.http_response_size = self.meter.create_histogram(
            name="http_response_size_bytes",
            description="HTTP response size in bytes",
            unit="By"
        )
        
        # Active requests gauge
        self.http_requests_active = self.meter.create_up_down_counter(
            name="http_requests_active",
            description="Number of active HTTP requests",
            unit="1"
        )

    def _setup_middleware(self):
        """Setup Flask middleware hooks"""
        self.app.before_request(self._before_request)
        self.app.after_request(self._after_request)
        self.app.teardown_request(self._teardown_request)
        
        # Handle exceptions
        self.app.errorhandler(Exception)(self._handle_exception)

    def _should_exclude_request(self) -> bool:
        """Check if the current request should be excluded from tracing"""
        if not request:
            return True
            
        url = remove_url_credentials(request.url)
        return self.excluded_urls and self.excluded_urls.url_disabled(url)

    def _get_request_attributes(self) -> Dict[str, Any]:
        """Extract request attributes for tracing"""
        attributes = {
            SpanAttributes.HTTP_METHOD: request.method,
            SpanAttributes.HTTP_URL: remove_url_credentials(request.url),
            SpanAttributes.HTTP_SCHEME: request.scheme,
            SpanAttributes.HTTP_HOST: request.host,
            SpanAttributes.HTTP_TARGET: request.path,
            SpanAttributes.HTTP_USER_AGENT: request.headers.get('User-Agent', ''),
            SpanAttributes.HTTP_FLAVOR: request.environ.get('SERVER_PROTOCOL', ''),
        }
        
        # Add request headers as attributes (filtered)
        for header_name, header_value in request.headers:
            if header_name.lower() in ['x-request-id', 'x-correlation-id', 'x-trace-id']:
                attributes[f"http.request.header.{header_name.lower()}"] = header_value
        
        # Add query parameters count
        if request.args:
            attributes["http.request.query_params_count"] = len(request.args)
        
        # Add request body size
        content_length = request.headers.get('Content-Length')
        if content_length:
            try:
                attributes[SpanAttributes.HTTP_REQUEST_CONTENT_LENGTH] = int(content_length)
            except ValueError:
                pass
        
        return attributes

    def _get_metric_labels(self) -> Dict[str, str]:
        """Get labels for metrics"""
        return {
            "method": request.method,
            "endpoint": request.endpoint or "unknown",
            "path": request.path,
        }

    def _before_request(self):
        """Called before each request"""
        if self._should_exclude_request():
            return
        
        # Start timing the request
        g.otel_start_time = time.time()
        
        # Increment active requests
        labels = self._get_metric_labels()
        self.http_requests_active.add(1, labels)
        
        # Extract trace context from request headers
        parent_context = extract(request.headers)
        
        # Create span name
        span_name = f"{request.method} {request.path}"
        
        # Start span with extracted context
        span = self.tracer.start_span(
            name=span_name,
            kind=SpanKind.SERVER,
            context=parent_context
        )
        
        # Set span attributes
        attributes = self._get_request_attributes()
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(key, value)
        
        # Store span in Flask's g object for later use
        g.otel_span = span
        g.otel_token = trace.set_span_in_context(span).attach()
        
        # Log request start
        logger.debug(f"Started tracing request: {request.method} {request.path}")

    def _after_request(self, response):
        """Called after each request"""
        if self._should_exclude_request():
            return response
        
        if not hasattr(g, 'otel_span'):
            return response
        
        span = g.otel_span
        start_time = getattr(g, 'otel_start_time', time.time())
        
        try:
            # Calculate request duration
            duration = time.time() - start_time
            
            # Set response attributes
            span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, response.status_code)
            
            # Set response size
            response_size = len(response.get_data()) if hasattr(response, 'get_data') else 0
            if response_size > 0:
                span.set_attribute(SpanAttributes.HTTP_RESPONSE_CONTENT_LENGTH, response_size)
            
            # Set span status based on HTTP status code
            if response.status_code >= 400:
                if response.status_code < 500:
                    span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
                else:
                    span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
            else:
                span.set_status(Status(StatusCode.OK))
            
            # Record metrics
            labels = self._get_metric_labels()
            labels["status_code"] = str(response.status_code)
            labels["status_class"] = f"{response.status_code // 100}xx"
            
            # Record request count
            self.http_requests_total.add(1, labels)
            
            # Record request duration
            self.http_request_duration.record(duration, labels)
            
            # Record request size
            request_size = int(request.headers.get('Content-Length', 0))
            if request_size > 0:
                self.http_request_size.record(request_size, labels)
            
            # Record response size
            if response_size > 0:
                self.http_response_size.record(response_size, labels)
            
            # Decrement active requests
            self.http_requests_active.add(-1, self._get_metric_labels())
            
            # Add custom business logic attributes
            self._add_business_attributes(span, response)
            
        except Exception as e:
            logger.error(f"Error in after_request middleware: {e}")
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
        
        return response

    def _teardown_request(self, exception):
        """Called when request context is torn down"""
        if not hasattr(g, 'otel_span'):
            return
        
        try:
            span = g.otel_span
            token = getattr(g, 'otel_token', None)
            
            # Record exception if one occurred
            if exception:
                span.record_exception(exception)
                span.set_status(Status(StatusCode.ERROR, str(exception)))
            
            # End span
            span.end()
            
            # Detach context
            if token:
                trace.context_api.detach(token)
                
            logger.debug("Completed request tracing")
            
        except Exception as e:
            logger.error(f"Error in teardown_request middleware: {e}")

    def _handle_exception(self, exception):
        """Handle uncaught exceptions"""
        if hasattr(g, 'otel_span'):
            span = g.otel_span
            span.record_exception(exception)
            span.set_status(Status(StatusCode.ERROR, str(exception)))
        
        # Re-raise the exception if it's not an HTTP exception
        if not isinstance(exception, HTTPException):
            raise exception
        
        # Return error response for HTTP exceptions
        return jsonify({'error': str(exception)}), exception.code

    def _add_business_attributes(self, span, response):
        """Add business-specific attributes to spans"""
        try:
            # Add response content type
            content_type = response.headers.get('Content-Type', '')
            if content_type:
                span.set_attribute("http.response.content_type", content_type)
            
            # Add business context based on endpoint
            if hasattr(request, 'endpoint'):
                endpoint = request.endpoint
                
                if endpoint and 'items' in endpoint:
                    span.set_attribute("business.domain", "inventory")
                    
                    if request.method == 'POST':
                        span.set_attribute("business.operation", "create_item")
                    elif request.method == 'GET' and request.view_args:
                        span.set_attribute("business.operation", "get_item")
                    elif request.method == 'PUT':
                        span.set_attribute("business.operation", "update_item")
                    elif request.method == 'DELETE':
                        span.set_attribute("business.operation", "delete_item")
                    elif 'search' in str(request.path):
                        span.set_attribute("business.operation", "search_items")
                
                # Add route template
                if hasattr(request, 'url_rule') and request.url_rule:
                    span.set_attribute("http.route", str(request.url_rule))
        
        except Exception as e:
            logger.debug(f"Error adding business attributes: {e}")

    def add_custom_span_attribute(self, key: str, value: Any):
        """Add custom attribute to current span"""
        if hasattr(g, 'otel_span') and g.otel_span:
            g.otel_span.set_attribute(key, value)

    def get_current_span(self):
        """Get current active span"""
        return getattr(g, 'otel_span', None)

    def get_trace_id(self) -> Optional[str]:
        """Get current trace ID"""
        span = self.get_current_span()
        if span:
            return format(span.get_span_context().trace_id, '032x')
        return None

    def get_span_id(self) -> Optional[str]:
        """Get current span ID"""
        span = self.get_current_span()
        if span:
            return format(span.get_span_context().span_id, '016x')
        return None


def setup_otel_middleware(app: Flask, tracer_provider=None, meter_provider=None) -> OpenTelemetryMiddleware:
    """
    Setup OpenTelemetry middleware for Flask app
    
    Args:
        app: Flask application instance
        tracer_provider: Optional tracer provider
        meter_provider: Optional meter provider
    
    Returns:
        OpenTelemetryMiddleware instance
    """
    middleware = OpenTelemetryMiddleware(
        app=app,
        tracer_provider=tracer_provider,
        meter_provider=meter_provider
    )
    
    # Add middleware reference to app for later access
    app.otel_middleware = middleware
    
    return middleware


# Decorator for adding custom tracing to functions
def trace_function(name: Optional[str] = None):
    """
    Decorator to add tracing to individual functions
    
    Args:
        name: Optional custom span name
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            span_name = name or f"{func.__module__}.{func.__name__}"
            tracer = trace.get_tracer(__name__)
            
            with tracer.start_as_current_span(span_name) as span:
                try:
                    # Add function metadata
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    result = func(*args, **kwargs)
                    
                    # Mark success
                    span.set_status(Status(StatusCode.OK))
                    return result
                    
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        
        return wrapper
    return decorator


# Context manager for custom spans
class trace_span:
    """Context manager for creating custom spans"""
    
    def __init__(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        self.name = name
        self.attributes = attributes or {}
        self.tracer = trace.get_tracer(__name__)
        self.span = None
    
    def __enter__(self):
        self.span = self.tracer.start_span(self.name)
        
        # Set attributes
        for key, value in self.attributes.items():
            if value is not None:
                self.span.set_attribute(key, value)
        
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.span.record_exception(exc_val)
            self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
        else:
            self.span.set_status(Status(StatusCode.OK))
        
        self.span.end()
