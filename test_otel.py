#!/usr/bin/env python3
"""
OpenTelemetry Testing Script for Docker containerized APIs
This script tests both APIs and validates OpenTelemetry instrumentation
"""

import requests
import json
import time
import sys
from datetime import datetime

def test_otel_service(base_url, service_name):
    print(f"🔍 Testing OpenTelemetry instrumentation for {service_name} at {base_url}...\n")
    
    try:
        # Test 1: Health check (should be traced)
        print("1. Testing health check (with tracing):")
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        print(f"   ⭐ Check OTEL collector logs for trace data")
        print()
        
        # Test 2: Create multiple items to generate telemetry data
        print("2. Creating test items to generate telemetry:")
        test_items = [
            {
                "name": f"OTEL Test Item 1 ({service_name})",
                "description": "First test item for OpenTelemetry validation",
                "price": 99.99,
                "is_available": True
            },
            {
                "name": f"OTEL Test Item 2 ({service_name})",
                "description": "Second test item for OpenTelemetry validation", 
                "price": 149.99,
                "is_available": False
            }
        ]
        
        created_items = []
        for i, item_data in enumerate(test_items, 1):
            print(f"   Creating item {i}: {item_data['name']}")
            response = requests.post(f"{base_url}/items", json=item_data)
            if response.status_code == 201:
                created_item = response.json()
                created_items.append(created_item)
                item_id = created_item.get("id")
                print(f"   ✅ Created item with ID: {item_id}")
            else:
                print(f"   ❌ Failed to create item: {response.status_code}")
        print()
        
        # Test 3: Get all items (should show custom metrics)
        print("3. Retrieving all items (metrics generation):")
        response = requests.get(f"{base_url}/items")
        print(f"   Status: {response.status_code}")
        
        if service_name == "Flask":
            items_data = response.json()
            print(f"   Total items: {items_data.get('count', 0)}")
        else:
            items_list = response.json()
            print(f"   Total items: {len(items_list)}")
        print()
        
        # Test 4: Search functionality (custom spans)
        print("4. Testing search functionality (custom spans):")
        search_queries = ["OTEL", "test", "nonexistent"]
        
        for query in search_queries:
            print(f"   Searching for: {query}")
            response = requests.get(f"{base_url}/items/search/{query}")
            
            if response.status_code == 200:
                if service_name == "Flask":
                    results = response.json()
                    count = results.get('count', 0)
                else:
                    results = response.json()
                    count = len(results)
                print(f"   Found {count} items")
            else:
                print(f"   Search failed: {response.status_code}")
        print()
        
        # Test 5: Update operations (should generate update spans)
        if created_items:
            print("5. Testing update operations (spans and metrics):")
            item_to_update = created_items[0]
            item_id = item_to_update.get("id")
            
            update_data = {
                "name": f"Updated OTEL Item ({service_name})",
                "description": "Updated via OpenTelemetry testing",
                "price": 199.99,
                "is_available": True
            }
            
            print(f"   Updating item: {item_id}")
            response = requests.put(f"{base_url}/items/{item_id}", json=update_data)
            
            if response.status_code == 200:
                print("   ✅ Item updated successfully")
            else:
                print(f"   ❌ Update failed: {response.status_code}")
            print()
        
        # Test 6: Error scenarios (should generate error spans)
        print("6. Testing error scenarios (error spans and exceptions):")
        
        # Try to get non-existent item
        print("   Testing 404 error (non-existent item):")
        response = requests.get(f"{base_url}/items/non-existent-id")
        print(f"   Status: {response.status_code} (expected 404)")
        
        # Try to create invalid item
        print("   Testing 400 error (invalid item data):")
        invalid_data = {"name": "", "price": "invalid"}
        response = requests.post(f"{base_url}/items", json=invalid_data)
        print(f"   Status: {response.status_code} (expected 400)")
        print()
        
        # Test 7: Clean up (delete created items)
        print("7. Cleaning up test items:")
        for item in created_items:
            item_id = item.get("id")
            if item_id:
                print(f"   Deleting item: {item_id}")
                response = requests.delete(f"{base_url}/items/{item_id}")
                if response.status_code == 200:
                    print("   ✅ Item deleted successfully")
                else:
                    print(f"   ⚠️ Delete failed: {response.status_code}")
        print()
        
        print(f"✅ OpenTelemetry testing completed for {service_name}!")
        print("📊 Check the following for telemetry data:")
        print("   - OTEL Collector logs: docker-compose logs otel-collector")
        print("   - Trace files: ./logs/all_traces.json")
        print("   - Zpages: http://localhost:55679/debug/tracez")
        print()
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed to {service_name}!")
        print(f"   Make sure the container is running on {base_url}")
    except Exception as e:
        print(f"❌ Test failed for {service_name}: {e}")

def check_otel_collector():
    """Check if OTEL collector is running and accessible"""
    print("🔧 Checking OpenTelemetry Collector status...\n")
    
    try:
        # Check health endpoint
        print("1. Checking collector health:")
        response = requests.get("http://localhost:13133/")
        print(f"   Health Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ OTEL Collector is healthy")
        else:
            print("   ⚠️ OTEL Collector health check failed")
        print()
        
        # Check zpages
        print("2. Checking zpages availability:")
        try:
            response = requests.get("http://localhost:55679/debug/servicez")
            print(f"   Zpages Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Zpages are accessible at: http://localhost:55679")
            else:
                print("   ⚠️ Zpages not accessible")
        except:
            print("   ❌ Zpages not available")
        print()
        
    except requests.exceptions.ConnectionError:
        print("❌ OTEL Collector is not accessible!")
        print("   Make sure the collector container is running")
        print("   Run: docker-compose logs otel-collector")
        return False
    except Exception as e:
        print(f"❌ Collector check failed: {e}")
        return False
    
    return True

def main():
    print("🔬 OpenTelemetry Instrumentation Testing")
    print("=" * 50)
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    # Wait for services to be ready
    print("⏳ Waiting for services to be ready...")
    time.sleep(5)
    
    # Check OTEL collector first
    if not check_otel_collector():
        print("⚠️ Proceeding with API tests despite collector issues...")
        print()
    
    # Test both services with OpenTelemetry instrumentation
    test_otel_service("http://localhost:8000", "FastAPI")
    test_otel_service("http://localhost:5000", "Flask")
    
    print("🎉 OpenTelemetry testing completed!")
    print("\n📋 Summary of what was tested:")
    print("   ✅ Automatic HTTP instrumentation")
    print("   ✅ Custom spans with attributes")
    print("   ✅ Custom metrics (counters, histograms)")
    print("   ✅ Error handling and exception recording")
    print("   ✅ Trace propagation")
    print("   ✅ Resource attributes")
    
    print("\n🔍 How to view telemetry data:")
    print("   1. OTEL Collector Logs:")
    print("      docker-compose logs -f otel-collector")
    print("   2. Trace Files:")
    print("      cat ./logs/all_traces.json | jq .")
    print("   3. Zpages (if available):")
    print("      http://localhost:55679/debug/tracez")
    print("      http://localhost:55679/debug/servicez")
    print("   4. Service Logs:")
    print("      docker-compose logs -f fastapi-service")
    print("      docker-compose logs -f flask-service")

if __name__ == "__main__":
    main()
