# EDOT Flask API

A Flask API with Elastic Distribution for OpenTelemetry (EDOT) Python agent integration.

## Features

- Flask REST API with CRUD operations
- EDOT Python agent for automatic instrumentation
- Custom APM labels and error tracking
- Health check endpoints
- OpenTelemetry compatibility
- Docker support

## EDOT Integration

This project uses the **Elastic Distribution for OpenTelemetry (EDOT) Python** agent which provides:
- Automatic instrumentation for Flask
- APM transaction and span tracking
- Custom labels and tags
- Error and exception capture
- Metrics collection
- OpenTelemetry bridge compatibility

## API Endpoints

- `GET /` - Welcome message with EDOT info
- `GET /health` - Health check
- `GET /items` - Get all items
- `GET /items/{item_id}` - Get item by ID
- `POST /items` - Create new item
- `PUT /items/{item_id}` - Update item
- `DELETE /items/{item_id}` - Delete item
- `GET /items/search/{query}` - Search items
- `GET /items/status/{status}` - Filter by status
- `GET /items/error` - Test error handling

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables (see .env file):
```bash
export ELASTIC_APM_SERVICE_NAME=edot-flask-service
export ELASTIC_APM_SERVER_URL=http://localhost:8200
```

## Running the API

### Local Development
```bash
python app.py
```
The API will be available at `http://localhost:5001`

### Docker
```bash
docker build -t edot-flask-service .
docker run -p 5001:5001 edot-flask-service
```

## EDOT Configuration

The EDOT agent is configured in `app.py` with the following key settings:

```python
app.config['ELASTIC_APM'] = {
    'SERVICE_NAME': 'edot-flask-service',
    'SERVICE_VERSION': '1.0.0',
    'SERVER_URL': 'http://otel-collector:8200',
    'ENVIRONMENT': 'development',
    'CAPTURE_BODY': 'all',
    'CAPTURE_HEADERS': True,
    'OPENTELEMETRY_BRIDGE_ENABLED': True,  # OpenTelemetry compatibility
}
```

## Custom APM Labels

The application includes custom APM labels for better observability:
- Transaction labels for endpoints and operations
- Custom tags for service metadata
- Error capture with context
- Performance metrics

## Example Usage

### Create an item:
```bash
curl -X POST "http://localhost:5001/items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "EDOT Test Item",
    "description": "Test item with EDOT tracking",
    "price": 49.99,
    "is_available": true
  }'
```

### Test error handling:
```bash
curl -X GET "http://localhost:5001/items/error"
```

## Observability Features

- **Automatic instrumentation**: Flask requests, database calls, HTTP clients
- **Custom labels**: Business logic context and metadata
- **Error tracking**: Automatic exception capture with stack traces
- **Performance metrics**: Response times, throughput, error rates
- **Distributed tracing**: Cross-service trace correlation
