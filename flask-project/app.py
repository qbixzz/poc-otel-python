from flask import Flask, request, jsonify
import uuid
from datetime import datetime

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
    return jsonify({
        'message': 'Welcome to Simple Flask API!',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'flask-service',
        'timestamp': datetime.utcnow().isoformat()
    })

# Get all items
@app.route('/items', methods=['GET'])
def get_items():
    items_list = list(items_db.values())
    return jsonify({
        'items': items_list,
        'count': len(items_list)
    })

# Get item by ID
@app.route('/items/<item_id>', methods=['GET'])
def get_item(item_id):
    if item_id not in items_db:
        return jsonify({'error': 'Item not found'}), 404
    
    return jsonify(items_db[item_id])

# Create new item
@app.route('/items', methods=['POST'])
def create_item():
    data = request.get_json()
    
    # Validate input data
    is_valid, error_message = validate_item_data(data)
    if not is_valid:
        return jsonify({'error': error_message}), 400
    
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
    return jsonify(new_item), 201

# Update item
@app.route('/items/<item_id>', methods=['PUT'])
def update_item(item_id):
    if item_id not in items_db:
        return jsonify({'error': 'Item not found'}), 404
    
    data = request.get_json()
    
    # Validate input data
    is_valid, error_message = validate_item_data(data)
    if not is_valid:
        return jsonify({'error': error_message}), 400
    
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
    return jsonify(updated_item)

# Delete item
@app.route('/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    if item_id not in items_db:
        return jsonify({'error': 'Item not found'}), 404
    
    deleted_item = items_db.pop(item_id)
    return jsonify({
        'message': f'Item {deleted_item["name"]} deleted successfully',
        'deleted_item': deleted_item
    })

# Search items by name or description
@app.route('/items/search/<query>', methods=['GET'])
def search_items(query):
    query_lower = query.lower()
    matching_items = [
        item for item in items_db.values()
        if query_lower in item['name'].lower() or query_lower in item.get('description', '').lower()
    ]
    
    return jsonify({
        'items': matching_items,
        'count': len(matching_items),
        'query': query
    })

# Get items by availability status
@app.route('/items/status/<status>', methods=['GET'])
def get_items_by_status(status):
    is_available = status.lower() == 'available'
    filtered_items = [
        item for item in items_db.values()
        if item['is_available'] == is_available
    ]
    
    return jsonify({
        'items': filtered_items,
        'count': len(filtered_items),
        'status': status
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
