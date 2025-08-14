from flask import Flask, request, jsonify
import uuid
from datetime import datetime
import logging

# Import OpenTelemetry components
from otel_config import init_otel, get_tracer, get_meter
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Initialize OpenTelemetry
init_otel(app)

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

# Root endpoint
@app.route('/')
def read_root():
    with tracer.start_as_current_span("read_root") as span:
        span.set_attribute("endpoint", "root")
        response = {
            'message': 'Welcome to Simple Flask API!',
            'version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat()
        }
        span.set_attribute("response.message", response["message"])
        return jsonify(response)

# Health check endpoint
@app.route('/health')
def health_check():
    with tracer.start_as_current_span("health_check") as span:
        span.set_attribute("endpoint", "health")
        response = {
            'status': 'healthy',
            'service': 'flask-service',
            'timestamp': datetime.utcnow().isoformat()
        }
        return jsonify(response)

# Get all items
@app.route('/items', methods=['GET'])
def get_items():
    with tracer.start_as_current_span("get_items") as span:
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
        return jsonify(response)

# Get item by ID
@app.route('/items/<item_id>', methods=['GET'])
def get_item(item_id):
    with tracer.start_as_current_span("get_item") as span:
        span.set_attribute("endpoint", "get_item")
        span.set_attribute("item.id", item_id)
        
        if item_id not in items_db:
            span.record_exception(Exception("Item not found"))
            span.set_status(Status(StatusCode.ERROR, "Item not found"))
            return jsonify({'error': 'Item not found'}), 404
        
        item = items_db[item_id]
        span.set_attribute("item.name", item['name'])
        span.set_attribute("item.price", item['price'])
        
        # Record metrics
        item_operations.add(1, {"operation": "get", "endpoint": "get_item"})
        
        return jsonify(item)

# Create new item
@app.route('/items', methods=['POST'])
def create_item():
    with tracer.start_as_current_span("create_item") as span:
        span.set_attribute("endpoint", "create_item")
        
        data = request.get_json()
        
        # Validate input data
        is_valid, error_message = validate_item_data(data)
        if not is_valid:
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
            'created_at': datetime.utcnow().isoformat()
        }
        
        items_db[item_id] = new_item
        
        span.set_attribute("item.id", item_id)
        span.set_attribute("item.created", True)
        
        # Record metrics
        item_counter.add(1, {"operation": "created"})
        item_operations.add(1, {"operation": "create", "endpoint": "create_item"})
        
        logger.info(f"Created item: {data['name']} with ID: {item_id}")
        return jsonify(new_item), 201

# Update item
@app.route('/items/<item_id>', methods=['PUT'])
def update_item(item_id):
    with tracer.start_as_current_span("update_item") as span:
        span.set_attribute("endpoint", "update_item")
        span.set_attribute("item.id", item_id)
        
        if item_id not in items_db:
            span.record_exception(Exception("Item not found"))
            span.set_status(Status(StatusCode.ERROR, "Item not found"))
            return jsonify({'error': 'Item not found'}), 404
        
        data = request.get_json()
        
        # Validate input data
        is_valid, error_message = validate_item_data(data)
        if not is_valid:
            span.record_exception(Exception(f"Validation error: {error_message}"))
            span.set_status(Status(StatusCode.ERROR, error_message))
            return jsonify({'error': error_message}), 400
        
        span.set_attribute("item.name", data['name'])
        
        # Update existing item
        updated_item = {
            'id': item_id,
            'name': data['name'],
            'description': data.get('description', ''),
            'price': float(data['price']),
            'is_available': data.get('is_available', True),
            'created_at': items_db[item_id].get('created_at'),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        items_db[item_id] = updated_item
        span.set_attribute("item.updated", True)
        
        # Record metrics
        item_operations.add(1, {"operation": "update", "endpoint": "update_item"})
        
        logger.info(f"Updated item: {data['name']} with ID: {item_id}")
        return jsonify(updated_item)

# Delete item
@app.route('/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    with tracer.start_as_current_span("delete_item") as span:
        span.set_attribute("endpoint", "delete_item")
        span.set_attribute("item.id", item_id)
        
        if item_id not in items_db:
            span.record_exception(Exception("Item not found"))
            span.set_status(Status(StatusCode.ERROR, "Item not found"))
            return jsonify({'error': 'Item not found'}), 404
        
        deleted_item = items_db.pop(item_id)
        span.set_attribute("item.name", deleted_item['name'])
        span.set_attribute("item.deleted", True)
        
        # Record metrics
        item_counter.add(-1, {"operation": "deleted"})
        item_operations.add(1, {"operation": "delete", "endpoint": "delete_item"})
        
        logger.info(f"Deleted item: {deleted_item['name']} with ID: {item_id}")
        return jsonify({
            'message': f'Item {deleted_item["name"]} deleted successfully',
            'deleted_item': deleted_item
        })

# Search items by name or description
@app.route('/items/search/<query>', methods=['GET'])
def search_items(query):
    with tracer.start_as_current_span("search_items") as span:
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
        
        logger.info(f"Search for '{query}' returned {len(matching_items)} items")
        return jsonify({
            'items': matching_items,
            'count': len(matching_items),
            'query': query
        })

# Get items by availability status
@app.route('/items/status/<status>', methods=['GET'])
def get_items_by_status(status):
    with tracer.start_as_current_span("get_items_by_status") as span:
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
        
        return jsonify({
            'items': filtered_items,
            'count': len(filtered_items),
            'status': status
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
