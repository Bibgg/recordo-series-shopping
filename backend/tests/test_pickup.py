import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
ADMIN = {"X-Admin-Token": "test-admin-token"}

def make_order(area="Baglung"):
    product = client.post("/api/v1/admin/products", headers=ADMIN, json={
        "name": "Pickup test item", "category": "Groceries", "price_npr": 100,
        "unit": "piece", "stock_quantity": 20, "pickup_area": area
    })
    assert product.status_code == 201
    return client.post("/api/v1/orders", json={
        "customer_name": "Buyer Test", "phone": "9800000000",
        "district": "Baglung", "municipality": "Baglung Municipality",
        "ward": "4", "delivery_address": "Test village, near school",
        "items": [{"product_id": product.json()["id"], "quantity": 1}]
    })

def test_pickup_area_progress_is_public_and_private_data_free():
    assert make_order().status_code == 201
    response = client.get("/api/v1/pickup/areas")
    assert response.status_code == 200
    area = response.json()[0]
    assert area["pickup_area"] == "Baglung"
    assert area["ready_orders"] == 1
    assert area["target_orders"] == 50
    assert area["remaining_orders"] == 49
    assert "phone" not in area and "customer_name" not in area

def test_pickup_batch_requires_threshold_unless_admin_forces():
    for _ in range(2):
        assert make_order("Baglung North").status_code == 201
    blocked = client.post("/api/v1/admin/pickup/batches", headers=ADMIN, json={
        "pickup_area": "Baglung North", "target_orders": 3
    })
    assert blocked.status_code == 409
    created = client.post("/api/v1/admin/pickup/batches", headers=ADMIN, json={
        "pickup_area": "Baglung North", "target_orders": 2
    })
    assert created.status_code == 201
    assert created.json()["order_count"] == 2
    assert created.json()["status"] == "pickup_scheduled"

def test_pickup_admin_routes_require_token():
    assert client.get("/api/v1/admin/pickup/batches").status_code == 401
