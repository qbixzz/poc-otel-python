"""
OpenTelemetry configuration for Flask application
"""
import os
import uuid
import time
import logging
from typing import Optional
from functools import wraps

from flask import g, request
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, SERVICE_INSTANCE_ID, DEPLOYMENT_ENVIRONMENT
from opentelemetry.trace import Status, StatusCode, get_current_span

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter as HTTPMetricExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter as HTTPLogExporter

from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor

from opentelemetry.propagate import set_global_textmap, extract
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry import _logs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenTelemetryConfig:
    def __init__(self):
        self.service_name = os.getenv("OTEL_SERVICE_NAME", "flask-service")
        self.service_version = os.getenv("OTEL_SERVICE_VERSION", "1.0.0")
        self.service_instance_id = os.getenv("OTEL_SERVICE_INSTANCE_ID", f"{self.service_name}-1")
        self.environment = os.getenv("OTEL_ENVIRONMENT", "development")
        
        # OTLP endpoints
        self.otlp_grpc_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        self.otlp_http_endpoint = os.getenv("OTEL_EXPORTER_OTLP_HTTP_ENDPOINT", "http://localhost:4318")
        
        # Headers for authentication (if needed)
        self.otlp_headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
        
        # Export modes
        self.export_to_console = os.getenv("OTEL_EXPORT_CONSOLE", "false").lower() == "true"
        self.export_to_otlp = os.getenv("OTEL_EXPORT_OTLP", "true").lower() == "true"
        self.use_http_exporter = os.getenv("OTEL_USE_HTTP_EXPORTER", "false").lower() == "true"

    def get_resource(self) -> Resource:
        """Create OpenTelemetry resource with service information"""
        return Resource.create({
            SERVICE_NAME: self.service_name,
            SERVICE_VERSION: self.service_version,
            SERVICE_INSTANCE_ID: self.service_instance_id,
            DEPLOYMENT_ENVIRONMENT: self.environment,
            "service.namespace": "python-apis",
            "host.name": os.getenv("HOSTNAME", "flask-container"),
        })

    def setup_tracing(self, resource: Resource) -> None:
        """Configure OpenTelemetry tracing"""
        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)

        # Add span processors
        span_processors = []
        
        if self.export_to_console:
            console_processor = BatchSpanProcessor(ConsoleSpanExporter())
            span_processors.append(console_processor)
            
        if self.export_to_otlp:
            try:
                if self.use_http_exporter:
                    otlp_exporter = HTTPSpanExporter(
                        endpoint=f"{self.otlp_http_endpoint}/v1/traces",
                        headers=self._parse_headers(self.otlp_headers),
                    )
                else:
                    otlp_exporter = OTLPSpanExporter(
                        endpoint=self.otlp_grpc_endpoint,
                        headers=self._parse_headers(self.otlp_headers),
                    )
                
                otlp_processor = BatchSpanProcessor(otlp_exporter)
                span_processors.append(otlp_processor)
                logger.info(f"OTLP trace exporter configured: {'HTTP' if self.use_http_exporter else 'gRPC'}")
                
            except Exception as e:
                logger.error(f"Failed to configure OTLP trace exporter: {e}")

        # Add all processors to tracer provider
        for processor in span_processors:
            tracer_provider.add_span_processor(processor)

    def setup_metrics(self, resource: Resource) -> None:
        """Configure OpenTelemetry metrics"""
        metric_readers = []
        
        if self.export_to_console:
            console_reader = PeriodicExportingMetricReader(
                ConsoleMetricExporter(),
                export_interval_millis=30000,  # 30 seconds
            )
            metric_readers.append(console_reader)
            
        if self.export_to_otlp:
            try:
                if self.use_http_exporter:
                    otlp_exporter = HTTPMetricExporter(
                        endpoint=f"{self.otlp_http_endpoint}/v1/metrics",
                        headers=self._parse_headers(self.otlp_headers),
                    )
                else:
                    otlp_exporter = OTLPMetricExporter(
                        endpoint=self.otlp_grpc_endpoint,
                        headers=self._parse_headers(self.otlp_headers),
                    )
                
                otlp_reader = PeriodicExportingMetricReader(
                    otlp_exporter,
                    export_interval_millis=30000,  # 30 seconds
                )
                metric_readers.append(otlp_reader)
                logger.info(f"OTLP metric exporter configured: {'HTTP' if self.use_http_exporter else 'gRPC'}")
                
            except Exception as e:
                logger.error(f"Failed to configure OTLP metric exporter: {e}")

        # Create meter provider
        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=metric_readers,
        )
        metrics.set_meter_provider(meter_provider)

    def setup_logging(self, resource: Resource) -> None:
        """Configure OpenTelemetry logging"""
        log_processors = []
        
        if self.export_to_console:
            console_processor = BatchLogRecordProcessor(ConsoleLogExporter())
            log_processors.append(console_processor)
            
        if self.export_to_otlp:
            try:
                if self.use_http_exporter:
                    otlp_exporter = HTTPLogExporter(
                        endpoint=f"{self.otlp_http_endpoint}/v1/logs",
                        headers=self._parse_headers(self.otlp_headers),
                    )
                else:
                    otlp_exporter = OTLPLogExporter(
                        endpoint=self.otlp_grpc_endpoint,
                        headers=self._parse_headers(self.otlp_headers),
                    )
                
                otlp_processor = BatchLogRecordProcessor(otlp_exporter)
                log_processors.append(otlp_processor)
                logger.info(f"OTLP log exporter configured: {'HTTP' if self.use_http_exporter else 'gRPC'}")
                
            except Exception as e:
                logger.error(f"Failed to configure OTLP log exporter: {e}")

        # Create logger provider
        logger_provider = LoggerProvider(resource=resource)
        for processor in log_processors:
            logger_provider.add_log_record_processor(processor)
        
        _logs.set_logger_provider(logger_provider)
        
        # Create and configure the logging handler
        handler = LoggingHandler(
            level=logging.INFO,
            logger_provider=logger_provider,
        )
        
        # Add the handler to the root logger to capture all logs
        logging.getLogger().addHandler(handler)
        logger.info("OpenTelemetry logging configured")

    def setup_propagation(self) -> None:
        """Configure trace context propagation"""
        # Set up composite propagator with multiple formats
        propagators = [
            TraceContextTextMapPropagator(),  # W3C Trace Context
            B3MultiFormat(),                  # B3 propagation (Zipkin style)
            W3CBaggagePropagator(),          # W3C Baggage
        ]
        
        composite_propagator = CompositePropagator(propagators)
        set_global_textmap(composite_propagator)
        logger.info("Trace context propagation configured")

    def setup_instrumentations(self) -> None:
        """Configure automatic instrumentations"""
        try:
            # Instrument requests library
            RequestsInstrumentor().instrument()
            logger.info("Requests instrumentation enabled")
            
            # Instrument logging
            LoggingInstrumentor().instrument()
            logger.info("Logging instrumentation enabled")
            
            # Instrument system metrics
            SystemMetricsInstrumentor().instrument()
            logger.info("System metrics instrumentation enabled")
            
        except Exception as e:
            logger.error(f"Failed to setup instrumentations: {e}")

    def instrument_flask(self, app) -> None:
        """Instrument Flask application"""
        try:
            FlaskInstrumentor().instrument_app(
                app,
                tracer_provider=trace.get_tracer_provider(),
                excluded_urls="health,readiness,liveness,metrics",  # Exclude health endpoints
            )
            
            # Add Flask request hooks for enhanced tracing and logging
            @app.before_request
            def before_request():
                """Called before each request"""
                g.start_time = time.time()
                g.request_id = str(uuid.uuid4())
                
                # Extract trace context from incoming headers
                extract(request.headers)
                
                # Store current span for later access
                current_span = get_current_span()
                if current_span and current_span.is_recording():
                    g.current_span = current_span
                    
                    # Add request metadata to span
                    current_span.set_attribute("http.method", request.method)
                    current_span.set_attribute("http.url", request.url)
                    current_span.set_attribute("http.route", request.endpoint or "unknown")
                    current_span.set_attribute("http.user_agent", request.headers.get("User-Agent", ""))
                    current_span.set_attribute("request.id", g.request_id)
                    
                    # Add custom attributes
                    if hasattr(request, 'remote_addr'):
                        current_span.set_attribute("http.client_ip", request.remote_addr)

            @app.after_request
            def after_request(response):
                """Called after each request"""
                duration = time.time() - getattr(g, 'start_time', time.time())
                
                # Update span with response data
                current_span = getattr(g, 'current_span', None)
                if current_span and current_span.is_recording():
                    current_span.set_attribute("http.status_code", response.status_code)
                    current_span.set_attribute("http.response_size", len(response.get_data()))
                    current_span.set_attribute("http.request_duration_ms", round(duration * 1000, 2))
                    
                    # Set span status based on HTTP status code
                    if response.status_code >= 400:
                        current_span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
                
                return response

            @app.teardown_request
            def teardown_request(exception):
                """Called after request teardown"""
                if exception:
                    current_span = getattr(g, 'current_span', None)
                    if current_span and current_span.is_recording():
                        current_span.record_exception(exception)
                        current_span.set_status(Status(StatusCode.ERROR, str(exception)))
            
            logger.info("Flask instrumentation enabled")
        except Exception as e:
            logger.error(f"Failed to instrument Flask: {e}")

    def _parse_headers(self, headers_str: str) -> Optional[dict]:
        """Parse headers string into dictionary"""
        if not headers_str:
            return None
            
        headers = {}
        for header in headers_str.split(","):
            if "=" in header:
                key, value = header.split("=", 1)
                headers[key.strip()] = value.strip()
        return headers if headers else None

    def initialize(self, app=None) -> None:
        """Initialize all OpenTelemetry components"""
        try:
            logger.info(f"Initializing OpenTelemetry for {self.service_name}")
            
            # Get resource
            resource = self.get_resource()
            
            # Setup components
            self.setup_tracing(resource)
            self.setup_metrics(resource)
            self.setup_logging(resource)  # Add logging setup
            self.setup_propagation()
            self.setup_instrumentations()
            
            # Instrument Flask app if provided
            if app:
                self.instrument_flask(app)
                
            logger.info("OpenTelemetry initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}")
            raise

# Global instance
otel_config = OpenTelemetryConfig()

def init_otel(app=None) -> OpenTelemetryConfig:
    """Initialize OpenTelemetry with optional Flask app"""
    otel_config.initialize(app)
    return otel_config

def get_tracer(name: str):
    """Get a tracer instance"""
    return trace.get_tracer(name)

def get_meter(name: str):
    """Get a meter instance"""
    return metrics.get_meter(name)

def get_current_trace_id() -> Optional[str]:
    """Get current trace ID"""
    current_span = get_current_span()
    if current_span and current_span.is_recording():
        return f"{current_span.get_span_context().trace_id:032x}"
    return None

def get_current_span_id() -> Optional[str]:
    """Get current span ID"""
    current_span = get_current_span()
    if current_span and current_span.is_recording():
        return f"{current_span.get_span_context().span_id:016x}"
    return None

def get_request_id() -> Optional[str]:
    """Get current request ID"""
    return getattr(g, 'request_id', None)

def add_span_attribute(key: str, value):
    """Add custom attribute to current span"""
    current_span = get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute(key, str(value))
