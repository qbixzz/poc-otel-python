# Python API Examples with OpenTelemetry

This repository contains two simple REST API implementations using different Python web frameworks, fully instrumented with **OpenTelemetry** for observability:

## 🚀 Projects

### 1. FastAPI Project (`fastapi-project/`)
- **Framework**: FastAPI
- **Port**: 8000
- **Features**: 
  - Automatic API documentation (Swagger/OpenAPI)
  - Type validation with Pydantic
  - Async support
  - High performance
  - **🔍 OpenTelemetry instrumentation**

### 2. Flask Project (`flask-project/`)
- **Framework**: Flask
- **Port**: 5000
- **Features**:
  - Lightweight and simple
  - Flexible and extensible
  - More manual control
  - Status-based filtering
  - **🔍 OpenTelemetry instrumentation**

## 📊 OpenTelemetry Features

### Implemented Instrumentation:
- ✅ **Automatic HTTP tracing** (requests, responses, status codes)
- ✅ **Custom spans** with business logic attributes
- ✅ **Custom metrics** (counters, histograms)
- ✅ **Error tracking** and exception recording
- ✅ **Distributed tracing** with trace propagation
- ✅ **Resource attributes** (service name, version, environment)
- ✅ **System metrics** (CPU, memory, disk)
- ✅ **Logging correlation** with trace IDs

### Telemetry Data Collection:
- **OTLP Collector**: Receives and processes telemetry data
- **Multiple exporters**: Console, file, and OTLP HTTP/gRPC
- **Zpages**: Built-in debugging and monitoring pages
- **Health checks**: Collector and service health monitoring

## Quick Start

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

#### Local Development:

##### FastAPI Server:
```bash
cd fastapi-project
python main.py
```
Access at: http://localhost:8000
API Docs: http://localhost:8000/docs

##### Flask Server:
```bash
cd flask-project
python app.py
```
Access at: http://localhost:5000

#### Docker Deployment:

##### Simple Docker Compose (Both APIs):
```bash
# Start both services
docker-compose -f docker-compose.simple.yml up --build

# Or use the batch file on Windows
start-docker-simple.bat
```

##### Full Docker Compose (With Nginx Gateway):
```bash
# Start both services + nginx gateway
docker-compose up --build

# Or use the batch file on Windows
start-docker-full.bat
```

**Docker Access URLs:**
- FastAPI Direct: http://localhost:8000
- Flask Direct: http://localhost:5000
- Nginx Gateway: http://localhost/
- FastAPI via Gateway: http://localhost/fastapi/
- Flask via Gateway: http://localhost/flask/

### Testing the APIs

#### Local Testing:
```bash
# Test FastAPI (in fastapi-project directory)
python test_api.py

# Test Flask (in flask-project directory)
python test_api.py
```

#### Docker Testing:
```bash
# Test Docker containers (simple setup)
python test_docker.py

# Test Docker containers with nginx gateway
python test_docker.py --with-nginx
```

#### OpenTelemetry Testing:
```bash
# Comprehensive OpenTelemetry instrumentation testing
python test_otel.py
```

### 📊 Observability Endpoints

Once running, you can access various observability endpoints:

#### Service Endpoints:
- **FastAPI**: http://localhost:8000
  - API Docs: http://localhost:8000/docs
  - Health: http://localhost:8000/health
- **Flask**: http://localhost:5000
  - Health: http://localhost:5000/health

#### OpenTelemetry Endpoints:
- **OTEL Collector Health**: http://localhost:13133/
- **Zpages (Tracing Debug)**: http://localhost:55679/debug/tracez
- **Zpages (Services)**: http://localhost:55679/debug/servicez
- **OTLP gRPC Receiver**: localhost:4317
- **OTLP HTTP Receiver**: localhost:4318

#### Viewing Telemetry Data:
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
