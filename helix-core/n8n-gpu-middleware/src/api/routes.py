from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.services.gpu_service import GPUService
from src.config.settings import API_KEY, API_URL
from src.services.gpu_service import GPUService

router = APIRouter()

class GPUTaskRequest(BaseModel):
    task_name: str
    parameters: dict

class GPUTaskResponse(BaseModel):
    task_id: str
    status: str
@router.post("/gpu/tasks", response_model=GPUTaskResponse)
async def create_gpu_task(task_request: GPUTaskRequest):
    try:
        task_id = await GPUService.submit_gpu_task(task_request.task_name, task_request.parameters)
        return GPUTaskResponse(task_id=task_id, status="submitted")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))