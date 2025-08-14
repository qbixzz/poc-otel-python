# Python API Examples

This repository contains two simple REST API implementations using different Python web frameworks:

## Projects

### 1. FastAPI Project (`fastapi-project/`)
- **Framework**: FastAPI
- **Port**: 8000
- **Features**: 
  - Automatic API documentation (Swagger/OpenAPI)
  - Type validation with Pydantic
  - Async support
  - High performance

### 2. Flask Project (`flask-project/`)
- **Framework**: Flask
- **Port**: 5000
- **Features**:
  - Lightweight and simple
  - Flexible and extensible
  - More manual control
  - Status-based filtering

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
