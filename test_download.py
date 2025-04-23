from remarks.downloader.video_downloader import download_video

def progress_callback(status, percent, message):
    """Print download progress updates"""
    print(f"Status: {status} | Progress: {percent:.1%} | {message}")

def main():
    # YouTube video URL
    video_url = "https://www.youtube.com/watch?v=fOg5MtrN06o"
    
    # Download path (leave as None to use configured default)
    download_path = None
    
    # Format option (best quality)
    format_option = "best"
    
    print(f"Starting download of {video_url}")
    
    # Download the video
    success, message, file_path = download_video(
        url=video_url,
        download_path=download_path,
        format_option=format_option,
        progress_callback=progress_callback
    )
    
    if success:
        print(f"Success! Video saved to: {file_path}")
    else:
        print(f"Download failed: {message}")

if __name__ == "__main__":
    main() 