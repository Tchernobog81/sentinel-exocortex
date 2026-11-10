"""
Cortex Loom Backend - FastAPI Application
Serveur local pour gérer les événements et l'analyse.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
import os
import logging
from datetime import datetime

# Import routes (compatible exécution package `backend.main` et script `main:app` depuis backend/)
try:
    from .routes import router as api_router
except ImportError:  # pragma: no cover
    from routes import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cortex Loom API",
    description="Backend pour Sentinel Exocortex - Veille des signaux faibles de la singularité",
    version="v1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration (allow all for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_root():
    """Serve index.html"""
    index_path = Path("index.html")
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Cortex Loom Backend - Consultez /api/docs pour la documentation"}


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("🚀 Cortex Loom Backend démarré")
    logger.info(f"📊 Docs disponibles à /api/docs")
    logger.info(f"🌐 Endpoints: /api/data, /api/data/recent, /api/data/stats")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    logger.info("⏹️ Cortex Loom Backend arrêté")


# For running with: python -m backend.main
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=True,
        log_level="info"
    )
