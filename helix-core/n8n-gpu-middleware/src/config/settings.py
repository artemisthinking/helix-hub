import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gpu_api_key: str = "test-key"
    gpu_api_url: str = "https://api.vast.ai/v0/batches"
    node_selection_strategy: str = "default"

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "../.env")
        env_file_encoding = "utf-8"

settings = Settings()
API_KEY = settings.gpu_api_key
API_URL = settings.gpu_api_url