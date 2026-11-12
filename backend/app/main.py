from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="Recordo Nepal Shopping API",
    version="0.1.0",
    description="Nepal-focused marketplace starter. All prices are NPR.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict before production deployment.
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

class Product(BaseModel):
    id: str
    name: str
    category: str
    price_npr: int = Field(ge=0)
    currency: str = "NPR"
    unit: str = "piece"
    sample: bool = True

SAMPLE_PRODUCTS = [
    Product(id="veg-001", name="Fresh Tomato", category="Vegetables", price_npr=80, unit="kg"),
    Product(id="fruit-001", name="Seasonal Banana", category="Fruits", price_npr=140, unit="dozen"),
    Product(id="grocery-001", name="Basmati Rice", category="Groceries", price_npr=950, unit="5 kg bag"),
    Product(id="daily-001", name="Mustard Oil", category="Daily Essentials", price_npr=320, unit="litre"),
]

@app.get("/health")
def health():
    return {"ok": True, "service": "recordo-nepal-api", "country": "NP", "currency": "NPR"}

@app.get("/api/v1/config")
def config():
    return {
        "market": "Nepal",
        "country_code": "NP",
        "currency_code": "NPR",
        "currency_symbol": "रु",
        "supported_languages": ["ne", "en"],
    }

@app.get("/api/v1/categories")
def categories():
    return [
        {"id": "vegetables", "name": "Vegetables"},
        {"id": "fruits", "name": "Fruits"},
        {"id": "groceries", "name": "Groceries"},
        {"id": "daily-essentials", "name": "Daily Essentials"},
    ]

@app.get("/api/v1/products", response_model=list[Product])
def products(category: str | None = Query(default=None)):
    items = SAMPLE_PRODUCTS
    if category:
        items = [item for item in items if item.category.lower() == category.lower()]
    return items
