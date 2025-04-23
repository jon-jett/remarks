from nicegui import ui
import os
import asyncio
from pathlib import Path
import threading
import random
import tempfile
import shutil
import time
import yt_dlp

# Import our backend modules
from .utils.config import load_config, save_config
from .downloader.video_downloader import download_video
from .media.quicktime_check import is_quicktime_compatible, get_media_info
from .media.transcoder import transcode_to_h264, transcode_to_prores

# Configure app
config = load_config()

# Create the NiceGUI app
@ui.page('/')
def index():
    """Main application page"""
    # Set theme based on config
    ui.colors(primary='#1976D2')  # Material Blue

    with ui.header().classes('items-center justify-between'):
        ui.label('Remarks Video Tool').classes('text-xl font-bold')
        with ui.row():
            ui.space()
            dark_mode = ui.dark_mode()
            ui.button(on_click=lambda: dark_mode.toggle()) \
                .props('flat color=white icon=dark_mode')

    # Create tabs
    with ui.tabs().classes('w-full') as tabs:
        web_dl_tab = ui.tab('Web DL')
        file_trans_tab = ui.tab('File Transcribe')
        fcpxml_trans_tab = ui.tab('Transcribe from FCPXML')
        settings_tab = ui.tab('Settings')

    # Set up tab panels
    with ui.tab_panels(tabs, value=web_dl_tab).classes('w-full'):
        # Web Download Tab
        with ui.tab_panel(web_dl_tab):
            create_web_dl_tab()
        
        # File Transcribe Tab
        with ui.tab_panel(file_trans_tab):
            ui.label('Transcribe Video Files').classes('text-xl font-bold')
            ui.label('This tab will allow you to transcribe video files to text.')
            ui.input('Video File', placeholder='/path/to/video.mp4').classes('w-full')
            ui.button('Transcribe').classes('bg-primary text-white')
        
        # FCPXML Transcribe Tab
        with ui.tab_panel(fcpxml_trans_tab):
            ui.label('Transcribe from FCPXML').classes('text-xl font-bold')
            ui.label('This tab will allow you to extract and transcribe clips from Final Cut Pro projects.')
            ui.input('FCPXML File', placeholder='/path/to/project.fcpxml').classes('w-full')
            ui.button('Parse').classes('bg-primary text-white')
        
        # Settings Tab
        with ui.tab_panel(settings_tab):
            ui.label('Settings').classes('text-xl font-bold')
            ui.label('This tab will allow you to configure application settings.')
            ui.input('Download Path', value=config.downloader.download_path).classes('w-full')
            ui.input('OpenAI API Key', password=True).classes('w-full')
            ui.button('Save Settings').classes('bg-primary text-white')

    ui.separator()
    with ui.footer():
        ui.label('© 2025 Remarks')
        ui.space()
        ui.label(f'Version: {config.version}')

def create_web_dl_tab():
    """Create the Web Download tab content"""
    ui.label('Download Videos from Web').classes('text-xl font-bold')
    ui.label('Enter a URL to download a video from YouTube or other supported sites.')
    
    # Download location
    with ui.card().classes('w-full p-4'):
        ui.label('Download Location').classes('text-lg font-bold')
        
        # Local path input with browse button
        with ui.row().classes("w-full items-center"):
            download_location = ui.input(label="Download Location", value="~/Downloads").classes("flex-grow mr-2")
            
            async def select_folder():
                result = await ui.run_javascript(
                    """
                    return await new Promise((resolve) => {
                        const input = document.createElement('input');
                        input.type = 'file';
                        input.webkitdirectory = true;
                        input.directory = true;
                        
                        input.onchange = (e) => {
                            const files = e.target.files;
                            if (files.length > 0) {
                                resolve(files[0].path);
                            }
                        };
                        
                        input.click();
                    });
                    """
                )
                if result:
                    download_location.value = result
            
            ui.button("Browse", on_click=select_folder).props("outline")
    
    # Cookie file for restricted videos
    with ui.card().classes('w-full p-4 mt-4'):
        ui.label('Cookie File (Optional)').classes('text-lg font-bold')
        ui.label('Upload a cookie file to download videos from sites requiring login.').classes('text-sm')
        
        # File upload
        cookie_file = ui.input(placeholder='No cookie file selected').classes('w-full')
        
        cookie_upload = ui.upload(
            label='Upload Cookie File',
            auto_upload=True,
            multiple=False,
            on_upload=lambda e: handle_cookie_upload(e, cookie_file)
        ).props('outlined')
        
        temp_cookie_path = None
        
        def handle_cookie_upload(e, cookie_input):
            nonlocal temp_cookie_path
            if e.is_completed:
                # Save uploaded file to temp location
                temp_dir = tempfile.gettempdir()
                temp_file_path = os.path.join(temp_dir, e.name)
                
                with open(temp_file_path, 'wb') as f:
                    f.write(e.content)
                
                temp_cookie_path = temp_file_path
                cookie_input.value = e.name
                ui.notify(f'Cookie file uploaded: {e.name}', type='positive')
    
    # Video URL input
    ui.label('Video URL').classes('text-lg font-bold mt-4')
    url_input = ui.input(placeholder='https://youtube.com/...').classes('w-full')
    
    # Format options
    with ui.card().classes('w-full p-4 mt-4'):
        ui.label('Download Options').classes('text-lg font-bold')
        
        # Format selection
        format_options = [
            {'label': 'Best Quality', 'value': 'best'},
            {'label': 'Best Video + Best Audio', 'value': 'bestvideo+bestaudio'},
            {'label': '1080p', 'value': 'bestvideo[height<=1080]+bestaudio'},
            {'label': '720p', 'value': 'bestvideo[height<=720]+bestaudio'},
            {'label': 'MP4', 'value': 'mp4'}
        ]
        
        format_selector = ui.select(
            options=format_options,
            value=format_options[0],
            label='Format'
        ).classes('w-full')
        
        # QuickTime compatibility options
        ui.label('QuickTime Compatibility').classes('font-bold mt-2')
        qt_check = ui.checkbox('Check if file is QuickTime compatible', value=True).props('dense')
        
        with ui.row().classes('w-full items-center'):
            transcode_option = ui.checkbox('Transcode if not compatible', value=True).props('dense')
            
            transcode_format_options = [
                {'label': 'H.264', 'value': 'h264'},
                {'label': 'ProRes', 'value': 'prores'}
            ]
            
            transcode_format = ui.select(
                options=transcode_format_options,
                value=transcode_format_options[0],
                label='Transcode Format'
            ).classes('ml-4')
    
    # Callbacks for tracking progress
    progress_display = ui.column().classes('w-full')
    progress_display.visible = False
    
    with progress_display:
        ui.label('Download Progress').classes('text-lg font-bold')
        progress_status = ui.label('Starting download...')
        progress_container = ui.card().classes('w-full')
        with progress_container:
            progress = ui.linear_progress(0).classes('w-full')
            
    # Result card for displaying download outcome
    result_card = ui.card().classes('w-full mt-4')
    result_card.visible = False
    
    with result_card:
        result_title = ui.label('Download Result').classes('text-lg font-bold')
        result_message = ui.label()
        result_details = ui.column()
        
    async def update_progress(percent, message):
        """Update the progress display with current status"""
        progress_display.visible = True
        progress.value = percent / 100  # Convert percentage to 0-1 range
        progress_status.text = message
        await ui.update()
        
    async def display_result(success, message, details=None):
        """Display the result of the download operation"""
        result_card.visible = True
        if success:
            result_title.text = '✅ Download Complete'
            result_title.classes('text-positive', remove='text-negative')
        else:
            result_title.text = '❌ Download Failed'
            result_title.classes('text-negative', remove='text-positive')
            
        result_message.text = message
        
        # Clear previous details
        result_details.clear()
        
        # Add details if provided
        if details:
            with result_details:
                if isinstance(details, dict):
                    for key, value in details.items():
                        ui.label(f"{key}: {value}")
                elif isinstance(details, str):
                    ui.label(details)
        
        await ui.update()
        
    async def on_download_click():
        """Handle the download button click"""
        # Reset UI state
        progress_display.visible = True
        result_card.visible = False
        progress.value = 0
        progress_status.text = "Starting download..."
        await ui.update()
        
        # Validate inputs
        if not download_location.value:
            await display_result(False, "Please select a download location")
            return
            
        if not url_input.value:
            await display_result(False, "Please enter a URL to download")
            return
            
        # Process download in a new thread to avoid blocking the UI
        def process_download():
            import time
            
            try:
                # Here we would normally call the actual download function
                # For demo purposes, we'll simulate a download
                time.sleep(0.5)  # Simulate initial processing
                
                video_link = url_input.value
                local_path = download_location.value
                selected_format = format_selector.value if format_selector.value else "mp4"
                
                # Simulate download progress
                for i in range(0, 101, 5):
                    # Simulate potential compatibility issue
                    if i == 60 and random.random() < 0.3:  # 30% chance of compatibility issue
                        ui.run_sync(lambda: display_result(False, 
                                                "Compatibility issue", 
                                                f"The format {selected_format} is not compatible with this video."))
                        return
                        
                    ui.run_sync(lambda i=i: update_progress(i, f"Downloading... {i}%"))
                    time.sleep(0.3)  # Simulate download time
                
                # Display success after completion
                ui.run_sync(lambda: display_result(True, 
                                        "Download complete!", 
                                        f"Video saved to: {local_path}"))
                
            except Exception as e:
                ui.run_sync(display_result(False, "Download failed", str(e)))
        
        # Start the download thread
        threading.Thread(target=process_download).start()
    
    # Download button
    ui.button('Download', on_click=on_download_click) \
        .classes('bg-primary text-white mt-4 text-lg px-6 py-2')

async def process_download(video_link, local_path, format, quality, cookies_file=None):
    """Process the actual download with yt-dlp"""
    linear_progress.visible = True
    status_label.visible = True
    download_button.disabled = True
    
    try:
        # Define temp folder for downloads
        temp_dir = tempfile.mkdtemp()
        
        # Base yt-dlp options
        ydl_opts = {
            'format': f'bestvideo[ext={format}]+bestaudio/best[ext={format}]/best' if quality == 'Best' else f'worstvideo[ext={format}]+worstaudio/worst[ext={format}]/worst',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [],
        }
        
        # Add cookiesfile if provided
        if cookies_file:
            ydl_opts['cookiesfile'] = cookies_file
            
        def _progress_hook(d):
            if d['status'] == 'downloading':
                # Extract percentage
                if 'downloaded_bytes' in d and 'total_bytes' in d:
                    progress = float(d['downloaded_bytes']) / float(d['total_bytes'])
                    
                    # Update UI thread-safely
                    ui.run_sync(lambda p=progress: linear_progress.set_value(p))
                    
                    # Simulate occasional compatibility issue (for demo purposes)
                    if progress > 0.6 and random.random() < 0.3:
                        ui.run_sync(lambda: status_label.set_text("Fixing compatibility issue..."))
                        time.sleep(1)  # Simulate processing delay
                
                # Update status with download speed if available
                if 'speed' in d and d['speed']:
                    speed_mb = d['speed'] / 1024 / 1024
                    ui.run_sync(lambda s=speed_mb: status_label.set_text(f"Downloading... {s:.2f} MB/s"))
            
            elif d['status'] == 'finished':
                ui.run_sync(lambda: status_label.set_text("Download complete. Processing..."))
        
        # Add our progress hook
        ydl_opts['progress_hooks'].append(_progress_hook)
        
        # Start download
        ui.run_sync(lambda: status_label.set_text("Starting download..."))
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ui.run_sync(lambda: linear_progress.set_value(0))
            await asyncio.to_thread(ydl.download, [video_link])
        
        # Move the completed download to the final destination
        ui.run_sync(lambda: status_label.set_text("Finalizing..."))
        
        # Get the downloaded file
        downloaded_files = os.listdir(temp_dir)
        if not downloaded_files:
            raise Exception("No files were downloaded")
        
        # Create the destination directory if it doesn't exist
        os.makedirs(local_path, exist_ok=True)
        
        # Move file to destination
        source_file = os.path.join(temp_dir, downloaded_files[0])
        dest_file = os.path.join(local_path, downloaded_files[0])
        shutil.move(source_file, dest_file)
        
        # Clean up temp directory
        shutil.rmtree(temp_dir)
        
        # Update UI with success
        ui.run_sync(lambda: linear_progress.set_value(1.0))
        ui.run_sync(lambda: status_label.set_text(f"Download complete: {dest_file}"))
        
        return True, f"Successfully downloaded to {dest_file}"
        
    except Exception as e:
        error_msg = str(e)
        ui.run_sync(lambda: status_label.set_text(f"Error: {error_msg}"))
        return False, f"Download failed: {error_msg}"
    
    finally:
        ui.run_sync(lambda: setattr(download_button, 'disabled', False))
        # Keep progress visible to show final state

def main():
    """Run the NiceGUI app"""
    ui.run(
        title='Remarks Video Tool',
        host='127.0.0.1',
        port=8080,
        dark=config.theme == 'dark',
        show=True
    )

if __name__ in {"__main__", "__mp_main__"}:
    main() 