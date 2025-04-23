import os
import re
import yt_dlp
from typing import Optional, Dict, Any, Callable, List, Tuple
from pathlib import Path

from ..utils.config import get_download_path, get_cookie_file

class DownloadProgress:
    """Class to track download progress"""
    def __init__(self, callback: Optional[Callable[[str, float, str], None]] = None):
        self.callback = callback
        self.status = "initializing"
        self.percent = 0.0
        self.message = ""
    
    def update(self, status: str, percent: float = 0.0, message: str = ""):
        """Update the progress status"""
        self.status = status
        self.percent = percent
        self.message = message
        
        if self.callback:
            self.callback(status, percent, message)

def strip_ansi_codes(text: str) -> str:
    """Strip ANSI color codes from strings"""
    if not isinstance(text, str):
        return text
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def progress_hook(d: Dict[str, Any], progress: DownloadProgress):
    """Hook function for yt-dlp to report progress"""
    if '_percent_str' in d:
        percent_str = strip_ansi_codes(d.get('_percent_str', '0%'))
        # Remove any non-numeric characters except dot
        percent_clean = re.sub(r'[^\d.]', '', percent_str)
        
        if percent_clean:
            try:
                percent_float = float(percent_clean)
                progress.update("downloading", percent_float / 100, f"{percent_str} complete")
            except:
                progress.update("downloading", 0.0, d.get('status', 'downloading'))
        else:
            progress.update("downloading", 0.0, d.get('status', 'downloading'))
    
    elif 'status' in d:
        if d['status'] == 'finished':
            progress.update("processing", 1.0, "Download finished, processing file...")
        else:
            progress.update(d['status'], 0.0, f"Status: {d['status']}")

def download_video(
    url: str, 
    download_path: Optional[str] = None, 
    format_option: str = 'best',
    cookie_file: Optional[str] = None,
    progress_callback: Optional[Callable[[str, float, str], None]] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Download video using yt-dlp
    
    Args:
        url: URL of the video to download
        download_path: Path where the video will be saved (uses config if None)
        format_option: Video format to download
        cookie_file: Path to a cookie file (uses config if None)
        progress_callback: Callback function for progress updates
        
    Returns:
        Tuple of (success, message, file_path)
    """
    try:
        # Use config values if not provided
        if download_path is None:
            download_path = get_download_path()
        
        if cookie_file is None:
            cookie_file = get_cookie_file()
        
        # Create download directory if it doesn't exist
        os.makedirs(download_path, exist_ok=True)
        
        # Initialize progress tracker
        progress = DownloadProgress(progress_callback)
        progress.update("initializing", 0.0, "Preparing to download...")
        
        # Configure options
        ydl_opts = {
            'format': format_option,
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'progress_hooks': [lambda d: progress_hook(d, progress)],
            'no_color': True,
        }
        
        # Add cookie file if available
        if cookie_file and os.path.exists(cookie_file):
            ydl_opts['cookiefile'] = cookie_file
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            progress.update("extracting", 0.0, "Extracting video information...")
            info = ydl.extract_info(url, download=True)
            
            video_title = info.get('title', 'video')
            video_ext = info.get('ext', 'mp4')
            video_path = os.path.join(download_path, f"{video_title}.{video_ext}")
            
            progress.update("complete", 1.0, f"Download complete: {video_title}.{video_ext}")
            return True, f"Successfully downloaded: {video_title}.{video_ext}", video_path
            
    except Exception as e:
        error_message = f"Error downloading video: {str(e)}"
        if progress_callback:
            progress_callback("error", 0.0, error_message)
        return False, error_message, None

def get_video_info(url: str, cookie_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Get information about a video without downloading it
    
    Args:
        url: URL of the video
        cookie_file: Path to a cookie file (uses config if None)
        
    Returns:
        Dictionary with video information
    """
    try:
        if cookie_file is None:
            cookie_file = get_cookie_file()
            
        ydl_opts = {
            'skip_download': True,
            'no_color': True,
        }
        
        if cookie_file and os.path.exists(cookie_file):
            ydl_opts['cookiefile'] = cookie_file
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    
    except Exception as e:
        print(f"Error getting video info: {e}")
        return {"error": str(e)} 