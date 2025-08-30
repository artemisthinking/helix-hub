from fastapi import middleware
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)
headers = {"Authorization": "test-token"}

def test_execute_gpu_task():
    response = client.post("/api/gpu-task", json={"task": "example_task"}, headers=headers)
    assert response.status_code == 200
    assert "task_id" in response.json()

def test_invalid_gpu_task():
    response = client.post("/api/gpu-task", json={"invalid_key": "invalid_value"}, headers=headers)
    assert response.status_code == 422  # Unprocessable Entity

def test_get_gpu_task_status():
    response = client.get("/api/gpu-task/status/1", headers=headers)
    assert response.status_code == 200
    assert "status" in response.json()