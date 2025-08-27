from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
import time
import logging
from datetime import datetime
from contextlib import asynccontextmanager

# Import OpenTelemetry components
from otel_config import init_otel, get_tracer, get_meter
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode

# Minimal logging setup - OpenTelemetry handles correlation automatically
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenTelemetry before creating the app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize OpenTelemetry
    logger.info("Starting FastAPI application with OpenTelemetry")
    init_otel(app)
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application")

# Create FastAPI instance with lifespan events
app = FastAPI(
    title="Simple FastAPI", 
    description="A simple FastAPI example with OpenTelemetry instrumentation", 
    version="1.0.0",
    lifespan=lifespan
)

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

# Pydantic models for request/response
class Item(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: float
    is_available: bool = True

class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    is_available: bool = True

# In-memory storage
items_db = {}

# Root endpoint
@app.get("/")
async def read_root():
    logger.info("Root endpoint accessed")
    
    with tracer.start_as_current_span("GET /") as span:
        span.set_attribute("endpoint", "root")
        
        response = {
            "message": "Welcome to Simple FastAPI!", 
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Root endpoint completed successfully")
        return response

# Health check endpoint
@app.get("/health")
async def health_check():
    logger.info("Health check accessed")
    
    with tracer.start_as_current_span("GET /health") as span:
        span.set_attribute("endpoint", "health")
        response = {
            "status": "healthy", 
            "service": "fastapi-service",
            "timestamp": datetime.now().isoformat(),
            "items_count": len(items_db)
        }
        
        logger.info("Health check completed")
        return response

# Get all items
@app.get("/items", response_model=List[Item])
async def get_items():
    logger.info("Getting all items")
    
    with tracer.start_as_current_span("GET /items") as span:
        span.set_attribute("endpoint", "get_items")
        span.set_attribute("items.count", len(items_db))
        
        # Record metrics
        item_operations.add(1, {"operation": "list", "endpoint": "get_items"})
        
        items_list = list(items_db.values())
        span.set_attribute("response.items_count", len(items_list))
        
        logger.info(f"Successfully retrieved {len(items_list)} items")
        return items_list

# Get item by ID
@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: str):
    logger.info(f"Getting item: {item_id}")
    
    with tracer.start_as_current_span("GET /items/{item_id}") as span:
        span.set_attribute("endpoint", "get_item")
        span.set_attribute("item.id", item_id)
        
        if item_id not in items_db:
            logger.warning(f"Item not found: {item_id}")
            span.record_exception(Exception("Item not found"))
            span.set_status(Status(StatusCode.ERROR, "Item not found"))
            raise HTTPException(status_code=404, detail="Item not found")
        
        item = items_db[item_id]
        span.set_attribute("item.name", item.name)
        span.set_attribute("item.price", item.price)
        
        # Record metrics
        item_operations.add(1, {"operation": "get", "endpoint": "get_item"})
        
        logger.info(f"Successfully retrieved item: {item.name}")
        return item

# Create new item
@app.post("/items", response_model=Item)
async def create_item(item: ItemCreate):
    logger.info(f"Creating new item: {item.name}")
    
    with tracer.start_as_current_span("POST /items") as span:
        span.set_attribute("endpoint", "create_item")
        span.set_attribute("item.name", item.name)
        span.set_attribute("item.price", item.price)
        
        item_id = str(uuid.uuid4())
        new_item = Item(id=item_id, **item.dict())
        items_db[item_id] = new_item
        
        span.set_attribute("item.id", item_id)
        span.set_attribute("item.created", True)
        
        # Record metrics
        item_counter.add(1, {"operation": "created"})
        item_operations.add(1, {"operation": "create", "endpoint": "create_item"})
        
        logger.info(f"Successfully created item: {item.name} with ID: {item_id}")
        return new_item

# Update item
@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: str, item: ItemCreate):
    logger.info(f"Updating item: {item_id}")
    
    with tracer.start_as_current_span("PUT /items/{item_id}") as span:
        span.set_attribute("endpoint", "update_item")
        span.set_attribute("item.id", item_id)
        span.set_attribute("item.name", item.name)
        
        if item_id not in items_db:
            logger.warning(f"Cannot update - item not found: {item_id}")
            span.record_exception(Exception("Item not found"))
            span.set_status(Status(StatusCode.ERROR, "Item not found"))
            raise HTTPException(status_code=404, detail="Item not found")
        
        old_item = items_db[item_id]
        updated_item = Item(id=item_id, **item.dict())
        items_db[item_id] = updated_item
        
        span.set_attribute("item.updated", True)
        
        # Record metrics
        item_operations.add(1, {"operation": "update", "endpoint": "update_item"})
        
        logger.info(f"Successfully updated item: {item.name}")
        return updated_item

# Delete item
@app.delete("/items/{item_id}")
async def delete_item(item_id: str):
    logger.info(f"Deleting item: {item_id}")
    
    with tracer.start_as_current_span("DELETE /items/{item_id}") as span:
        span.set_attribute("endpoint", "delete_item")
        span.set_attribute("item.id", item_id)
        
        if item_id not in items_db:
            logger.warning(f"Cannot delete - item not found: {item_id}")
            span.record_exception(Exception("Item not found"))
            span.set_status(Status(StatusCode.ERROR, "Item not found"))
            raise HTTPException(status_code=404, detail="Item not found")
        
        deleted_item = items_db.pop(item_id)
        span.set_attribute("item.name", deleted_item.name)
        span.set_attribute("item.deleted", True)
        
        # Record metrics
        item_counter.add(-1, {"operation": "deleted"})
        item_operations.add(1, {"operation": "delete", "endpoint": "delete_item"})
        
        logger.info(f"Successfully deleted item: {deleted_item.name}")
        return {"message": f"Item {deleted_item.name} deleted successfully"}

# Search items
@app.get("/search")
async def search_items(q: str = ""):
    logger.info(f"Searching items with query: {q}")
    
    with tracer.start_as_current_span("GET /search") as span:
        span.set_attribute("endpoint", "search_items")
        span.set_attribute("search.query", q)
        
        # Perform search
        search_results = []
        for item_id, item in items_db.items():
            if q.lower() in item.name.lower() or q.lower() in item.description.lower():
                search_results.append({
                    "id": item_id,
                    "name": item.name,
                    "description": item.description,
                    "price": item.price
                })
        
        span.set_attribute("search.results_count", len(search_results))
        
        # Record metrics
        item_operations.add(1, {"operation": "search", "endpoint": "search_items"})
        
        logger.info(f"Search completed: found {len(search_results)} items")
        return {"query": q, "results": search_results, "count": len(search_results)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
