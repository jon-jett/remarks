import os
import yt_dlp
import asyncio
import logging
import json
import requests
from playwright.async_api import async_playwright
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from enum import Enum
from typing import Optional, Dict, Any
import pathlib
import subprocess

logger = logging.getLogger(__name__)

class DownloadMethod(Enum):
    YT_DLP = "yt-dlp"
    PLAYWRIGHT = "playwright"
    SELENIUM = "selenium"
    DIRECT = "direct"
    FAILED = "failed"

class VideoDownloader:
    def __init__(self, download_dir: Optional[str] = None, cookie_dir: str = "cookies"):
        # Get user's home directory
        home_dir = str(pathlib.Path.home())
        
        # Set up shared library directory in Movies/remarks/library
        self.library_dir = os.path.join(home_dir, "Movies", "remarks", "library")
        os.makedirs(self.library_dir, exist_ok=True)
        
        # Use provided download_dir or default to library directory
        self.download_dir = download_dir if download_dir else self.library_dir
        self.cookie_dir = cookie_dir
        
        # Create directories if they don't exist
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.cookie_dir, exist_ok=True)
        
        # Set up FFmpeg path
        self.ffmpeg_path = self._setup_ffmpeg()
        
        logger.info(f"Using download directory: {self.download_dir}")
        logger.info(f"Using library directory: {self.library_dir}")
        logger.info(f"Using FFmpeg path: {self.ffmpeg_path}")

    def _setup_ffmpeg(self) -> str:
        """Set up and return the path to the FFmpeg binary."""
        # Get the directory where this file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Navigate up to the backend directory
        backend_dir = os.path.dirname(os.path.dirname(current_dir))
        # Path to the bin directory
        bin_dir = os.path.join(backend_dir, "bin")
        
        # Create bin directory if it doesn't exist
        os.makedirs(bin_dir, exist_ok=True)
        
        # Path to FFmpeg binary
        ffmpeg_path = os.path.join(bin_dir, "ffmpeg")
        
        # Check if FFmpeg exists
        if not os.path.exists(ffmpeg_path):
            logger.warning("FFmpeg binary not found in bin directory. Using system FFmpeg if available.")
            # Try to find system FFmpeg
            try:
                subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
                return "ffmpeg"  # Use system FFmpeg
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.error("No FFmpeg binary found. Please add FFmpeg to the bin directory.")
                raise RuntimeError("FFmpeg binary not found. Please add FFmpeg to the bin directory.")
        
        # Make sure the binary is executable
        os.chmod(ffmpeg_path, 0o755)
        return ffmpeg_path

    async def download(self, url: str, cookie_file: Optional[str] = None) -> Dict[str, Any]:
        """Attempt to download a video using multiple methods in sequence."""
        methods = [
            (self._try_yt_dlp, DownloadMethod.YT_DLP),
            (self._try_playwright, DownloadMethod.PLAYWRIGHT),
            (self._try_selenium, DownloadMethod.SELENIUM),
            (self._try_direct_download, DownloadMethod.DIRECT)
        ]

        for method, method_name in methods:
            try:
                result = await method(url, cookie_file)
                if result["success"]:
                    # If the file was downloaded to a different directory, move it to the library
                    if os.path.dirname(result["file_path"]) != self.library_dir:
                        new_path = os.path.join(self.library_dir, os.path.basename(result["file_path"]))
                        os.rename(result["file_path"], new_path)
                        result["file_path"] = new_path
                    
                    return {
                        "success": True,
                        "method": method_name.value,
                        "file_path": result["file_path"],
                        "metadata": result.get("metadata", {})
                    }
            except Exception as e:
                logger.error(f"Download method {method_name.value} failed: {str(e)}")
                continue

        return {
            "success": False,
            "method": DownloadMethod.FAILED.value,
            "error": "All download methods failed"
        }

    async def _try_yt_dlp(self, url: str, cookie_file: Optional[str] = None) -> Dict[str, Any]:
        """Attempt to download using yt-dlp."""
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'ffmpeg_location': self.ffmpeg_path
        }

        if cookie_file:
            cookie_path = os.path.join(self.cookie_dir, cookie_file)
            if os.path.exists(cookie_path):
                ydl_opts['cookiefile'] = cookie_path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            return {
                "success": True,
                "file_path": file_path,
                "metadata": {
                    "title": info.get('title'),
                    "duration": info.get('duration'),
                    "uploader": info.get('uploader'),
                    "upload_date": info.get('upload_date')
                }
            }

    async def _try_playwright(self, url: str, cookie_file: Optional[str] = None) -> Dict[str, Any]:
        """Attempt to download using Playwright."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()
            
            if cookie_file:
                cookie_path = os.path.join(self.cookie_dir, cookie_file)
                if os.path.exists(cookie_path):
                    with open(cookie_path, 'r') as f:
                        cookies = json.load(f)
                        await context.add_cookies(cookies)

            page = await context.new_page()
            await page.goto(url)
            
            # Wait for video element to be present
            await page.wait_for_selector('video')
            
            # Get video source URL
            video_src = await page.evaluate('() => document.querySelector("video").src')
            
            if not video_src:
                raise Exception("Could not find video source URL")

            # Download the video
            response = requests.get(video_src, stream=True)
            filename = os.path.join(self.download_dir, f"video_{hash(url)}.mp4")
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            await browser.close()
            return {
                "success": True,
                "file_path": filename
            }

    async def _try_selenium(self, url: str, cookie_file: Optional[str] = None) -> Dict[str, Any]:
        """Attempt to download using Selenium."""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        
        driver = webdriver.Chrome(options=options)
        
        try:
            if cookie_file:
                cookie_path = os.path.join(self.cookie_dir, cookie_file)
                if os.path.exists(cookie_path):
                    with open(cookie_path, 'r') as f:
                        cookies = json.load(f)
                        for cookie in cookies:
                            driver.add_cookie(cookie)

            driver.get(url)
            
            # Wait for video element
            video_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            
            video_src = video_element.get_attribute('src')
            if not video_src:
                raise Exception("Could not find video source URL")

            # Download the video
            response = requests.get(video_src, stream=True)
            filename = os.path.join(self.download_dir, f"video_{hash(url)}.mp4")
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            return {
                "success": True,
                "file_path": filename
            }
        finally:
            driver.quit()

    async def _try_direct_download(self, url: str, cookie_file: Optional[str] = None) -> Dict[str, Any]:
        """Attempt direct download of the URL."""
        headers = {}
        if cookie_file:
            cookie_path = os.path.join(self.cookie_dir, cookie_file)
            if os.path.exists(cookie_path):
                with open(cookie_path, 'r') as f:
                    cookies = json.load(f)
                    headers['Cookie'] = '; '.join([f"{c['name']}={c['value']}" for c in cookies])

        response = requests.get(url, headers=headers, stream=True)
        if response.status_code != 200:
            raise Exception(f"Direct download failed with status code {response.status_code}")

        filename = os.path.join(self.download_dir, f"video_{hash(url)}.mp4")
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return {
            "success": True,
            "file_path": filename
        }

    def upload_cookies(self, file: bytes, filename: str) -> str:
        """Save uploaded cookie file."""
        cookie_path = os.path.join(self.cookie_dir, filename)
        with open(cookie_path, 'wb') as f:
            f.write(file)
        return filename

    def list_cookie_files(self) -> list:
        """List available cookie files."""
        return [f for f in os.listdir(self.cookie_dir) if f.endswith('.json')]

    def delete_cookie_file(self, filename: str) -> bool:
        """Delete a cookie file."""
        cookie_path = os.path.join(self.cookie_dir, filename)
        if os.path.exists(cookie_path):
            os.remove(cookie_path)
            return True
        return False 