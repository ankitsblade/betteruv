from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from jwt import encode

from challengeapp.settings import load_settings

app = FastAPI()


class HealthResponse(BaseModel):
    status: str
    server: str
    token_preview: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = load_settings()
    token = encode({"project": settings["project"]}, "dev-secret", algorithm="HS256")
    return HealthResponse(status="ok", server=uvicorn.__version__, token_preview=token[:12])
