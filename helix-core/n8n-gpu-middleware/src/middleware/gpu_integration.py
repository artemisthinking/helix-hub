from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class GPUIntegrationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Handle authentication and node selection logic here
        # Example: Check for API key in headers
        api_key = request.headers.get("X-API-Key")
        if not api_key or not self.authenticate(api_key):
            return Response("Unauthorized", status_code=401)

        # Example: Select a GPU node
        gpu_node = self.select_gpu_node()
        if not gpu_node:
            return Response("No available GPU nodes", status_code=503)

        # Dispatch the request to the next middleware or route handler
        response = await call_next(request)

        # Optionally, you can modify the response here
        return response

    def authenticate(self, api_key: str) -> bool:
        # Implement your authentication logic here
        return api_key == "your_secret_api_key"

    def select_gpu_node(self):
        # Implement your logic to select an available GPU node
        # This could involve querying the Vast.ai API
        return "selected_gpu_node"  # Placeholder for the selected node