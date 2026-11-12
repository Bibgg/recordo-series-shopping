import os
import pytest
from fastapi.testclient import TestClient

os.environ["ADMIN_API_TOKEN"] = "test-admin-token"
from app.main import app, Base, engine

@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

client = TestClient(app)
ADMIN = {"X-Admin-Token": "test-admin-token"}

def test_health_reports_nepal_and_npr():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["country"] == "NP"
    assert response.json()["currency"] == "NPR"

def test_config_uses_nepalese_rupees():
    response = client.get("/api/v1/config")
    assert response.status_code == 200
    assert response.json()["currency_code"] == "NPR"
    assert response.json()["currency_symbol"] == "रु"

def test_admin_can_add_product_and_customer_can_order_and_track():
    product = client.post("/api/v1/admin/products", headers=ADMIN, json={
        "name": "Local potatoes", "description": "Farm fresh", "category": "Vegetables",
        "price_npr": 60, "unit": "kg", "stock_quantity": 10
    })
    assert product.status_code == 201
    product_id = product.json()["id"]
    order = client.post("/api/v1/orders", json={
        "customer_name": "Test Buyer", "phone": "9800000000", "district": "Baglung",
        "municipality": "Baglung Municipality", "ward": "4", "delivery_address": "Test village, near school",
        "items": [{"product_id": product_id, "quantity": 2}]
    })
    assert order.status_code == 201
    assert order.json()["total_npr"] == 120
    tracked = client.get(f"/api/v1/orders/{order.json()['order_code']}?phone=9800000000")
    assert tracked.status_code == 200
    assert tracked.json()["status"] == "placed"
    assert client.get("/api/v1/admin/orders", headers=ADMIN).status_code == 200

def test_order_rejects_insufficient_stock():
    product = client.post("/api/v1/admin/products", headers=ADMIN, json={
        "name": "Fresh apples", "category": "Fruits", "price_npr": 200,
        "unit": "kg", "stock_quantity": 1
    })
    response = client.post("/api/v1/orders", json={
        "customer_name": "Test Buyer", "phone": "9800000000", "district": "Baglung",
        "municipality": "Baglung Municipality", "ward": "4", "delivery_address": "Test village, near school",
        "items": [{"product_id": product.json()["id"], "quantity": 2}]
    })
    assert response.status_code == 409

def test_admin_routes_require_token():
    response = client.get("/api/v1/admin/orders")
    assert response.status_code == 401
