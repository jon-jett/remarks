#!/usr/bin/env python3
import os
import sys
import platform
import subprocess
import shutil
import urllib.request
import zipfile
import tarfile
from pathlib import Path

def get_ffmpeg_url() -> str:
    """Get the appropriate FFmpeg download URL based on the platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == "darwin":  # macOS
        if machine == "arm64":  # Apple Silicon
            return "https://evermeet.cx/ffmpeg/ffmpeg-6.1.zip"
        else:  # Intel
            return "https://evermeet.cx/ffmpeg/ffmpeg-6.1.zip"
    elif system == "linux":
        if machine == "x86_64":
            return "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        elif machine == "aarch64":
            return "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz"
    elif system == "windows":
        return "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    
    raise RuntimeError(f"Unsupported platform: {system} {machine}")

def download_file(url: str, destination: str) -> None:
    """Download a file from the given URL to the destination path."""
    print(f"Downloading FFmpeg from {url}...")
    urllib.request.urlretrieve(url, destination)

def extract_archive(archive_path: str, extract_path: str) -> None:
    """Extract the downloaded archive."""
    print(f"Extracting {archive_path}...")
    if archive_path.endswith('.zip'):
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
    elif archive_path.endswith('.tar.xz'):
        with tarfile.open(archive_path, 'r:xz') as tar_ref:
            tar_ref.extractall(extract_path)

def setup_ffmpeg() -> None:
    """Download and set up FFmpeg for the current platform."""
    # Get the backend directory
    backend_dir = Path(__file__).parent.parent
    bin_dir = backend_dir / "bin"
    bin_dir.mkdir(exist_ok=True)
    
    # Get the appropriate FFmpeg URL
    url = get_ffmpeg_url()
    archive_name = url.split('/')[-1]
    archive_path = bin_dir / archive_name
    
    try:
        # Download FFmpeg
        download_file(url, str(archive_path))
        
        # Extract the archive
        extract_archive(str(archive_path), str(bin_dir))
        
        # Clean up the archive
        archive_path.unlink()
        
        # On macOS, the binary is directly in the zip
        if platform.system().lower() == "darwin":
            ffmpeg_path = bin_dir / "ffmpeg"
            if not ffmpeg_path.exists():
                raise RuntimeError("FFmpeg binary not found in the downloaded archive")
        else:
            # On other platforms, we need to find the binary in the extracted directory
            for file in bin_dir.glob("**/ffmpeg"):
                if file.is_file():
                    shutil.move(str(file), str(bin_dir / "ffmpeg"))
                    break
            else:
                raise RuntimeError("FFmpeg binary not found in the downloaded archive")
        
        # Make the binary executable
        ffmpeg_path = bin_dir / "ffmpeg"
        ffmpeg_path.chmod(0o755)
        
        print(f"FFmpeg has been successfully set up at {ffmpeg_path}")
        
    except Exception as e:
        print(f"Error setting up FFmpeg: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_ffmpeg() 