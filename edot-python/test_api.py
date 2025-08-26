import requests
import json
import time

# EDOT Flask API endpoint
BASE_URL = "http://localhost:5001"

def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_root_endpoint():
    """Test root endpoint"""
    print("\nTesting root endpoint...")
    try:
        response = requests.get(BASE_URL)
        print(f"Root endpoint status: {response.status_code}")
        data = response.json()
        print(f"Message: {data.get('message')}")
        print(f"Agent: {data.get('agent')}")
        return response.status_code == 200
    except Exception as e:
        print(f"Root endpoint test failed: {e}")
        return False

def test_crud_operations():
    """Test CRUD operations"""
    print("\nTesting CRUD operations...")
    
    # Test data
    test_item = {
        "name": "EDOT Test Item",
        "description": "Testing EDOT Flask API with automatic instrumentation",
        "price": 99.99,
        "is_available": True
    }
    
    try:
        # CREATE - Create new item
        print("1. Creating item...")
        response = requests.post(f"{BASE_URL}/items", json=test_item)
        print(f"Create status: {response.status_code}")
        if response.status_code == 201:
            created_item = response.json()
            item_id = created_item["id"]
            print(f"Created item ID: {item_id}")
        else:
            print("Failed to create item")
            return False
        
        # READ - Get all items
        print("\n2. Getting all items...")
        response = requests.get(f"{BASE_URL}/items")
        print(f"Get all items status: {response.status_code}")
        items_data = response.json()
        print(f"Total items: {items_data.get('count')}")
        
        # READ - Get specific item
        print(f"\n3. Getting item by ID: {item_id}")
        response = requests.get(f"{BASE_URL}/items/{item_id}")
        print(f"Get item status: {response.status_code}")
        if response.status_code == 200:
            item = response.json()
            print(f"Item name: {item.get('name')}")
        
        # UPDATE - Update the item
        print(f"\n4. Updating item: {item_id}")
        updated_data = {
            "name": "EDOT Updated Item",
            "description": "Updated with EDOT tracing",
            "price": 149.99,
            "is_available": False
        }
        response = requests.put(f"{BASE_URL}/items/{item_id}", json=updated_data)
        print(f"Update status: {response.status_code}")
        if response.status_code == 200:
            updated_item = response.json()
            print(f"Updated name: {updated_item.get('name')}")
        
        # SEARCH - Search for items
        print("\n5. Searching items...")
        response = requests.get(f"{BASE_URL}/items/search/EDOT")
        print(f"Search status: {response.status_code}")
        search_results = response.json()
        print(f"Search results: {search_results.get('count')} items found")
        
        # DELETE - Delete the item
        print(f"\n6. Deleting item: {item_id}")
        response = requests.delete(f"{BASE_URL}/items/{item_id}")
        print(f"Delete status: {response.status_code}")
        if response.status_code == 200:
            delete_result = response.json()
            print(f"Delete message: {delete_result.get('message')}")
        
        return True
        
    except Exception as e:
        print(f"CRUD operations test failed: {e}")
        return False

def test_error_handling():
    """Test error handling"""
    print("\nTesting error handling...")
    try:
        # Test intentional error
        response = requests.get(f"{BASE_URL}/items/error")
        print(f"Error test status: {response.status_code}")
        if response.status_code == 500:
            error_data = response.json()
            print(f"Error message: {error_data.get('error')}")
            print("Error handling works correctly!")
        
        # Test 404 error
        response = requests.get(f"{BASE_URL}/items/nonexistent-id")
        print(f"404 test status: {response.status_code}")
        if response.status_code == 404:
            print("404 error handling works correctly!")
        
        return True
        
    except Exception as e:
        print(f"Error handling test failed: {e}")
        return False

def generate_load():
    """Generate some load to see tracing in action"""
    print("\nGenerating load for tracing demo...")
    
    # Create multiple items
    for i in range(5):
        test_item = {
            "name": f"Load Test Item {i+1}",
            "description": f"Generated for EDOT tracing demo {i+1}",
            "price": round(10.0 + i * 5.5, 2),
            "is_available": i % 2 == 0
        }
        
        try:
            response = requests.post(f"{BASE_URL}/items", json=test_item)
            if response.status_code == 201:
                print(f"Created item {i+1}")
            time.sleep(0.5)  # Small delay between requests
        except Exception as e:
            print(f"Failed to create item {i+1}: {e}")
    
    # Get all items multiple times
    for i in range(3):
        try:
            response = requests.get(f"{BASE_URL}/items")
            if response.status_code == 200:
                data = response.json()
                print(f"Fetched {data.get('count')} items (request {i+1})")
            time.sleep(1)
        except Exception as e:
            print(f"Failed to fetch items: {e}")
    
    # Search operations
    search_terms = ["Load", "Test", "demo"]
    for term in search_terms:
        try:
            response = requests.get(f"{BASE_URL}/items/search/{term}")
            if response.status_code == 200:
                data = response.json()
                print(f"Search '{term}' found {data.get('count')} items")
            time.sleep(0.5)
        except Exception as e:
            print(f"Search failed for '{term}': {e}")

def main():
    """Main test function"""
    print("=== EDOT Flask API Test Suite ===")
    
    # Wait for service to be ready
    print("Waiting for service to be ready...")
    for attempt in range(10):
        if test_health_check():
            break
        print(f"Attempt {attempt + 1}/10 failed, retrying...")
        time.sleep(2)
    else:
        print("Service is not ready after 10 attempts")
        return
    
    # Run tests
    tests = [
        ("Root Endpoint", test_root_endpoint),
        ("CRUD Operations", test_crud_operations),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        success = test_func()
        results.append((test_name, success))
    
    # Generate load for tracing
    print(f"\n{'='*50}")
    print("Generating Load for Tracing")
    print('='*50)
    generate_load()
    
    # Summary
    print(f"\n{'='*50}")
    print("Test Summary")
    print('='*50)
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    print("\n=== EDOT Tracing Info ===")
    print("Check your APM dashboard to see:")
    print("- Service: edot-flask-service")
    print("- Transactions with custom labels")
    print("- Error traces and exceptions")
    print("- Performance metrics")

if __name__ == "__main__":
    main()
