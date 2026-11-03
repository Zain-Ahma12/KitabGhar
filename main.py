from fastapi import FastAPI, status
from contextlib import asynccontextmanager
from routes import book_router, users_router
from database import create_tables
from custom_docs_ui import setup_custom_docs
import time
from datetime import datetime, timezone
import logging
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Remember when the app started so we can report uptime.
    global START_TIME
    START_TIME = time.time()
    logger.info("Application started")
    create_tables()
    print("Database tables created")
    yield
    # shutdown: clean up here
    print("Shutting down the app")

app = FastAPI(
    title="KitabGhar Exchange APIs",
    description="APIs for KitabGhar service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,  # to override the default /docs route
)

setup_custom_docs(app, docs_path="/docs")

app.include_router(book_router)
app.include_router(users_router)

@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    tags=["health"]
    )
async def liveness() -> dict[str, object]:
    """Liveness check: it only proves the app is running, so it never touches the database."""
    return {
        "status": "healthy",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    
if __name__ == "__main__":
    
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
