from flask import Flask, request, jsonify, g
import uuid
import json
import time
from datetime import datetime
import logging

# Import OpenTelemetry components
from otel_config import init_otel, get_tracer, get_meter, get_current_trace_id, get_current_span_id, get_request_id
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode, get_current_span

# Configure structured logging for OpenTelemetry integration
class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with OpenTelemetry correlation"""
    
    def format(self, record):
        # Get current span context
        span = get_current_span()
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'service': 'flask-service',
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add trace correlation if available
        if span and span.is_recording():
            span_context = span.get_span_context()
            log_entry.update({
                'trace_id': f"{span_context.trace_id:032x}",
                'span_id': f"{span_context.span_id:016x}",
                'trace_flags': span_context.trace_flags
            })
        
        # Add request context if available
        request_id = get_request_id()
        if request_id:
            log_entry['request_id'] = request_id
        
        # Add any extra fields from the log record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 'msecs', 
                          'relativeCreated', 'thread', 'threadName', 'processName', 'process']:
                log_entry[key] = value
        
        return json.dumps(log_entry)

# Configure logging with structured format
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)

# Get logger and set structured formatter
logger = logging.getLogger(__name__)
for handler in logger.handlers:
    handler.setFormatter(StructuredFormatter())

# Also configure root logger for consistent formatting across all modules
root_logger = logging.getLogger()
for handler in root_logger.handlers:
    handler.setFormatter(StructuredFormatter())

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
    start_time = time.time()
    
    # Log request start
    logger.info("Endpoint accessed", extra={
        'endpoint': '/',
        'method': 'GET',
        'action': 'request_start',
        'user_agent': request.headers.get('User-Agent', 'unknown'),
        'remote_addr': request.remote_addr
    })
    
    # Get current trace ID
    current_trace_id = get_current_trace_id()
    
    response = {
        'message': 'Welcome to Simple Flask API!',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'trace_id': current_trace_id  # Include trace ID in response
    }
    
    # Log successful response
    duration_ms = round((time.time() - start_time) * 1000, 2)
    logger.info("Endpoint completed successfully", extra={
        'endpoint': '/',
        'method': 'GET',
        'action': 'request_success',
        'status_code': 200,
        'duration_ms': duration_ms,
        'response_size': len(json.dumps(response))
    })
    
    return jsonify(response)

# Health check endpoint (excluded from detailed tracing)
@app.route('/health')
def health_check():
    start_time = time.time()
    
    # Log health check access
    logger.info("Health check accessed", extra={
        'endpoint': '/health',
        'method': 'GET',
        'action': 'health_check',
        'items_count': len(items_db)
    })
    
    response = {
        'status': 'healthy',
        'service': 'flask-service',
        'timestamp': datetime.now().isoformat(),
        'items_count': len(items_db)
    }
    
    # Log successful health check
    duration_ms = round((time.time() - start_time) * 1000, 2)
    logger.info("Health check completed", extra={
        'endpoint': '/health',
        'method': 'GET',
        'action': 'health_check_success',
        'status_code': 200,
        'duration_ms': duration_ms,
        'service_status': 'healthy'
    })
    
    return jsonify(response)

# Get all items
@app.route('/items', methods=['GET'])
def get_items():
    with tracer.start_as_current_span("get_items") as span:
        start_time = time.time()
        
        # Log request start
        logger.info("Getting all items", extra={
            'endpoint': '/items',
            'method': 'GET',
            'action': 'get_all_items_start',
            'current_items_count': len(items_db)
        })
        
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
        
        # Log successful response
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info("Successfully retrieved all items", extra={
            'endpoint': '/items',
            'method': 'GET',
            'action': 'get_all_items_success',
            'status_code': 200,
            'items_returned': len(items_list),
            'duration_ms': duration_ms,
            'response_size': len(json.dumps(response))
        })
        
        return jsonify(response)

# Get item by ID
@app.route('/items/<item_id>', methods=['GET'])
def get_item(item_id):
    with tracer.start_as_current_span("get_item") as span:
        start_time = time.time()
        
        # Log request start
        logger.info("Getting item by ID", extra={
            'endpoint': '/items/<item_id>',
            'method': 'GET',
            'action': 'get_item_start',
            'item_id': item_id,
            'total_items': len(items_db)
        })
        
        span.set_attribute("endpoint", "get_item")
        span.set_attribute("item.id", item_id)
        
        if item_id not in items_db:
            # Log item not found
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.warning("Item not found", extra={
                'endpoint': '/items/<item_id>',
                'method': 'GET',
                'action': 'get_item_not_found',
                'item_id': item_id,
                'status_code': 404,
                'duration_ms': duration_ms,
                'error': 'Item not found'
            })
            
            span.record_exception(Exception("Item not found"))
            span.set_status(Status(StatusCode.ERROR, "Item not found"))
            return jsonify({'error': 'Item not found'}), 404
        
        item = items_db[item_id]
        span.set_attribute("item.name", item['name'])
        span.set_attribute("item.price", item['price'])
        
        # Record metrics
        item_operations.add(1, {"operation": "get", "endpoint": "get_item"})
        
        # Log successful response
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info("Successfully retrieved item", extra={
            'endpoint': '/items/<item_id>',
            'method': 'GET',
            'action': 'get_item_success',
            'item_id': item_id,
            'item_name': item['name'],
            'item_price': item['price'],
            'status_code': 200,
            'duration_ms': duration_ms,
            'response_size': len(json.dumps(item))
        })
        
        return jsonify(item)

# Create new item
@app.route('/items', methods=['POST'])
def create_item():
    with tracer.start_as_current_span("create_item") as span:
        start_time = time.time()
        
        data = request.get_json()
        
        # Log request start
        logger.info("Creating new item", extra={
            'endpoint': '/items',
            'method': 'POST',
            'action': 'create_item_start',
            'request_data': data if data else {},
            'current_items_count': len(items_db)
        })
        
        span.set_attribute("endpoint", "create_item")
        
        # Validate input data
        is_valid, error_message = validate_item_data(data)
        if not is_valid:
            # Log validation error
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error("Item creation failed - validation error", extra={
                'endpoint': '/items',
                'method': 'POST',
                'action': 'create_item_validation_error',
                'error': error_message,
                'status_code': 400,
                'duration_ms': duration_ms,
                'request_data': data if data else {}
            })
            
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
        
        # Log successful creation
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info("Successfully created new item", extra={
            'endpoint': '/items',
            'method': 'POST',
            'action': 'create_item_success',
            'item_id': item_id,
            'item_name': data['name'],
            'item_price': data['price'],
            'status_code': 201,
            'duration_ms': duration_ms,
            'total_items': len(items_db),
            'response_size': len(json.dumps(new_item))
        })
        
        return jsonify(new_item), 201

# Update item
@app.route('/items/<item_id>', methods=['PUT'])
def update_item(item_id):
    with tracer.start_as_current_span("update_item") as span:
        start_time = time.time()
        
        # Log request start
        logger.info("Updating item", extra={
            'endpoint': '/items/<item_id>',
            'method': 'PUT',
            'action': 'update_item_start',
            'item_id': item_id
        })
        
        span.set_attribute("endpoint", "update_item")
        span.set_attribute("item.id", item_id)
        
        if item_id not in items_db:
            # Log item not found
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.warning("Cannot update - item not found", extra={
                'endpoint': '/items/<item_id>',
                'method': 'PUT',
                'action': 'update_item_not_found',
                'item_id': item_id,
                'status_code': 404,
                'duration_ms': duration_ms,
                'error': 'Item not found'
            })
            
            span.record_exception(Exception("Item not found"))
            span.set_status(Status(StatusCode.ERROR, "Item not found"))
            return jsonify({'error': 'Item not found'}), 404
        
        data = request.get_json()
        
        # Validate input data
        is_valid, error_message = validate_item_data(data)
        if not is_valid:
            # Log validation error
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error("Item update failed - validation error", extra={
                'endpoint': '/items/<item_id>',
                'method': 'PUT',
                'action': 'update_item_validation_error',
                'item_id': item_id,
                'error': error_message,
                'status_code': 400,
                'duration_ms': duration_ms,
                'request_data': data if data else {}
            })
            
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
        
        # Log successful update
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info("Successfully updated item", extra={
            'endpoint': '/items/<item_id>',
            'method': 'PUT',
            'action': 'update_item_success',
            'item_id': item_id,
            'old_name': old_item_name,
            'new_name': data['name'],
            'new_price': data['price'],
            'status_code': 200,
            'duration_ms': duration_ms,
            'response_size': len(json.dumps(updated_item))
        })
        
        return jsonify(updated_item)

# Delete item
@app.route('/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    with tracer.start_as_current_span("delete_item") as span:
        start_time = time.time()
        
        # Log request start
        logger.info("Deleting item", extra={
            'endpoint': '/items/<item_id>',
            'method': 'DELETE',
            'action': 'delete_item_start',
            'item_id': item_id,
            'current_items_count': len(items_db)
        })
        
        span.set_attribute("endpoint", "delete_item")
        span.set_attribute("item.id", item_id)
        
        if item_id not in items_db:
            # Log item not found
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.warning("Cannot delete - item not found", extra={
                'endpoint': '/items/<item_id>',
                'method': 'DELETE',
                'action': 'delete_item_not_found',
                'item_id': item_id,
                'status_code': 404,
                'duration_ms': duration_ms,
                'error': 'Item not found'
            })
            
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
        
        # Log successful deletion
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info("Successfully deleted item", extra={
            'endpoint': '/items/<item_id>',
            'method': 'DELETE',
            'action': 'delete_item_success',
            'item_id': item_id,
            'deleted_item_name': deleted_item['name'],
            'deleted_item_price': deleted_item['price'],
            'status_code': 200,
            'duration_ms': duration_ms,
            'remaining_items': len(items_db),
            'response_size': len(json.dumps(response))
        })
        
        return jsonify(response)

# Search items by name or description
@app.route('/items/search/<query>', methods=['GET'])
def search_items(query):
    with tracer.start_as_current_span("search_items") as span:
        start_time = time.time()
        
        # Log search request start
        logger.info("Searching items", extra={
            'endpoint': '/items/search/<query>',
            'method': 'GET',
            'action': 'search_items_start',
            'search_query': query,
            'total_items': len(items_db)
        })
        
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
        
        # Log search results
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info("Search completed", extra={
            'endpoint': '/items/search/<query>',
            'method': 'GET',
            'action': 'search_items_success',
            'search_query': query,
            'results_count': len(matching_items),
            'status_code': 200,
            'duration_ms': duration_ms,
            'response_size': len(json.dumps(response))
        })
        
        return jsonify(response)

# Get items by availability status
@app.route('/items/status/<status>', methods=['GET'])
def get_items_by_status(status):
    with tracer.start_as_current_span("get_items_by_status") as span:
        start_time = time.time()
        
        # Log filter request start
        logger.info("Filtering items by status", extra={
            'endpoint': '/items/status/<status>',
            'method': 'GET',
            'action': 'filter_items_start',
            'filter_status': status,
            'total_items': len(items_db)
        })
        
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
        
        # Log filter results
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info("Status filter completed", extra={
            'endpoint': '/items/status/<status>',
            'method': 'GET',
            'action': 'filter_items_success',
            'filter_status': status,
            'results_count': len(filtered_items),
            'available_items': len([i for i in items_db.values() if i['is_available']]),
            'unavailable_items': len([i for i in items_db.values() if not i['is_available']]),
            'status_code': 200,
            'duration_ms': duration_ms,
            'response_size': len(json.dumps(response))
        })
        
        return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
