from secrets import choice
from flask import Flask, request, jsonify
import uuid
from datetime import datetime
import logging
import os

from opentelemetry import trace

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# Create Flask app
app = Flask(__name__)

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
    logger.info("Root endpoint accessed")
    
    response = {
        'message': 'Welcome to EDOT Flask API!',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'agent': 'Elastic Distribution for OpenTelemetry (EDOT) Python',
        'service_name': os.getenv('OTEL_SERVICE_NAME', 'edot-flask-api')
    }
    
    logger.info("Root endpoint completed successfully")
    return jsonify(response)

# Health check endpoint
@app.route('/health')
def health_check():
    logger.info("Health check accessed")
    
    response = {
        'status': 'healthy',
        'service': os.getenv('OTEL_SERVICE_NAME', 'edot-flask-api'),
        'version': os.getenv('OTEL_SERVICE_VERSION', '1.0.0'),
        'timestamp': datetime.now().isoformat(),
        'items_count': len(items_db)
    }
    
    logger.info("Health check completed successfully")
    return jsonify(response)

# Get all items
@app.route('/items', methods=['GET'])
def get_items():
    logger.info("Getting all items")
    
    with tracer.start_as_current_span("get_items") as span:
        span.set_attribute("value", "items")
    items_list = list(items_db.values())
    response = {
        'items': items_list,
        'count': len(items_list)
    }
    
    logger.info(f"Retrieved {len(items_list)} items")
    return jsonify(response)

# Get item by ID
@app.route('/items/<item_id>', methods=['GET'])
def get_item(item_id):
    logger.info(f"Getting item by ID: {item_id}")
    
    with tracer.start_as_current_span("get_items_id") as span:
        span.set_attribute("value", "items_id")
    if item_id not in items_db:
        logger.warning(f"Item not found: {item_id}")
        return jsonify({'error': 'Item not found'}), 404
    
    item = items_db[item_id]
    
    logger.info(f"Retrieved item: {item['name']} (ID: {item_id})")
    return jsonify(item)

# Create new item
@app.route('/items', methods=['POST'])
def create_item():
    logger.info("Creating new item")
    
    data = request.get_json()
    
    # Validate input data
    is_valid, error_message = validate_item_data(data)
    if not is_valid:
        logger.error(f"Validation error: {error_message}")
        return jsonify({'error': error_message}), 400
    
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
    
    logger.info(f"Created item: {data['name']} with ID: {item_id}")
    return jsonify(new_item), 201

# Update item
@app.route('/items/<item_id>', methods=['PUT'])
def update_item(item_id):
    logger.info(f"Updating item: {item_id}")
    
    if item_id not in items_db:
        logger.warning(f"Update failed - Item not found: {item_id}")
        return jsonify({'error': 'Item not found'}), 404
    
    data = request.get_json()
    
    # Validate input data
    is_valid, error_message = validate_item_data(data)
    if not is_valid:
        logger.error(f"Validation error: {error_message}")
        return jsonify({'error': error_message}), 400
    
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
    
    logger.info(f"Updated item: {data['name']} with ID: {item_id}")
    return jsonify(updated_item)

# Delete item
@app.route('/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    logger.info(f"Deleting item: {item_id}")
    
    if item_id not in items_db:
        logger.warning(f"Delete failed - Item not found: {item_id}")
        return jsonify({'error': 'Item not found'}), 404
    
    deleted_item = items_db.pop(item_id)
    
    logger.info(f"Deleted item: {deleted_item['name']} with ID: {item_id}")
    return jsonify({
        'message': f'Item {deleted_item["name"]} deleted successfully',
        'deleted_item': deleted_item
    })

# Search items by name or description
@app.route('/items/search/<query>', methods=['GET'])
def search_items(query):
    logger.info(f"Searching items with query: {query}")
    
    query_lower = query.lower()
    matching_items = [
        item for item in items_db.values()
        if query_lower in item['name'].lower() or query_lower in item.get('description', '').lower()
    ]
    
    logger.info(f"Search for '{query}' returned {len(matching_items)} items")
    return jsonify({
        'items': matching_items,
        'count': len(matching_items),
        'query': query
    })

# Get items by availability status
@app.route('/items/status/<status>', methods=['GET'])
def get_items_by_status(status):
    logger.info(f"Filtering items by status: {status}")
    
    is_available = status.lower() == 'available'
    filtered_items = [
        item for item in items_db.values()
        if item['is_available'] == is_available
    ]
    
    logger.info(f"Filter by status '{status}' returned {len(filtered_items)} items")
    return jsonify({
        'items': filtered_items,
        'count': len(filtered_items),
        'status': status
    })

# Custom endpoint to demonstrate error handling
@app.route('/items/error', methods=['GET'])
def trigger_error():
    logger.info("Triggering intentional error for testing")
    
    try:
        # Intentionally trigger an error for testing
        result = 1 / 0
        return jsonify({'result': result})
    except Exception as e:
        logger.error(f"Test error triggered: {str(e)}")
        return jsonify({'error': 'Intentional error for testing'}), 500

if __name__ == '__main__':
    logger.info("Starting EDOT Flask service...")
    logger.info(f"Service name: {os.getenv('OTEL_SERVICE_NAME', 'edot-flask-api')}")
    logger.info(f"OTLP endpoint: {os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'not set')}")
    app.run(host='0.0.0.0', port=5001, debug=False)
