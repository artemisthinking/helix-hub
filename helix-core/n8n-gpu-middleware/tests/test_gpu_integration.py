import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_gpu_integration_success():
    response = client.post("/gpu/tasks", json={"task": "example_task"}, headers={"Authorization": "test-token"})
    assert response.status_code == 200
    assert "task_id" in response.json()

def test_gpu_integration_failure():
    response = client.post("/gpu/tasks", json={"task": ""}, headers={"Authorization": "test-token"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Task cannot be empty"}

def test_gpu_node_selection():
    response = client.get("/gpu/nodes", headers={"Authorization": "test-token"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_gpu_job_dispatch():
    response = client.post("/gpu/jobs", json={"task_id": "12345"}, headers={"Authorization": "test-token"})
    assert response.status_code == 200
    assert response.json() == {"status": "Job dispatched successfully."}