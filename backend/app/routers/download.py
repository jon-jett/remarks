from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List
from ..services.video_downloader import VideoDownloader
from pydantic import BaseModel
import os

router = APIRouter()
downloader = VideoDownloader()

class DownloadRequest(BaseModel):
    url: str
    cookie_file: Optional[str] = None

@router.post("/video")
async def download_video(request: DownloadRequest):
    """Download a video using multiple methods with fallback."""
    try:
        result = await downloader.download(request.url, request.cookie_file)
        if result["success"]:
            return JSONResponse(content=result)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cookies")
async def upload_cookies(file: UploadFile = File(...)):
    """Upload a cookie file."""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are accepted")
    
    try:
        content = await file.read()
        filename = downloader.upload_cookies(content, file.filename)
        return {"filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cookies")
async def list_cookies():
    """List available cookie files."""
    try:
        return {"files": downloader.list_cookie_files()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cookies/{filename}")
async def delete_cookies(filename: str):
    """Delete a cookie file."""
    try:
        if not filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Only JSON files can be deleted")
        
        if downloader.delete_cookie_file(filename):
            return {"message": f"Cookie file {filename} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Cookie file not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 