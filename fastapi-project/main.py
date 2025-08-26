from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
import logging
from contextlib import asynccontextmanager

# Import OpenTelemetry components
from otel_config import init_otel, get_tracer, get_meter
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode


# Configure logging
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
    with tracer.start_as_current_span("read_root") as span:
        span.set_attribute("endpoint", "root")
        response = {"message": "Welcome to Simple FastAPI!", "version": "1.0.0"}
        span.set_attribute("response.message", response["message"])
        return response

# Health check endpoint
@app.get("/health")
async def health_check():
    with tracer.start_as_current_span("health_check") as span:
        span.set_attribute("endpoint", "health")
        return {"status": "healthy", "service": "fastapi-service"}

# Get all items
@app.get("/items", response_model=List[Item])
async def get_items():
    with tracer.start_as_current_span("recieve_item1") as span:
        span.set_attribute("endpoint", "recieve_item2")
        span.set_attribute("items.count", len(items_db))
        
        # Record metrics
        item_operations.add(1, {"operation": "list", "endpoint": "recieve"})
        
        items_list = list(items_db.values())
        span.set_attribute("response.items_count", len(items_list))
        return items_list

# Get item by ID
@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: str):
    with tracer.start_as_current_span("get_item") as span:
        span.set_attribute("endpoint", "get_item")
        span.set_attribute("item.id", item_id)
        
        if item_id not in items_db:
            span.record_exception(Exception("Item not found"))
            span.set_status(Status(StatusCode.ERROR, "Item not found"))
            raise HTTPException(status_code=404, detail="Item not found")
        
        item = items_db[item_id]
        span.set_attribute("item.name", item.name)
        span.set_attribute("item.price", item.price)
        
        # Record metrics
        item_operations.add(1, {"operation": "get", "endpoint": "get_item"})
        
        return item

# Create new item
@app.post("/items", response_model=Item)
async def create_item(item: ItemCreate):
    with tracer.start_as_current_span("create_item") as span:
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
        
        logger.info(f"Created item: {item.name} with ID: {item_id}")
        return new_item

# Update item
@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: str, item: ItemCreate):
    with tracer.start_as_current_span("update_item") as span:
        span.set_attribute("endpoint", "update_item")
        span.set_attribute("item.id", item_id)
        span.set_attribute("item.name", item.name)
        
        if item_id not in items_db:
            span.record_exception(Exception("Item not found"))
            span.set_status(Status(StatusCode.ERROR, "Item not found"))
            raise HTTPException(status_code=404, detail="Item not found")
        
        updated_item = Item(id=item_id, **item.dict())
        items_db[item_id] = updated_item
        
        span.set_attribute("item.updated", True)
        
        # Record metrics
        item_operations.add(1, {"operation": "update", "endpoint": "update_item"})
        
        logger.info(f"Updated item: {item.name} with ID: {item_id}")
        return updated_item

# Delete item
@app.delete("/items/{item_id}")
async def delete_item(item_id: str):
    with tracer.start_as_current_span("delete_item") as span:
        span.set_attribute("endpoint", "delete_item")
        span.set_attribute("item.id", item_id)
        
        if item_id not in items_db:
            span.record_exception(Exception("Item not found"))
            span.set_status(Status(StatusCode.ERROR, "Item not found"))
            raise HTTPException(status_code=404, detail="Item not found")
        
        deleted_item = items_db.pop(item_id)
        span.set_attribute("item.name", deleted_item.name)
        span.set_attribute("item.deleted", True)
        
        # Record metrics
        item_counter.add(-1, {"operation": "deleted"})
        item_operations.add(1, {"operation": "delete", "endpoint": "delete_item"})
        
        logger.info(f"Deleted item: {deleted_item.name} with ID: {item_id}")
        return {"message": f"Item {deleted_item.name} deleted successfully"}

# Search items by name
@app.get("/items/search/{query}", response_model=List[Item])
async def search_items(query: str):
    with tracer.start_as_current_span("search_items") as span:
        span.set_attribute("endpoint", "search_items")
        span.set_attribute("search.query", query)
        
        matching_items = [
            item for item in items_db.values() 
            if query.lower() in item.name.lower() or (item.description and query.lower() in item.description.lower())
        ]
        
        span.set_attribute("search.results_count", len(matching_items))
        
        # Record metrics
        item_operations.add(1, {"operation": "search", "endpoint": "search_items"})
        
        logger.info(f"Search for '{query}' returned {len(matching_items)} items")
        return matching_items

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
