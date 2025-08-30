from pydantic import BaseModel
from typing import List, Optional

class GpuTask(BaseModel):
    task_id: str
    user_id: str
    command: str
    parameters: Optional[dict] = None
    status: str
    result: Optional[dict] = None
    created_at: str
    updated_at: str

class GpuTaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None

class GpuTaskListResponse(BaseModel):
    tasks: List[GpuTaskResponse]