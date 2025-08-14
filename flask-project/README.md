# Flask Simple API

A simple REST API built with Flask that provides CRUD operations for managing items.

## Features

- Full CRUD operations (Create, Read, Update, Delete)
- Item search functionality
- Input validation
- Status-based item filtering
- Health check endpoint
- Error handling

## API Endpoints

- `GET /` - Welcome message with timestamp
- `GET /health` - Health check with timestamp
- `GET /items` - Get all items with count
- `GET /items/{item_id}` - Get item by ID
- `POST /items` - Create new item
- `PUT /items/{item_id}` - Update item
- `DELETE /items/{item_id}` - Delete item
- `GET /items/search/{query}` - Search items by name or description
- `GET /items/status/{status}` - Get items by availability status (available/unavailable)

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the API

```bash
python app.py
```

The API will be available at `http://localhost:5000`

## Example Usage

### Create an item

```bash
curl -X POST "http://localhost:5000/items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smartphone",
    "description": "Latest model smartphone",
    "price": 699.99,
    "is_available": true
  }'
```

### Get all items

```bash
curl -X GET "http://localhost:5000/items"
```

### Search items

```bash
curl -X GET "http://localhost:5000/items/search/phone"
```

### Get available items

```bash
curl -X GET "http://localhost:5000/items/status/available"
```

## Data Structure

Each item has the following structure:

```json
{
  "id": "uuid-string",
  "name": "Item Name",
  "description": "Item Description",
  "price": 99.99,
  "is_available": true,
  "created_at": "2025-01-01T00:00:00.000000",
  "updated_at": "2025-01-01T00:00:00.000000"
}
```
