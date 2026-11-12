from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

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

def test_products_have_npr_prices():
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    assert response.json()
    assert all(item["currency"] == "NPR" for item in response.json())
    assert all(item["price_npr"] >= 0 for item in response.json())
