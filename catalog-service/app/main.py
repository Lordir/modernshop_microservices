from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import time

app = FastAPI(title="Catalog Service")

# Мок база данных товаров
fake_products_db = [
    {
        "id": 1,
        "name": "Laptop Gaming Pro",
        "price": 999.99,
        "category": "electronics",
        "description": "High-performance gaming laptop",
        "stock": 15
    },
    {
        "id": 2,
        "name": "Wireless Mouse",
        "price": 29.99,
        "category": "electronics",
        "description": "Ergonomic wireless mouse",
        "stock": 50
    },
    {
        "id": 3,
        "name": "Programming Book",
        "price": 49.99,
        "category": "books",
        "description": "Learn Python programming",
        "stock": 25
    }
]


class Product(BaseModel):
    id: int
    name: str
    price: float
    category: str
    description: str
    stock: int


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "catalog-service",
        "timestamp": time.time()
    }


@app.get("/catalog/products")
async def get_products(category: Optional[str] = None, search: Optional[str] = None):
    products = fake_products_db

    # Фильтрация по категории
    if category:
        products = [p for p in products if p["category"] == category]

    # Поиск по названию
    if search:
        products = [p for p in products if search.lower() in p["name"].lower()]

    return products


@app.get("/catalog/products/{product_id}")
async def get_product(product_id: int):
    product = next((p for p in fake_products_db if p["id"] == product_id), None)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@app.get("/catalog/categories")
async def get_categories():
    categories = list(set(p["category"] for p in fake_products_db))
    return categories


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True
    )