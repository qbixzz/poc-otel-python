from flask import Flask, request, jsonify, g
import uuid
import json
from datetime import datetime
import logging

# Import OpenTelemetry components
from otel_config import init_otel, get_tracer, get_meter, get_current_trace_id, get_current_span_id
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode

# Minimal logging setup - OpenTelemetry handles correlation automatically
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Initialize OpenTelemetry first
otel_config = init_otel(app)

# Get OpenTelemetry tracer and meter
tracer = get_tracer(__name__)
meter = get_meter(__name__)

# Create custom metrics
item_counter = meter.create_counter(
    "items_total",
    description="Total number of items processed",
    unit="1",
)

request_duration = meter.create_histogram(
    "request_duration_seconds",
    description="Duration of requests in seconds", 
    unit="s",
)

item_operations = meter.create_counter(
    "item_operations_total",
    description="Total number of item operations",
    unit="1",
)

# In-memory storage
items_db = {}

# Helper function to validate item data
def validate_item_data(data):
    required_fields = ['name', 'price']
    if not data:
        return False, "No data provided"
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    if not isinstance(data['price'], (int, float)) or data['price'] < 0:
        return False, "Price must be a positive number"
    
    return True, None

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Root endpoint (relies on middleware for basic tracing)
@app.route('/')
def read_root():
    logger.info("Root endpoint accessed")
    
    # Get current trace ID
    current_trace_id = get_current_trace_id()
    
    response = {
        'message': 'Welcome to Simple Flask API!',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'trace_id': current_trace_id  # Include trace ID in response
    }
    
    logger.info("Root endpoint completed successfully")
    return jsonify(response)

# Health check endpoint (excluded from detailed tracing)
@app.route('/health')
def health_check():
    logger.info("Health check accessed")
    
    response = {
        'status': 'healthy',
        'service': 'flask-service',
        'timestamp': datetime.now().isoformat(),
        'items_count': len(items_db)
    }
    
    logger.info("Health check completed")
    return jsonify(response)

# Get all items
@app.route('/items', methods=['GET'])
def get_items():
    logger.info("Getting all items")
    
    with tracer.start_as_current_span("GET /items") as span:
        span.set_attribute("endpoint", "get_items")
        span.set_attribute("items.count", len(items_db))
        
        items_list = list(items_db.values())
        response = {
            'items': items_list,
            'count': len(items_list)
        }
        
        # Record metrics
        item_operations.add(1, {"operation": "list", "endpoint": "get_items"})
        
        span.set_attribute("response.items_count", len(items_list))
        
        logger.info(f"Successfully retrieved {len(items_list)} items")
        return jsonify(response)

# Get item by ID
@app.route('/items/<item_id>', methods=['GET'])
def get_item(item_id):
    logger.info(f"Getting item: {item_id}")
    
    with tracer.start_as_current_span("GET /items/<item_id>") as span:
        span.set_attribute("endpoint", "get_item")
        span.set_attribute("item.id", item_id)
        
        if item_id not in items_db:
            logger.warning(f"Item not found: {item_id}")
            span.record_exception(Exception("Item not found"))
            span.set_status(Status(StatusCode.ERROR, "Item not found"))
            return jsonify({'error': 'Item not found'}), 404
        
        item = items_db[item_id]
        span.set_attribute("item.name", item['name'])
        span.set_attribute("item.price", item['price'])
        
        # Record metrics
        item_operations.add(1, {"operation": "get", "endpoint": "get_item"})
        
        logger.info(f"Successfully retrieved item: {item['name']}")
        return jsonify(item)

# Create new item
@app.route('/items', methods=['POST'])
def create_item():
    data = request.get_json()
    logger.info(f"Creating new item: {data.get('name', 'Unknown') if data else 'No data'}")
    
    with tracer.start_as_current_span("POST /items") as span:
        span.set_attribute("endpoint", "create_item")
        
        # Validate input data
        is_valid, error_message = validate_item_data(data)
        if not is_valid:
            logger.error(f"Item creation failed - validation error: {error_message}")
            span.record_exception(Exception(f"Validation error: {error_message}"))
            span.set_status(Status(StatusCode.ERROR, error_message))
            return jsonify({'error': error_message}), 400
        
        span.set_attribute("item.name", data['name'])
        span.set_attribute("item.price", data['price'])
        
        # Create new item
        item_id = str(uuid.uuid4())
        new_item = {
            'id': item_id,
            'name': data['name'],
            'description': data.get('description', ''),
            'price': float(data['price']),
            'is_available': data.get('is_available', True),
            'created_at': datetime.now().isoformat()
        }
        
        items_db[item_id] = new_item
        
        span.set_attribute("item.id", item_id)
        span.set_attribute("item.created", True)
        
        # Record metrics
        item_counter.add(1, {"operation": "created"})
        item_operations.add(1, {"operation": "create", "endpoint": "create_item"})
        
        logger.info(f"Successfully created new item: {data['name']} with ID: {item_id}")
        return jsonify(new_item), 201

# Update item
@app.route('/items/<item_id>', methods=['PUT'])
def update_item(item_id):
    logger.info(f"Updating item: {item_id}")
    
    with tracer.start_as_current_span("PUT /items/<item_id>") as span:
        span.set_attribute("endpoint", "update_item")
        span.set_attribute("item.id", item_id)
        
        if item_id not in items_db:
            logger.warning(f"Cannot update - item not found: {item_id}")
            span.record_exception(Exception("Item not found"))
            span.set_status(Status(StatusCode.ERROR, "Item not found"))
            return jsonify({'error': 'Item not found'}), 404
        
        data = request.get_json()
        
        # Validate input data
        is_valid, error_message = validate_item_data(data)
        if not is_valid:
            logger.error(f"Item update failed - validation error: {error_message}")
            span.record_exception(Exception(f"Validation error: {error_message}"))
            span.set_status(Status(StatusCode.ERROR, error_message))
            return jsonify({'error': error_message}), 400
        
        old_item_name = items_db[item_id]['name']
        span.set_attribute("item.name", data['name'])
        
        # Update existing item
        updated_item = {
            'id': item_id,
            'name': data['name'],
            'description': data.get('description', ''),
            'price': float(data['price']),
            'is_available': data.get('is_available', True),
            'created_at': items_db[item_id].get('created_at'),
            'updated_at': datetime.now().isoformat()
        }
        
        items_db[item_id] = updated_item
        span.set_attribute("item.updated", True)
        
        # Record metrics
        item_operations.add(1, {"operation": "update", "endpoint": "update_item"})
        
        logger.info(f"Successfully updated item: {old_item_name} -> {data['name']}")
        return jsonify(updated_item)

# Delete item
@app.route('/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    logger.info(f"Deleting item: {item_id}")
    
    with tracer.start_as_current_span("DELETE /items/<item_id>") as span:
        span.set_attribute("endpoint", "delete_item")
        span.set_attribute("item.id", item_id)
        
        if item_id not in items_db:
            logger.warning(f"Cannot delete - item not found: {item_id}")
            span.record_exception(Exception("Item not found"))
            span.set_status(Status(StatusCode.ERROR, "Item not found"))
            return jsonify({'error': 'Item not found'}), 404
        
        deleted_item = items_db.pop(item_id)
        span.set_attribute("item.name", deleted_item['name'])
        span.set_attribute("item.deleted", True)
        
        # Record metrics
        item_counter.add(-1, {"operation": "deleted"})
        item_operations.add(1, {"operation": "delete", "endpoint": "delete_item"})
        
        response = {
            'message': f'Item {deleted_item["name"]} deleted successfully',
            'deleted_item': deleted_item
        }
        
        logger.info(f"Successfully deleted item: {deleted_item['name']}")
        return jsonify(response)

# Search items by name or description
@app.route('/items/search/<query>', methods=['GET'])
def search_items(query):
    logger.info(f"Searching items for query: {query}")
    
    with tracer.start_as_current_span("GET /items/search/<query>") as span:
        span.set_attribute("endpoint", "search_items")
        span.set_attribute("search.query", query)
        
        query_lower = query.lower()
        matching_items = [
            item for item in items_db.values()
            if query_lower in item['name'].lower() or query_lower in item.get('description', '').lower()
        ]
        
        span.set_attribute("search.results_count", len(matching_items))
        
        # Record metrics
        item_operations.add(1, {"operation": "search", "endpoint": "search_items"})
        
        response = {
            'items': matching_items,
            'count': len(matching_items),
            'query': query
        }
        
        logger.info(f"Search completed - found {len(matching_items)} items")
        return jsonify(response)

# Get items by availability status
@app.route('/items/status/<status>', methods=['GET'])
def get_items_by_status(status):
    logger.info(f"Filtering items by status: {status}")
    
    with tracer.start_as_current_span("GET /items/status/<status>") as span:
        span.set_attribute("endpoint", "get_items_by_status")
        span.set_attribute("filter.status", status)
        
        is_available = status.lower() == 'available'
        filtered_items = [
            item for item in items_db.values()
            if item['is_available'] == is_available
        ]
        
        span.set_attribute("filter.results_count", len(filtered_items))
        
        # Record metrics
        item_operations.add(1, {"operation": "filter", "endpoint": "get_items_by_status"})
        
        response = {
            'items': filtered_items,
            'count': len(filtered_items),
            'status': status
        }
        
        logger.info(f"Status filter completed - found {len(filtered_items)} items with status: {status}")
        return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
