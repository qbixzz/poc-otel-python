#!/usr/bin/env python3
"""
Test script for all three Python API services:
1. FastAPI service (port 8000)
2. Flask service (port 5000) 
3. EDOT Flask service (port 5001)
"""

import requests
import json
import time

def test_service(service_name, base_url, port):
    """Test a service with basic CRUD operations"""
    print(f"\n{'='*50}")
    print(f"Testing {service_name} on {base_url}:{port}")
    print(f"{'='*50}")
    
    try:
        # Test health endpoint
        health_response = requests.get(f"{base_url}:{port}/health")
        print(f"✅ Health check: {health_response.status_code}")
        
        # Test root endpoint
        root_response = requests.get(f"{base_url}:{port}/")
        print(f"✅ Root endpoint: {root_response.status_code}")
        
        # Test create item
        new_item = {
            "name": f"Test Item from {service_name}",
            "description": f"Created via {service_name} API",
            "price": 99.99,
            "is_available": True
        }
        
        create_response = requests.post(
            f"{base_url}:{port}/items",
            json=new_item,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Create item: {create_response.status_code}")
        
        if create_response.status_code == 201:
            created_item = create_response.json()
            item_id = created_item.get('id')
            
            # Test get item by ID
            if item_id:
                get_response = requests.get(f"{base_url}:{port}/items/{item_id}")
                print(f"✅ Get item: {get_response.status_code}")
                
                # Test update item
                updated_data = {
                    "name": f"Updated {service_name} Item",
                    "description": "Updated description",
                    "price": 149.99,
                    "is_available": False
                }
                
                update_response = requests.put(
                    f"{base_url}:{port}/items/{item_id}",
                    json=updated_data,
                    headers={"Content-Type": "application/json"}
                )
                print(f"✅ Update item: {update_response.status_code}")
                
                # Test delete item
                delete_response = requests.delete(f"{base_url}:{port}/items/{item_id}")
                print(f"✅ Delete item: {delete_response.status_code}")
        
        # Test get all items
        all_items_response = requests.get(f"{base_url}:{port}/items")
        print(f"✅ Get all items: {all_items_response.status_code}")
        
        print(f"🎉 {service_name} tests completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print(f"❌ {service_name} is not accessible at {base_url}:{port}")
    except Exception as e:
        print(f"❌ Error testing {service_name}: {str(e)}")

def main():
    print("🚀 Starting API tests for all three services")
    print("Make sure Docker Compose is running with all services")
    
    # Wait a bit for services to start up
    print("⏳ Waiting 5 seconds for services to initialize...")
    time.sleep(5)
    
    # Test all three services
    services = [
        ("FastAPI", "http://localhost", 8000),
        ("Flask", "http://localhost", 5000),
        ("EDOT Flask", "http://localhost", 5001)
    ]
    
    for service_name, base_url, port in services:
        test_service(service_name, base_url, port)
    
    print(f"\n{'='*50}")
    print("🏁 All API tests completed!")
    print("Check the OpenTelemetry collector logs for trace data.")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
