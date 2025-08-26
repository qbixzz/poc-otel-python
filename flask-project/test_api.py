#!/usr/bin/env python3
"""
Enhanced test script for Flask application with integrated OpenTelemetry logging
Run this after starting the Flask server (python app.py)
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:5000"

def test_flask_with_integrated_logging():
    print("🌶️ Testing Flask endpoints with integrated OpenTelemetry logging...\n")
    
    try:
        # Test 1: Root endpoint
        print("1. Testing root endpoint with logging:")
        response = requests.get(f"{BASE_URL}/")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Trace ID: {data.get('trace_id', 'Not available')}")
        print(f"   Message: {data.get('message')}\n")
        
        # Test 2: Health check
        print("2. Testing health check with logging:")
        response = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Service Status: {response.json().get('status')}\n")
        
        # Test 3: Create item
        print("3. Creating a new item (with detailed logging):")
        item_data = {
            "name": "Test Smartphone Pro",
            "description": "A flagship smartphone with amazing features and AI capabilities",
            "price": 899.99,
            "is_available": True
        }
        response = requests.post(f"{BASE_URL}/items", json=item_data)
        print(f"   Status: {response.status_code}")
        created_item = response.json()
        item_id = created_item["id"]
        print(f"   Created Item ID: {item_id}")
        print(f"   Created Item Name: {created_item['name']}\n")
        
        # Test 4: Create another item
        print("4. Creating another item:")
        item_data2 = {
            "name": "Wireless Noise-Cancelling Headphones",
            "description": "Premium over-ear headphones with active noise cancellation",
            "price": 299.99,
            "is_available": False
        }
        response = requests.post(f"{BASE_URL}/items", json=item_data2)
        print(f"   Status: {response.status_code}")
        item_id2 = response.json()["id"]
        print(f"   Created Item ID: {item_id2}\n")
        
        # Test 5: Get all items
        print("5. Getting all items (with count logging):")
        response = requests.get(f"{BASE_URL}/items")
        print(f"   Status: {response.status_code}")
        all_items = response.json()
        print(f"   Total Items: {all_items['count']}\n")
        
        # Test 6: Get item by ID
        print("6. Getting item by ID (with detailed logging):")
        response = requests.get(f"{BASE_URL}/items/{item_id}")
        print(f"   Status: {response.status_code}")
        item = response.json()
        print(f"   Retrieved: {item['name']} - ${item['price']}\n")
        
        # Test 7: Update item
        print("7. Updating item (with before/after logging):")
        update_data = {
            "name": "Updated Flagship Smartphone Pro Max",
            "description": "The latest flagship smartphone with advanced AI and 5G",
            "price": 1099.99,
            "is_available": True
        }
        response = requests.put(f"{BASE_URL}/items/{item_id}", json=update_data)
        print(f"   Status: {response.status_code}")
        updated_item = response.json()
        print(f"   Updated: {updated_item['name']} - ${updated_item['price']}\n")
        
        # Test 8: Search items
        print("8. Searching items (with query logging):")
        response = requests.get(f"{BASE_URL}/items/search/smartphone")
        print(f"   Status: {response.status_code}")
        search_result = response.json()
        print(f"   Search Query: '{search_result['query']}'")
        print(f"   Results Found: {search_result['count']}\n")
        
        # Test 9: Filter by availability
        print("9. Getting available items (with filter logging):")
        response = requests.get(f"{BASE_URL}/items/status/available")
        print(f"   Status: {response.status_code}")
        available_items = response.json()
        print(f"   Available Items: {available_items['count']}\n")
        
        # Test 10: Filter by unavailability
        print("10. Getting unavailable items:")
        response = requests.get(f"{BASE_URL}/items/status/unavailable")
        print(f"   Status: {response.status_code}")
        unavailable_items = response.json()
        print(f"   Unavailable Items: {unavailable_items['count']}\n")
        
        # Test 11: Test error case - get non-existent item
        print("11. Testing error case - get non-existent item:")
        fake_id = "non-existent-id-12345"
        response = requests.get(f"{BASE_URL}/items/{fake_id}")
        print(f"   Status: {response.status_code}")
        print(f"   Error: {response.json().get('error')}\n")
        
        # Test 12: Test validation error
        print("12. Testing validation error (missing required field):")
        bad_data = {"description": "Item without name"}
        response = requests.post(f"{BASE_URL}/items", json=bad_data)
        print(f"   Status: {response.status_code}")
        print(f"   Error: {response.json().get('error')}\n")
        
        # Test 13: Delete item
        print("13. Deleting item (with deletion logging):")
        response = requests.delete(f"{BASE_URL}/items/{item_id}")
        print(f"   Status: {response.status_code}")
        delete_response = response.json()
        print(f"   Deleted: {delete_response['deleted_item']['name']}\n")
        
        print("✅ All Flask tests with integrated OpenTelemetry logging completed!")
        print("\n📊 Check the following for logs:")
        print("   - Console output (structured JSON logs)")
        print("   - OpenTelemetry Collector logs")
        print("   - Kibana APM traces with correlated logs")
        print("   - Each request should have trace_id correlation")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed! Make sure the Flask server is running:")
        print("   python app.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_flask_with_integrated_logging()
