# Complete Guide: Implementing OpenTelemetry in Python Projects

This repository serves as a **comprehensive guide** for implementing OpenTelemetry observability in Python applications. It demonstrates the complete journey from a basic Python project to a fully instrumented service with **traces, metrics, and logs**.

## 📋 Table of Contents

- [🎯 Overview](#overview)
- [🔄 From Plain Python to OpenTelemetry](#from-plain-python-to-opentelemetry)
- [📦 Dependencies & Installation](#dependencies--installation)
- [⚙️ Implementation Guide](#implementation-guide)
- [🏗️ Project Examples](#project-examples)
- [🚀 Quick Start](#quick-start)
- [📊 Observability Features](#observability-features)
- [🔧 Configuration](#configuration)
- [📈 Monitoring & Debugging](#monitoring--debugging)

## 🎯 Overview

This guide shows you **exactly what needs to be added** to transform a regular Python project into an OpenTelemetry-instrumented application that can send comprehensive telemetry data (traces, metrics, logs) to observability platforms.

### What You'll Learn

- ✅ **Step-by-step implementation** of OpenTelemetry in Python
- ✅ **Before/after code comparisons** showing exact changes needed
- ✅ **Complete configuration examples** for production use
- ✅ **Multiple framework support** (FastAPI, Flask)
- ✅ **Real-world examples** with error handling and performance monitoring

## 🔄 From Plain Python to OpenTelemetry

### What a Regular Python Project Needs to Add

#### 1. **Dependencies** (New packages to install)

```bash
# Core OpenTelemetry packages
pip install opentelemetry-api opentelemetry-sdk
pip install opentelemetry-exporter-otlp

# Automatic instrumentation (choose based on your stack)
pip install opentelemetry-instrumentation-fastapi    # For FastAPI
pip install opentelemetry-instrumentation-flask     # For Flask
pip install opentelemetry-instrumentation-requests  # For HTTP requests
pip install opentelemetry-instrumentation-logging   # For log correlation
```

#### 2. **Configuration Module** (New file: `otel_config.py`)

Create a centralized configuration to handle:

- ✅ **Service identification** (name, version, environment)
- ✅ **Exporter setup** (OTLP, console, file)
- ✅ **Automatic instrumentation** of frameworks
- ✅ **Custom metrics and tracing**
- ✅ **Error handling and debugging**

#### 3. **Application Integration** (Modify existing `main.py` or `app.py`)

Add 2-3 lines to initialize OpenTelemetry:

```python
# Add these imports
from otel_config import init_otel

# Add this initialization (usually after app creation)
init_otel(app)  # Pass your app instance
```

#### 4. **Environment Configuration** (New/updated `.env` or environment variables)

```bash
OTEL_SERVICE_NAME=your-service-name
OTEL_SERVICE_VERSION=1.0.0
OTEL_ENVIRONMENT=production
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

#### 5. **Collector Configuration** (New file: `otel-collector-config.yaml`)

Set up the OpenTelemetry Collector to receive, process, and export your telemetry data.

### That's It! 🎉

With these additions, your Python application will automatically:

- **Track all HTTP requests** with detailed spans
- **Capture application metrics** (response times, error rates)
- **Correlate logs** with trace IDs
- **Monitor system resources** (CPU, memory)
- **Export data** to your observability platform

## 📦 Dependencies & Installation

### Complete Dependency List

```bash
# Core OpenTelemetry packages (REQUIRED)
opentelemetry-api==1.21.0              # Core API
opentelemetry-sdk==1.21.0              # SDK implementation

# Exporters (choose based on your backend)
opentelemetry-exporter-otlp==1.21.0                    # OTLP (recommended)
opentelemetry-exporter-otlp-proto-grpc==1.21.0         # gRPC OTLP
opentelemetry-exporter-otlp-proto-http==1.21.0         # HTTP OTLP

# Automatic Instrumentation (choose based on your stack)
opentelemetry-instrumentation==0.42b0                   # Base instrumentation
opentelemetry-instrumentation-fastapi==0.42b0           # FastAPI auto-instrumentation
opentelemetry-instrumentation-flask==0.42b0             # Flask auto-instrumentation
opentelemetry-instrumentation-requests==0.42b0          # HTTP requests
opentelemetry-instrumentation-httpx==0.42b0             # HTTPX requests
opentelemetry-instrumentation-system-metrics==0.42b0    # System metrics
opentelemetry-instrumentation-logging==0.42b0           # Log correlation

# Additional utilities
opentelemetry-propagator-b3==1.21.0                     # B3 propagation (Zipkin)
opentelemetry-semantic-conventions==0.42b0              # Standard conventions
```

### Installation Commands

```bash
# Option 1: Install all at once
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp \
            opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-requests \
            opentelemetry-instrumentation-logging opentelemetry-instrumentation-system-metrics

# Option 2: Use requirements.txt (see fastapi-project/requirements.txt for complete example)
pip install -r requirements.txt
```

## ⚙️ Implementation Guide

### Step 1: Create OpenTelemetry Configuration Module

Create `otel_config.py` in your project root:

```python
"""
OpenTelemetry Configuration Module
Add this file to any Python project to enable observability
"""
import os
import logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

# Import framework-specific instrumentors
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # For FastAPI
from opentelemetry.instrumentation.flask import FlaskInstrumentor      # For Flask
from opentelemetry.instrumentation.requests import RequestsInstrumentor

def init_otel(app=None):
    """
    Initialize OpenTelemetry for any Python application
    Call this function with your app instance (FastAPI/Flask/etc.)
    """
    # 1. Configure service resource
    resource = Resource.create({
        SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "python-service"),
        SERVICE_VERSION: os.getenv("OTEL_SERVICE_VERSION", "1.0.0"),
        "service.environment": os.getenv("OTEL_ENVIRONMENT", "development"),
    })
    
    # 2. Setup tracing
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    
    # Add OTLP span exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # 3. Setup metrics
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        ),
        export_interval_millis=30000
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)
    
    # 4. Setup automatic instrumentation
    RequestsInstrumentor().instrument()  # HTTP requests
    
    # Framework-specific instrumentation
    if app:
        if hasattr(app, 'router'):  # FastAPI
            FastAPIInstrumentor.instrument_app(app)
        elif hasattr(app, 'wsgi_app'):  # Flask
            FlaskInstrumentor().instrument_app(app)
    
    logging.info("OpenTelemetry initialized successfully")
```

### Step 2: Modify Your Application

#### For FastAPI Applications

**Before (Plain FastAPI):**

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**After (With OpenTelemetry):**

```python
# main.py
from fastapi import FastAPI
from otel_config import init_otel  # Add this import

app = FastAPI()

# Add this line - initialize OpenTelemetry
init_otel(app)

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### For Flask Applications

**Before (Plain Flask):**

```python
# app.py
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return {'message': 'Hello World'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**After (With OpenTelemetry):**

```python
# app.py
from flask import Flask
from otel_config import init_otel  # Add this import

app = Flask(__name__)

# Add this line - initialize OpenTelemetry
init_otel(app)

@app.route('/')
def hello():
    return {'message': 'Hello World'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Step 3: Environment Configuration

Create `.env` file or set environment variables:

```bash
# Service identification
OTEL_SERVICE_NAME=my-python-service
OTEL_SERVICE_VERSION=1.0.0
OTEL_ENVIRONMENT=production

# OpenTelemetry Collector endpoint
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317

# Optional: Export configuration
OTEL_EXPORT_CONSOLE=false
OTEL_EXPORT_OTLP=true
```

### Step 4: Set Up OpenTelemetry Collector

Create `otel-collector-config.yaml`:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1000

exporters:
  # Export to your observability platform
  otlphttp:
    endpoint: "https://your-observability-platform.com/api/traces"
    headers:
      "Authorization": "Bearer YOUR_API_TOKEN"
  
  # Debug export to console
  debug:
    verbosity: normal

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlphttp, debug]
    
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlphttp, debug]
```

## 🏗️ Project Examples

This repository contains two complete examples showing OpenTelemetry implementation:

### 1. FastAPI Project (`fastapi-project/`)

- **Framework**: FastAPI with Pydantic
- **Port**: 8000
- **Features**:
  - Automatic API documentation (Swagger/OpenAPI)
  - Type validation and async support
  - **Complete OpenTelemetry instrumentation**
  - Custom business logic tracing
  - Performance metrics and error tracking

### 2. Flask Project (`flask-project/`)

- **Framework**: Flask with Werkzeug
- **Port**: 5000
- **Features**:
  - Lightweight REST API
  - Manual validation and synchronous processing
  - **Complete OpenTelemetry instrumentation**
  - Request filtering and custom attributes
  - Error handling and logging correlation

Both projects demonstrate:

- ✅ **Automatic HTTP tracing** with request/response details
- ✅ **Custom spans** for business logic
- ✅ **Custom metrics** (counters, histograms, gauges)
- ✅ **Error tracking** with exception details
- ✅ **Distributed tracing** with context propagation
- ✅ **Log correlation** with trace IDs
- ✅ **System metrics** monitoring

## 🚀 Quick Start

### Prerequisites

Make sure you have Python 3.8+ installed and a virtual environment set up.

**For Docker:** Make sure you have Docker and Docker Compose installed.

### Installation

#### Option 1: Local Development

1. Install all dependencies:

```bash
pip install fastapi==0.104.1 uvicorn==0.24.0 pydantic==2.5.0 Flask==3.0.0 Werkzeug==3.0.1 requests==2.31.0
```

#### Option 2: Docker (Recommended)

No additional installation required - Docker will handle dependencies.

### Running the APIs

#### Local Development

##### FastAPI Server

```bash
cd fastapi-project
python main.py
```

Access at: <http://localhost:8000>
API Docs: <http://localhost:8000/docs>

##### Flask Server

```bash
cd flask-project
python app.py
```

Access at: <http://localhost:5000>

#### Docker Deployment

##### Simple Docker Compose (Both APIs)

```bash
# Start both services
docker-compose -f docker-compose.simple.yml up --build

# Or use the batch file on Windows
start-docker-simple.bat
```

##### Full Docker Compose (With Nginx Gateway)

```bash
# Start both services + nginx gateway
docker-compose up --build

# Or use the batch file on Windows
start-docker-full.bat
```

**Docker Access URLs:**

- FastAPI Direct: <http://localhost:8000>
- Flask Direct: <http://localhost:5000>
- Nginx Gateway: <http://localhost/>
- FastAPI via Gateway: <http://localhost/fastapi/>
- Flask via Gateway: <http://localhost/flask/>

### Testing the APIs

#### Local Testing

```bash
# Test FastAPI (in fastapi-project directory)
python test_api.py

# Test Flask (in flask-project directory)
python test_api.py
```

#### Docker Testing

```bash
# Test Docker containers (simple setup)
python test_docker.py

# Test Docker containers with nginx gateway
python test_docker.py --with-nginx
```

#### OpenTelemetry Testing

```bash
# Comprehensive OpenTelemetry instrumentation testing
python test_otel.py
```

## 📊 Observability Features

### Implemented Instrumentation

- ✅ **Automatic HTTP tracing** (requests, responses, status codes)
- ✅ **Custom spans** with business logic attributes
- ✅ **Custom metrics** (counters, histograms)
- ✅ **Error tracking** and exception recording
- ✅ **Distributed tracing** with trace propagation
- ✅ **Resource attributes** (service name, version, environment)
- ✅ **System metrics** (CPU, memory, disk)
- ✅ **Logging correlation** with trace IDs

### Telemetry Data Collection

- **OTLP Collector**: Receives and processes telemetry data
- **Multiple exporters**: Console, file, and OTLP HTTP/gRPC
- **Zpages**: Built-in debugging and monitoring pages
- **Health checks**: Collector and service health monitoring

### 📊 Observability Endpoints

Once running, you can access various observability endpoints:

#### Service Endpoints

- **FastAPI**: <http://localhost:8000>
  - API Docs: <http://localhost:8000/docs>
  - Health: <http://localhost:8000/health>
- **Flask**: <http://localhost:5000>
  - Health: <http://localhost:5000/health>

#### OpenTelemetry Endpoints

- **OTEL Collector Health**: <http://localhost:13133/>
- **Zpages (Tracing Debug)**: <http://localhost:55679/debug/tracez>
- **Zpages (Services)**: <http://localhost:55679/debug/servicez>
- **OTLP gRPC Receiver**: localhost:4317
- **OTLP HTTP Receiver**: localhost:4318

#### Viewing Telemetry Data

```bash
# View collector logs
docker-compose logs -f otel-collector

# View service logs with correlation IDs
docker-compose logs -f fastapi-service
docker-compose logs -f flask-service

# View exported trace files
cat ./logs/all_traces.json | jq .

# Monitor container stats
docker stats
```

## 🔧 Configuration

### Advanced OpenTelemetry Configuration

For production environments, you can customize the OpenTelemetry configuration:

```python
# Enhanced otel_config.py with advanced features
import os
import logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter

def init_otel_advanced(app=None):
    """Advanced OpenTelemetry initialization with custom configuration"""
    
    # Environment-based configuration
    service_name = os.getenv("OTEL_SERVICE_NAME", "python-service")
    service_version = os.getenv("OTEL_SERVICE_VERSION", "1.0.0")
    environment = os.getenv("OTEL_ENVIRONMENT", "development")
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    
    # Resource configuration
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        "service.environment": environment,
        "service.namespace": "python-apis",
        "host.name": os.getenv("HOSTNAME", "localhost"),
    })
    
    # Tracing setup with multiple exporters
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    
    # OTLP exporter for production
    otlp_span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_span_exporter))
    
    # Console exporter for development
    if environment == "development":
        console_span_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(console_span_exporter))
    
    # Metrics setup
    metric_readers = [
        PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=otlp_endpoint),
            export_interval_millis=30000
        )
    ]
    
    if environment == "development":
        console_metric_reader = PeriodicExportingMetricReader(
            ConsoleMetricExporter(),
            export_interval_millis=60000
        )
        metric_readers.append(console_metric_reader)
    
    meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
    metrics.set_meter_provider(meter_provider)
    
    # Framework-specific instrumentation
    if app:
        # Add middleware, custom spans, and metrics
        setup_custom_instrumentation(app)
    
    logging.info(f"OpenTelemetry initialized for {service_name} v{service_version}")

def setup_custom_instrumentation(app):
    """Setup custom instrumentation based on framework"""
    # Add custom middleware, spans, and metrics here
    pass
```

### Environment Variables Reference

```bash
# Service Configuration
OTEL_SERVICE_NAME=my-python-service          # Service name
OTEL_SERVICE_VERSION=1.0.0                   # Service version
OTEL_ENVIRONMENT=production                   # Environment (dev/staging/prod)

# OTLP Configuration
OTEL_EXPORTER_OTLP_ENDPOINT=http://collector:4317    # OTLP gRPC endpoint
OTEL_EXPORTER_OTLP_HTTP_ENDPOINT=http://collector:4318 # OTLP HTTP endpoint
OTEL_EXPORTER_OTLP_HEADERS=api-key=your-key          # Authentication headers

# Export Configuration
OTEL_EXPORT_CONSOLE=false                    # Enable console export
OTEL_EXPORT_OTLP=true                       # Enable OTLP export
OTEL_USE_HTTP_EXPORTER=false                # Use HTTP instead of gRPC

# Performance Tuning
OTEL_BSP_MAX_QUEUE_SIZE=2048                # Span processor queue size
OTEL_BSP_EXPORT_TIMEOUT=30000               # Export timeout (ms)
OTEL_BSP_SCHEDULE_DELAY=5000                # Export schedule delay (ms)
```

## 📈 Monitoring & Debugging

### Custom Spans and Metrics

Add custom observability to your business logic:

```python
from opentelemetry import trace, metrics
from opentelemetry.trace import get_current_span, Status, StatusCode

# Get tracer and meter
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Create custom metrics
request_counter = meter.create_counter(
    "requests_total",
    description="Total number of requests",
    unit="1"
)

request_duration = meter.create_histogram(
    "request_duration_seconds",
    description="Request duration in seconds",
    unit="s"
)

@app.post("/items")
async def create_item(item: Item):
    # Create custom span
    with tracer.start_as_current_span("create_item") as span:
        try:
            # Add custom attributes
            span.set_attribute("item.name", item.name)
            span.set_attribute("item.price", item.price)
            
            # Simulate business logic
            result = await process_item(item)
            
            # Record metrics
            request_counter.add(1, {"endpoint": "/items", "method": "POST"})
            
            # Add result to span
            span.set_attribute("item.id", result.id)
            span.set_status(Status(StatusCode.OK))
            
            return result
            
        except Exception as e:
            # Record error in span
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            
            # Record error metric
            request_counter.add(1, {
                "endpoint": "/items", 
                "method": "POST", 
                "status": "error"
            })
            
            raise
```

### Log Correlation

Correlate logs with traces using trace context:

```python
import logging
from opentelemetry import trace
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Enable log correlation
LoggingInstrumentor().instrument()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] - %(message)s'
)

logger = logging.getLogger(__name__)

@app.get("/items/{item_id}")
async def get_item(item_id: str):
    logger.info(f"Getting item {item_id}")
    
    # Your business logic here
    item = await fetch_item(item_id)
    
    if item:
        logger.info(f"Found item {item_id}")
        return item
    else:
        logger.warning(f"Item {item_id} not found")
        raise HTTPException(status_code=404, detail="Item not found")
```

### Health Checks and Metrics

Implement health checks and expose metrics:

```python
@app.get("/health")
async def health_check():
    """Health check endpoint with telemetry"""
    with tracer.start_as_current_span("health_check") as span:
        try:
            # Check dependencies (database, external services, etc.)
            db_status = await check_database()
            cache_status = await check_cache()
            
            # Add health status to span
            span.set_attribute("health.database", db_status)
            span.set_attribute("health.cache", cache_status)
            
            if db_status and cache_status:
                span.set_status(Status(StatusCode.OK))
                return {"status": "healthy", "database": db_status, "cache": cache_status}
            else:
                span.set_status(Status(StatusCode.ERROR, "Service unhealthy"))
                return {"status": "unhealthy", "database": db_status, "cache": cache_status}
                
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=503, detail="Service unavailable")
```

## API Comparison

| Feature | FastAPI | Flask |
|---------|---------|-------|
| Auto Documentation | ✅ Built-in Swagger UI | ❌ Manual |
| Type Validation | ✅ Pydantic models | ⚠️ Manual validation |
| Performance | ✅ High (async) | ⚠️ Standard |
| Learning Curve | ⚠️ Moderate | ✅ Easy |
| Flexibility | ⚠️ Opinionated | ✅ Very flexible |
| Community | ✅ Growing fast | ✅ Large, established |

## Common Endpoints

Both APIs provide similar functionality:

- `GET /` - Welcome message
- `GET /health` - Health check  
- `GET /items` - List all items
- `POST /items` - Create new item
- `GET /items/{id}` - Get item by ID
- `PUT /items/{id}` - Update item
- `DELETE /items/{id}` - Delete item
- `GET /items/search/{query}` - Search items

## Item Data Structure

```json
{
  "id": "uuid-string",
  "name": "Item Name",
  "description": "Item Description", 
  "price": 99.99,
  "is_available": true
}
```

Choose the framework that best fits your project needs!

---

**🎯 Summary**: This guide provides everything you need to add comprehensive OpenTelemetry observability to any Python project. From a simple 3-line integration to advanced custom instrumentation, you now have the tools to monitor your applications effectively.

For questions or contributions, please check the individual project READMEs in `fastapi-project/` and `flask-project/` directories.
