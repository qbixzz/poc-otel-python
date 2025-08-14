#!/usr/bin/env python3
"""
Test script for Flask application
Run this after starting the Flask server (python app.py)
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_flask():
    print("🌶️ Testing Flask endpoints...\n")
    
    # Test root endpoint
    print("1. Testing root endpoint:")
    response = requests.get(f"{BASE_URL}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}\n")
    
    # Test health check
    print("2. Testing health check:")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}\n")
    
    # Test create item
    print("3. Creating a new item:")
    item_data = {
        "name": "Test Smartphone",
        "description": "A flagship smartphone with amazing features",
        "price": 899.99,
        "is_available": True
    }
    response = requests.post(f"{BASE_URL}/items", json=item_data)
    print(f"   Status: {response.status_code}")
    created_item = response.json()
    print(f"   Response: {json.dumps(created_item, indent=2)}\n")
    
    # Save item ID for further tests
    item_id = created_item["id"]
    
    # Create another item for testing
    print("4. Creating another item:")
    item_data2 = {
        "name": "Wireless Headphones",
        "description": "Premium noise-cancelling headphones",
        "price": 299.99,
        "is_available": False
    }
    response = requests.post(f"{BASE_URL}/items", json=item_data2)
    print(f"   Status: {response.status_code}")
    item_id2 = response.json()["id"]
    
    # Test get all items
    print("\n5. Getting all items:")
    response = requests.get(f"{BASE_URL}/items")
    print(f"   Status: {response.status_code}")
    all_items = response.json()
    print(f"   Items count: {all_items['count']}\n")
    
    # Test get item by ID
    print("6. Getting item by ID:")
    response = requests.get(f"{BASE_URL}/items/{item_id}")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}\n")
    
    # Test update item
    print("7. Updating item:")
    update_data = {
        "name": "Updated Flagship Smartphone",
        "description": "The latest flagship smartphone with advanced AI",
        "price": 999.99,
        "is_available": True
    }
    response = requests.put(f"{BASE_URL}/items/{item_id}", json=update_data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}\n")
    
    # Test search
    print("8. Searching items:")
    response = requests.get(f"{BASE_URL}/items/search/smartphone")
    print(f"   Status: {response.status_code}")
    search_result = response.json()
    print(f"   Found {search_result['count']} items\n")
    
    # Test get available items
    print("9. Getting available items:")
    response = requests.get(f"{BASE_URL}/items/status/available")
    print(f"   Status: {response.status_code}")
    available_items = response.json()
    print(f"   Available items count: {available_items['count']}\n")
    
    # Test get unavailable items
    print("10. Getting unavailable items:")
    response = requests.get(f"{BASE_URL}/items/status/unavailable")
    print(f"   Status: {response.status_code}")
    unavailable_items = response.json()
    print(f"   Unavailable items count: {unavailable_items['count']}\n")
    
    # Test delete item
    print("11. Deleting first item:")
    response = requests.delete(f"{BASE_URL}/items/{item_id}")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}\n")
    
    print("✅ Flask tests completed!")

if __name__ == "__main__":
    try:
        test_flask()
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed! Make sure the Flask server is running:")
        print("   python app.py")
    except Exception as e:
        print(f"❌ Test failed: {e}")
