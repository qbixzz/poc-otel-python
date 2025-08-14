#!/usr/bin/env python3
"""
Test script for FastAPI application
Run this after starting the FastAPI server (python main.py)
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_fastapi():
    print("🚀 Testing FastAPI endpoints...\n")
    
    # Test root endpoint
    print("1. Testing root endpoint:")
    response = requests.get(f"{BASE_URL}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")
    
    # Test health check
    print("2. Testing health check:")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")
    
    # Test create item
    print("3. Creating a new item:")
    item_data = {
        "name": "Test Laptop",
        "description": "A powerful gaming laptop",
        "price": 1299.99,
        "is_available": True
    }
    response = requests.post(f"{BASE_URL}/items", json=item_data)
    print(f"   Status: {response.status_code}")
    created_item = response.json()
    print(f"   Response: {json.dumps(created_item, indent=2)}\n")
    
    # Save item ID for further tests
    item_id = created_item["id"]
    
    # Test get all items
    print("4. Getting all items:")
    response = requests.get(f"{BASE_URL}/items")
    print(f"   Status: {response.status_code}")
    print(f"   Items count: {len(response.json())}\n")
    
    # Test get item by ID
    print("5. Getting item by ID:")
    response = requests.get(f"{BASE_URL}/items/{item_id}")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}\n")
    
    # Test update item
    print("6. Updating item:")
    update_data = {
        "name": "Updated Gaming Laptop",
        "description": "An even more powerful gaming laptop",
        "price": 1499.99,
        "is_available": True
    }
    response = requests.put(f"{BASE_URL}/items/{item_id}", json=update_data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}\n")
    
    # Test search
    print("7. Searching items:")
    response = requests.get(f"{BASE_URL}/items/search/gaming")
    print(f"   Status: {response.status_code}")
    print(f"   Found items: {len(response.json())}\n")
    
    # Test delete item
    print("8. Deleting item:")
    response = requests.delete(f"{BASE_URL}/items/{item_id}")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")
    
    print("✅ FastAPI tests completed!")
    print(f"📖 Visit {BASE_URL}/docs for interactive API documentation")

if __name__ == "__main__":
    try:
        test_fastapi()
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed! Make sure the FastAPI server is running:")
        print("   python main.py")
    except Exception as e:
        print(f"❌ Test failed: {e}")
