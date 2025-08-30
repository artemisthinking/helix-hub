
from typing import List, Dict, Any
import httpx
from src.config.settings import API_URL, API_KEY


def submit_gpu_task(job_payload: Dict[str, Any]) -> Dict[str, Any]:
    service = GPUService()
    return service.submit_job(job_payload)

class GPUService:
    def __init__(self):
        self.client = httpx.Client(base_url=API_URL, headers={"Authorization": f"Bearer {API_KEY}"})

    def get_available_nodes(self) -> List[Dict[str, Any]]:
        response = self.client.get("/nodes/available")
        response.raise_for_status()
        return response.json()

    def submit_job(self, job_payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.post("/jobs/submit", json=job_payload)
        response.raise_for_status()
        return response.json()

def submit_gpu_task(job_payload: Dict[str, Any]) -> Dict[str, Any]:
    service = GPUService()
    return service.submit_job(job_payload)
    def __init__(self):
        self.client = httpx.Client(base_url=API_URL, headers={"Authorization": f"Bearer {API_KEY}"})

    def get_available_nodes(self) -> List[Dict[str, Any]]:
        response = self.client.get("/nodes/available")
        response.raise_for_status()
        return response.json()

    def submit_job(self, job_payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.post("/jobs/submit", json=job_payload)
        response.raise_for_status()
        return response.json()