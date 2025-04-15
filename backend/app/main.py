from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import pathlib
from .routers import video, download
from typing import Dict

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get user's home directory
home_dir = str(pathlib.Path.home())

# Create required directories
UPLOAD_DIR = "uploads"
COOKIE_DIR = "cookies"
LIBRARY_DIR = os.path.join(home_dir, "Movies", "remarks", "library")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(COOKIE_DIR, exist_ok=True)
os.makedirs(LIBRARY_DIR, exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/library", StaticFiles(directory=LIBRARY_DIR), name="library")

# Include routers
app.include_router(video.router, prefix="/api/video", tags=["video"])
app.include_router(download.router, prefix="/api/download", tags=["download"])

@app.get("/")
async def root():
    return {"message": "Video Processing API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/download")
async def download_video(request: Dict[str, str]):
    url = request.get("url")
    download_dir = request.get("download_dir")
    
    if not url:
        return {"success": False, "error": "URL is required"}
    
    downloader = VideoDownloader(download_dir=download_dir)
    result = await downloader.download(url)
    return result

@app.get("/default-path")
async def get_default_path():
    home_dir = str(pathlib.Path.home())
    default_path = os.path.join(home_dir, "Movies", "remarks", "library")
    return {"path": default_path}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 