import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "AI Viz PoC API is running"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200

def test_get_sales_data():
    response = client.get("/data/sales")
    assert response.status_code == 200
    assert "data" in response.json()

def test_text_to_viz():
    response = client.post("/query/text-to-viz", json={"query": "show me sales by region"})
    assert response.status_code == 200
    data = response.json()
    assert "chart_type" in data
    assert "data" in data
    assert "config" in data

