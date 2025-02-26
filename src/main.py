from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi_pagination import add_pagination

from src import models
from src.common.config import shutdown_db_client, startup_db_client
from src.config import settings
from src.common.helpers.exception import setup_exception_handlers
from .endpoint import router as apikey_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_db_client(
        app=app,
        mongodb_uri=settings.MONGODB_URI,
        database_name=settings.MONGO_DB,
        document_models=models.document_models,
    )

    yield

    await shutdown_db_client(app=app)


app: FastAPI = FastAPI(
    lifespan=lifespan,
    title=settings.APP_TITLE,
    description="A simple API key manager for developers and their projects.",
    docs_url="/apikeys/docs",
    redoc_url="/apikeys/redoc",
    openapi_url="/apikeys/openapi.json",
)


@app.get("/", include_in_schema=False)
async def read_root():
    return RedirectResponse(url="/apikeys/docs")


@app.get("/apikeys/@ping", tags=["DEFAULT"], summary="Check if server is available")
async def ping():
    return {"message": "pong !"}


# Add the API key router to the app
app.include_router(apikey_router)


# Add pagination support to the app
add_pagination(parent=app)

# Add exception handlers to the app
setup_exception_handlers(app=app)
