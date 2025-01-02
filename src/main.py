from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi_pagination import add_pagination

from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    pass


app: FastAPI = FastAPI(
    title=settings.APP_TITLE,
    description="A simple API key manager for developers and their projects.",
    docs_url="/apikeys-hub/docs",
    redoc_url="/apikeys-hub/redoc",
    openapi_url="/apikeys-hub/openapi.json",
)


@app.get("/", include_in_schema=False)
async def read_root():
    return RedirectResponse(url="/apikeys-hub/docs")


@app.get("/apikeys-hub/@ping", tags=["DEFAULT"], summary="Check if server is available")
async def ping():
    return {"message": "pong !"}


# Add pagination support to the app
add_pagination(app)
