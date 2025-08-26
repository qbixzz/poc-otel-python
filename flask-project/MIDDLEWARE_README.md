# Flask OpenTelemetry Middleware Implementation

This project demonstrates how to implement OpenTelemetry as middleware in Flask applications for automatic observability without code changes.

## 🎯 Architecture Overview

```
Flask Application
       ↓
OpenTelemetry Middleware (Automatic)
       ↓
┌─────────────────────────────────────┐
│           Captures:                 │
│  • HTTP Requests/Responses          │
│  • Request Duration & Size          │  
│  • Error Handling                   │
│  • Business Context                 │
│  • Metrics & Traces                 │
└─────────────────────────────────────┘
       ↓
OpenTelemetry Collector
       ↓
Observability Platform (Elastic, Jaeger, etc.)
```

## 🚀 Key Features

### ✅ Automatic Instrumentation
- **Zero Code Changes**: All HTTP requests automatically traced
- **HTTP Attributes**: Method, URL, status codes, headers
- **Request/Response Sizes**: Automatic size tracking
- **Duration Metrics**: Request timing automatically captured

### 📊 Comprehensive Metrics
- `http_requests_total`: Total HTTP requests by endpoint/status
- `http_request_duration_seconds`: Request duration histograms  
- `http_request_size_bytes`: Request payload sizes
- `http_response_size_bytes`: Response payload sizes
- `http_requests_active`: Active request counter

### 🏷️ Business Context
- **Domain Detection**: Automatic business domain identification
- **Operation Mapping**: Maps endpoints to business operations
- **Custom Attributes**: Easy custom span attribute addition
- **Route Templates**: Flask route template tracking

### 🔗 Trace Propagation
- **W3C Trace Context**: Standard trace header propagation
- **B3 Propagation**: Zipkin-style trace propagation
- **Baggage Support**: W3C baggage propagation
- **Multi-Format**: Composite propagator support

## 📦 Implementation

### 1. Core Middleware (`otel_middleware.py`)

```python
from otel_middleware import setup_otel_middleware

# Initialize middleware
otel_middleware = setup_otel_middleware(app)

# Access middleware features
trace_id = otel_middleware.get_trace_id()
otel_middleware.add_custom_span_attribute("business.user_id", user_id)
```

### 2. Flask Application Integration

```python
from flask import Flask
from otel_config import init_otel
from otel_middleware import setup_otel_middleware

app = Flask(__name__)

# Initialize OpenTelemetry
init_otel(app)

# Setup middleware for automatic instrumentation
otel_middleware = setup_otel_middleware(app)

@app.route('/api/users')
def get_users():
    # Middleware automatically:
    # - Creates span for this request
    # - Sets HTTP attributes
    # - Records metrics
    # - Handles errors
    
    # Optional: Add custom business context
    otel_middleware.add_custom_span_attribute("business.operation", "list_users")
    
    return jsonify(users)
```

### 3. Advanced Usage

#### Custom Function Tracing
```python
from otel_middleware import trace_function

@trace_function("validate_user_data")
def validate_user(data):
    # Function automatically traced
    return is_valid, errors
```

#### Custom Span Context Manager
```python
from otel_middleware import trace_span

def process_order(order_data):
    with trace_span("process_payment", {"order.id": order_data["id"]}):
        # Custom business logic tracing
        payment_result = process_payment(order_data)
    
    return payment_result
```

## 🔧 Configuration

### Environment Variables
```bash
# Service identification
OTEL_SERVICE_NAME=flask-service
OTEL_SERVICE_VERSION=1.0.0
OTEL_ENVIRONMENT=development

# OTLP exporter
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc

# Excluded URLs (health checks, etc.)
OTEL_PYTHON_FLASK_EXCLUDED_URLS=/health,/metrics,/ready
```

### Middleware Configuration
```python
# Custom exclusions
middleware = setup_otel_middleware(
    app=app,
    excluded_urls=["/health", "/metrics", "/internal/*"]
)

# Custom tracer/meter providers
middleware = setup_otel_middleware(
    app=app,
    tracer_provider=custom_tracer_provider,
    meter_provider=custom_meter_provider
)
```

## 📊 Generated Telemetry

### Trace Attributes (Automatic)
```json
{
  "http.method": "POST",
  "http.url": "http://localhost:5000/api/items",
  "http.status_code": 201,
  "http.request_content_length": 156,
  "http.response_content_length": 284,
  "http.route": "/api/items",
  "http.user_agent": "curl/7.68.0",
  "business.domain": "inventory",
  "business.operation": "create_item"
}
```

### Metrics (Automatic)
```
# Request count
http_requests_total{method="POST", endpoint="create_item", status_code="201"} 15

# Request duration
http_request_duration_seconds{method="POST", endpoint="create_item"} 0.045

# Request size
http_request_size_bytes{method="POST", endpoint="create_item"} 156
```

## 🧪 Testing

### Run Middleware Tests
```bash
# Start the Flask application
python app.py

# Run middleware feature tests
python test_middleware.py
```

### Manual Testing
```bash
# Create an item (generates traces)
curl -X POST http://localhost:5000/items \\
  -H "Content-Type: application/json" \\
  -H "traceparent: 00-12345678901234567890123456789012-1234567890123456-01" \\
  -d '{"name":"Test Item","price":99.99}'

# Check response includes trace ID
# Middleware automatically adds trace context to logs
```

### Docker Compose Testing
```bash
# Start all services
docker-compose -f docker-compose-dev.yml up -d

# Run tests
python test_middleware.py

# Check traces in logs
docker-compose -f docker-compose-dev.yml logs otel-collector
```

## 🎭 Comparison: Manual vs Middleware

### Before (Manual Tracing)
```python
@app.route('/items', methods=['POST'])
def create_item():
    with tracer.start_as_current_span("create_item") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.url)
        
        try:
            data = request.get_json()
            span.set_attribute("item.name", data['name'])
            
            # Business logic...
            
            span.set_attribute("http.status_code", 201)
            return jsonify(item), 201
            
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
```

### After (Middleware Approach)
```python
@app.route('/items', methods=['POST'])
def create_item():
    # Middleware automatically handles:
    # - Span creation & management
    # - HTTP attributes
    # - Error handling
    # - Metrics recording
    
    data = request.get_json()
    
    # Optional: Add custom business context
    otel_middleware.add_custom_span_attribute("item.category", data.get('category'))
    
    # Just business logic
    item = create_new_item(data)
    return jsonify(item), 201
```

## 🎯 Benefits

### 🔥 Developer Experience
- **Reduced Boilerplate**: 90% less tracing code
- **Consistent Instrumentation**: Same approach across all endpoints
- **Error-Free**: No manual span management mistakes
- **Focus on Business Logic**: Less infrastructure concerns

### 📈 Observability
- **Complete Coverage**: All HTTP requests automatically traced
- **Standardized Attributes**: Consistent span attributes
- **Rich Context**: Business domain auto-detection
- **Performance Metrics**: Built-in performance monitoring

### 🚀 Production Ready
- **Low Overhead**: Minimal performance impact
- **Configurable**: Flexible configuration options
- **Battle Tested**: Based on OpenTelemetry standards
- **Scalable**: Handles high-throughput applications

## 🔄 Integration with Existing Code

The middleware is designed to work alongside existing manual instrumentation:

```python
@app.route('/complex-operation')
def complex_operation():
    # Middleware handles HTTP-level tracing automatically
    
    # Add custom business spans for complex operations
    with tracer.start_as_current_span("business_validation") as span:
        result = validate_business_rules()
        span.set_attribute("validation.result", result)
    
    with tracer.start_as_current_span("external_api_call") as span:
        api_response = call_external_api()
        span.set_attribute("api.response_time", api_response.duration)
    
    return jsonify({"status": "completed"})
```

## 📚 Next Steps

1. **Enable Middleware**: Add to your Flask app
2. **Configure Environment**: Set OTEL environment variables  
3. **Test Locally**: Run test scripts to verify
4. **Deploy & Monitor**: Deploy and check observability platform
5. **Extend**: Add custom business attributes as needed

This middleware approach provides comprehensive observability with minimal code changes, making it ideal for both new applications and retrofitting existing Flask services.
