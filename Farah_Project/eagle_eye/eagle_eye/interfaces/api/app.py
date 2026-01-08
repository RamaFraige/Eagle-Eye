import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from eagle_eye.config.settings import settings

logger = logging.getLogger(__name__)


# Create a context lifecycle manager
async def lifespan(app: FastAPI):
    logger.debug("Loading dependencies...")
    # Import API routes dynamically to avoid circular dependencies
    from eagle_eye.database import close_db, init_db

    from .routes import router as api_router

    # Initialize the database connection
    logger.debug("Initializing database...")
    init_db()
    # Include all defined API routes into the FastAPI application
    app.include_router(api_router)
    yield
    # Close the database connection when the application shuts down
    logger.debug("Closing database...")
    close_db()


app = FastAPI(
    title=settings.APP_NAME,
    description="WebRTC API for Eagle Eye",
    version="0.1.0",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},  # Hide schema section
    lifespan=lifespan,
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=RedirectResponse, include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {"status": "ok"}


def run_api():
    import uvicorn

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)


if __name__ == "__main__":
    run_api()
