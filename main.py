import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes.agent import router as agent_router
from app.api.routes.cart import router as cart_router
from app.api.routes.products import router as products_router
from app.services.product_images import STATIC_DIR, STATIC_URL_PREFIX

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
# Keep third-party HTTP clients quiet even in debug mode
for noisy_logger in ("httpx", "httpcore", "chromadb", "google_genai"):
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered shopping assistant with LangGraph workflow, Google Gemini and a local vector database",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agent_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(cart_router, prefix="/api")

# Product images (generated with `python generate_product_images.py`)
STATIC_DIR.mkdir(exist_ok=True)
app.mount(STATIC_URL_PREFIX, StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Welcome to the Shopping Assistant API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/health"
    }


@app.on_event("startup")
async def startup_event():
    """
    Startup event to initialize services.
    """
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Environment: {settings.environment}")
    print(f"Gemini Model: {settings.gemini_model}")
    print(f"Gemini Embedding Model: {settings.gemini_embedding_model}")
    print(f"Vector DB: {settings.resolve_path(settings.vector_db_path)}")
    print(f"Selection Policy: {settings.selection_policy}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event to cleanup resources.
    """
    print(f"Shutting down {settings.app_name}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
