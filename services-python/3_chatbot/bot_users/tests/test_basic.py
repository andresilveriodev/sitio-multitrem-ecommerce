"""
Testes básicos para o Chatbot Service
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Testa o endpoint de health check"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "chatbot_service"
    assert data["port"] == 8002


def test_root_endpoint():
    """Testa o endpoint raiz"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "E-commerce Chatbot Service" in data["message"]
    assert data["version"] == "1.0.0"


def test_process_message_missing_data():
    """Testa processamento de mensagem com dados faltando"""
    response = client.post("/chatbot/process-message", json={})
    assert response.status_code == 400


def test_process_message_empty_message():
    """Testa processamento de mensagem vazia"""
    response = client.post("/chatbot/process-message", json={
        "user_id": "123",
        "message": ""
    })
    assert response.status_code == 200
    data = response.json()
    assert not data["success"]
    assert "vazia" in data["error"]


def test_cache_stats_endpoint():
    """Testa endpoint de estatísticas do cache"""
    response = client.get("/chatbot/cache-stats")
    assert response.status_code == 200
    data = response.json()
    assert data["success"]
    assert "cache_stats" in data


def test_system_health_endpoint():
    """Testa endpoint de saúde do sistema"""
    response = client.get("/chatbot/system-health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"]
    assert "health" in data


