#!/usr/bin/env python3
"""
Example demonstrating OpenTelemetry middleware usage in Flask
This shows different ways to add tracing and observability to your Flask app.
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_middleware_features():
    """Test various middleware features"""
    print("🚀 Testing OpenTelemetry Middleware Features\n")
    
    print("=== 1. Automatic Request Tracing ===")
    print("   The middleware automatically captures:")
    print("   - HTTP method, URL, status code")
    print("   - Request/response sizes")
    print("   - Request duration")
    print("   - Error handling")
    
    # Test root endpoint with trace ID in response
    print("\n1.1. Root endpoint (with trace ID):")
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Response: {data['message']}")
        print(f"   📊 Trace ID: {data.get('trace_id', 'N/A')}")
    
    # Test health check
    print("\n1.2. Health check (excluded from detailed tracing):")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print(f"   ✅ Status: {response.json()['status']}")
    
    print("\n=== 2. Automatic Metrics Collection ===")
    print("   The middleware collects these metrics:")
    print("   - http_requests_total")
    print("   - http_request_duration_seconds") 
    print("   - http_request_size_bytes")
    print("   - http_response_size_bytes")
    print("   - http_requests_active")
    
    # Create multiple requests to generate metrics
    print("\n2.1. Creating items to generate metrics...")
    items_created = []
    for i in range(3):
        item_data = {
            "name": f"Test Item {i+1}",
            "description": f"Middleware test item {i+1}",
            "price": 99.99 + i * 10,
            "is_available": True
        }
        response = requests.post(f"{BASE_URL}/items", json=item_data)
        if response.status_code == 201:
            items_created.append(response.json()["id"])
            print(f"   ✅ Created: {item_data['name']}")
    
    print("\n=== 3. Custom Business Attributes ===")
    print("   The middleware adds business context:")
    print("   - business.domain = 'inventory'")
    print("   - business.operation = specific operations")
    print("   - http.route = Flask route templates")
    
    # Test get operations
    print("\n3.1. Testing GET operations:")
    if items_created:
        response = requests.get(f"{BASE_URL}/items/{items_created[0]}")
        if response.status_code == 200:
            item = response.json()
            print(f"   ✅ Retrieved: {item['name']}")
    
    # Test search operations
    print("\n3.2. Testing search operations:")
    response = requests.get(f"{BASE_URL}/items/search/test")
    if response.status_code == 200:
        results = response.json()
        print(f"   ✅ Search results: {results['count']} items")
    
    print("\n=== 4. Error Handling ===")
    print("   The middleware automatically handles:")
    print("   - Exception recording in spans")
    print("   - Error status codes")
    print("   - Span status setting")
    
    # Test 404 error
    print("\n4.1. Testing 404 error:")
    response = requests.get(f"{BASE_URL}/items/nonexistent-item")
    print(f"   📊 Status Code: {response.status_code}")
    if response.status_code == 404:
        print(f"   ✅ Error: {response.json().get('error', 'Unknown')}")
    
    # Test validation error
    print("\n4.2. Testing validation error:")
    invalid_data = {"name": "", "price": -10}  # Invalid data
    response = requests.post(f"{BASE_URL}/items", json=invalid_data)
    print(f"   📊 Status Code: {response.status_code}")
    if response.status_code == 400:
        print(f"   ✅ Validation Error: {response.json().get('error', 'Unknown')}")
    
    print("\n=== 5. Trace Context Propagation ===")
    print("   The middleware supports:")
    print("   - W3C Trace Context")
    print("   - B3 Propagation (Zipkin)")
    print("   - W3C Baggage")
    
    # Test with custom headers
    print("\n5.1. Testing with trace headers:")
    custom_headers = {
        "traceparent": "00-12345678901234567890123456789012-1234567890123456-01",
        "x-request-id": "test-request-123"
    }
    response = requests.get(f"{BASE_URL}/", headers=custom_headers)
    if response.status_code == 200:
        print(f"   ✅ Request with custom trace context processed")
    
    print("\n=== 6. Performance Impact ===")
    print("   Testing middleware performance...")
    
    # Measure request time with and without custom spans
    start_time = time.time()
    for i in range(10):
        response = requests.get(f"{BASE_URL}/items")
    duration = time.time() - start_time
    print(f"   📊 10 requests took: {duration:.3f} seconds")
    print(f"   📊 Average per request: {duration/10*1000:.1f} ms")
    
    # Clean up created items
    print("\n=== Cleanup ===")
    for item_id in items_created:
        response = requests.delete(f"{BASE_URL}/items/{item_id}")
        if response.status_code == 200:
            print(f"   🗑️ Deleted item: {item_id}")
    
    print("\n🎉 Middleware testing completed!")
    print("\n📊 Check your OpenTelemetry collector/observability platform for:")
    print("   - Traces with automatic HTTP spans")
    print("   - Custom business attributes")
    print("   - Metrics for request counts, durations, sizes")
    print("   - Error traces with exceptions")
    print("   - Trace context propagation")

def show_middleware_benefits():
    """Show the benefits of using OpenTelemetry middleware"""
    print("\n" + "="*60)
    print("🎯 OPENTELEMETRY MIDDLEWARE BENEFITS")
    print("="*60)
    
    print("\n✅ AUTOMATIC INSTRUMENTATION:")
    print("   • Zero code changes required for basic tracing")
    print("   • All HTTP requests automatically traced") 
    print("   • Request/response data captured")
    print("   • Error handling built-in")
    
    print("\n📊 COMPREHENSIVE METRICS:")
    print("   • Request counts by endpoint, method, status")
    print("   • Request duration histograms")
    print("   • Request/response size tracking")
    print("   • Active request counters")
    
    print("\n🏷️ BUSINESS CONTEXT:")
    print("   • Automatic business domain detection")
    print("   • Operation-specific attributes")
    print("   • Custom attribute support")
    print("   • Route template tracking")
    
    print("\n🔗 TRACE PROPAGATION:")
    print("   • W3C Trace Context support")
    print("   • B3 propagation for Zipkin")
    print("   • Baggage propagation")
    print("   • Multi-format support")
    
    print("\n🚨 ERROR HANDLING:")
    print("   • Automatic exception recording")
    print("   • Span status management")
    print("   • HTTP error code tracking")
    print("   • Debug information preservation")
    
    print("\n⚡ PERFORMANCE:")
    print("   • Minimal overhead")
    print("   • Asynchronous export")
    print("   • Configurable sampling")
    print("   • Memory efficient")

if __name__ == "__main__":
    try:
        test_middleware_features()
        show_middleware_benefits()
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed! Make sure the Flask server is running:")
        print("   python app.py")
        print("   or")
        print("   docker-compose -f docker-compose-dev.yml up")
    except Exception as e:
        print(f"❌ Test failed: {e}")
