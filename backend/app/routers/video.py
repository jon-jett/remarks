from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
from typing import List
from ..services.video_processor import VideoProcessor

router = APIRouter()
video_processor = VideoProcessor()

@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    try:
        # Ensure the file is a video
        if not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Save the file
        file_path = os.path.join("uploads", file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the video
        result = await video_processor.process_video(file_path)
        
        return JSONResponse(content={
            "message": "Video uploaded and processed successfully",
            "file_path": file_path,
            "metadata": result
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_videos():
    try:
        videos = []
        for filename in os.listdir("uploads"):
            if filename.endswith(('.mp4', '.mov', '.avi', '.mkv')):
                file_path = os.path.join("uploads", filename)
                videos.append({
                    "filename": filename,
                    "path": file_path,
                    "size": os.path.getsize(file_path)
                })
        return videos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{filename}")
async def delete_video(filename: str):
    try:
        file_path = os.path.join("uploads", filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return {"message": f"Video {filename} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Video not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 