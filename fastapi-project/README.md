# FastAPI Simple API

A simple REST API built with FastAPI that provides CRUD operations for managing items.

## Features

- Full CRUD operations (Create, Read, Update, Delete)
- Item search functionality
- Input validation with Pydantic
- Automatic API documentation
- Health check endpoint

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /items` - Get all items
- `GET /items/{item_id}` - Get item by ID
- `POST /items` - Create new item
- `PUT /items/{item_id}` - Update item
- `DELETE /items/{item_id}` - Delete item
- `GET /items/search/{query}` - Search items by name or description

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the API

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## Interactive API Documentation

Once the server is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Example Usage

### Create an item:
```bash
curl -X POST "http://localhost:8000/items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "description": "Gaming laptop",
    "price": 999.99,
    "is_available": true
  }'
```

### Get all items:
```bash
curl -X GET "http://localhost:8000/items"
```

### Search items:
```bash
curl -X GET "http://localhost:8000/items/search/laptop"
```
