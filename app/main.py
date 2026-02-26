import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import get_settings
from .utils.logging import configure_logging

STATIC_DIR = Path(__file__).parent / "static"

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    logging.getLogger(__name__).info(
        f"Starting Project Planning Agent | env={settings.app_env} "
        f"| store={settings.session_store}"
    )
    yield
    logging.getLogger(__name__).info("Shutting down")


app = FastAPI(
    title="Project Planning Agent",
    description=(
        "Conversational AI service that guides users through 5-stage structured "
        "project planning and outputs a fully structured project plan."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def serve_ui():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# Routes are registered after models/storage/agent are defined.
# Import here to avoid circular imports at module load time.
from .api.routes import chat, sessions, plans  # noqa: E402

app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(sessions.router, prefix="/api/v1", tags=["Sessions"])
app.include_router(plans.router, prefix="/api/v1", tags=["Plans"])
