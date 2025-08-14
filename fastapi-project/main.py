from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid

# Create FastAPI instance
app = FastAPI(title="Simple FastAPI", description="A simple FastAPI example", version="1.0.0")

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
    return {"message": "Welcome to Simple FastAPI!", "version": "1.0.0"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "fastapi-service"}

# Get all items
@app.get("/items", response_model=List[Item])
async def get_items():
    return list(items_db.values())

# Get item by ID
@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: str):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]

# Create new item
@app.post("/items", response_model=Item)
async def create_item(item: ItemCreate):
    item_id = str(uuid.uuid4())
    new_item = Item(id=item_id, **item.dict())
    items_db[item_id] = new_item
    return new_item

# Update item
@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: str, item: ItemCreate):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    updated_item = Item(id=item_id, **item.dict())
    items_db[item_id] = updated_item
    return updated_item

# Delete item
@app.delete("/items/{item_id}")
async def delete_item(item_id: str):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    deleted_item = items_db.pop(item_id)
    return {"message": f"Item {deleted_item.name} deleted successfully"}

# Search items by name
@app.get("/items/search/{query}", response_model=List[Item])
async def search_items(query: str):
    matching_items = [
        item for item in items_db.values() 
        if query.lower() in item.name.lower() or (item.description and query.lower() in item.description.lower())
    ]
    return matching_items

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
