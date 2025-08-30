from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.middleware.gpu_integration import GPUIntegrationMiddleware
from src.api.routes import router as api_router

app = FastAPI()

# Add CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GPU integration middleware
app.add_middleware(GPUIntegrationMiddleware)

# Include API routes
app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the n8n GPU Middleware API"}