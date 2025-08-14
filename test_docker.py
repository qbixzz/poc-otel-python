#!/usr/bin/env python3
"""
Test script for Docker containerized APIs
Run this after starting the containers with docker-compose
"""

import requests
import json
import time
import sys

def test_service(base_url, service_name):
    print(f"🐳 Testing {service_name} at {base_url}...\n")
    
    try:
        # Test root endpoint
        print("1. Testing root endpoint:")
        response = requests.get(f"{base_url}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}\n")
        
        # Test health check
        print("2. Testing health check:")
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}\n")
        
        # Test create item
        print("3. Creating a new item:")
        item_data = {
            "name": f"Docker Test Item ({service_name})",
            "description": f"Test item created in {service_name} container",
            "price": 199.99,
            "is_available": True
        }
        response = requests.post(f"{base_url}/items", json=item_data)
        print(f"   Status: {response.status_code}")
        created_item = response.json()
        print(f"   Response: {json.dumps(created_item, indent=2)}\n")
        
        # Save item ID for further tests
        item_id = created_item.get("id")
        if not item_id:
            print("   ⚠️ Could not get item ID from response")
            return
        
        # Test get all items
        print("4. Getting all items:")
        response = requests.get(f"{base_url}/items")
        print(f"   Status: {response.status_code}")
        items_data = response.json()
        
        if isinstance(items_data, list):
            print(f"   Items count: {len(items_data)}")
        elif isinstance(items_data, dict) and 'count' in items_data:
            print(f"   Items count: {items_data['count']}")
        else:
            print(f"   Response: {json.dumps(items_data, indent=2)}")
        print()
        
        # Test search
        print("5. Searching items:")
        response = requests.get(f"{base_url}/items/search/docker")
        print(f"   Status: {response.status_code}")
        search_data = response.json()
        
        if isinstance(search_data, list):
            print(f"   Found items: {len(search_data)}")
        elif isinstance(search_data, dict) and 'count' in search_data:
            print(f"   Found items: {search_data['count']}")
        print()
        
        # Test delete item
        print("6. Deleting test item:")
        response = requests.delete(f"{base_url}/items/{item_id}")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}\n")
        
        print(f"✅ {service_name} container tests completed!\n")
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed to {service_name}!")
        print(f"   Make sure the container is running on {base_url}")
    except Exception as e:
        print(f"❌ Test failed for {service_name}: {e}")

def test_nginx_gateway():
    print("🌐 Testing Nginx Gateway...\n")
    
    try:
        # Test gateway root
        print("1. Testing gateway root:")
        response = requests.get("http://localhost/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}\n")
        
        # Test gateway health
        print("2. Testing gateway health:")
        response = requests.get("http://localhost/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}\n")
        
        # Test FastAPI through gateway
        print("3. Testing FastAPI through gateway:")
        response = requests.get("http://localhost/fastapi/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}\n")
        
        # Test Flask through gateway
        print("4. Testing Flask through gateway:")
        response = requests.get("http://localhost/flask/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}\n")
        
        print("✅ Nginx Gateway tests completed!\n")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed to Nginx Gateway!")
        print("   Make sure nginx container is running on port 80")
    except Exception as e:
        print(f"❌ Gateway test failed: {e}")

def main():
    print("🐳 Docker Container API Testing\n")
    print("=" * 50)
    
    # Wait a moment for services to be ready
    print("⏳ Waiting for services to be ready...")
    time.sleep(3)
    
    # Test both services directly
    test_service("http://localhost:8000", "FastAPI")
    test_service("http://localhost:5000", "Flask")
    
    # Check if we should test nginx gateway
    if len(sys.argv) > 1 and sys.argv[1] == "--with-nginx":
        test_nginx_gateway()
    
    print("🎉 All container tests completed!")
    print("\nDirect Access URLs:")
    print("- FastAPI: http://localhost:8000")
    print("- FastAPI Docs: http://localhost:8000/docs")
    print("- Flask: http://localhost:5000")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--with-nginx":
        print("\nGateway Access URLs:")
        print("- Gateway: http://localhost/")
        print("- FastAPI via Gateway: http://localhost/fastapi/")
        print("- Flask via Gateway: http://localhost/flask/")

if __name__ == "__main__":
    main()
