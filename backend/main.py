import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import upload, export
from backend.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# Allow the mobile-optimized React frontend to communicate with this gateway
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the dynamic proxy storage pool so the client can play lightweight streams immediately
app.mount("/api/streams", StaticFiles(directory=settings.PROXY_DIR), name="streams")

# Include structural application routers
app.include_router(upload.router, prefix="/api/video", tags=["Video / AI Processing"])
app.include_router(export.router, prefix="/api/export", tags=["High-Quality Rendering"])

@app.get("/health")
def health_check():
    """Simple verification route to confirm gateway health status."""
    return {"status": "operational", "project": settings.PROJECT_NAME}

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
