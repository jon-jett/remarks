import os
import click
import json
from typing import Optional

from ..downloader.video_downloader import download_video, get_video_info
from ..transcriber.transcriber import transcribe_video, parse_fcpxml
from ..utils.config import load_config, save_config, AppConfig, update_download_path, update_cookie_file, update_openai_api_key

# Progress callback for CLI
def cli_progress_callback(status: str, percent: float, message: str):
    """Simple CLI progress callback"""
    if status == "error":
        click.echo(f"Error: {message}")
    else:
        if percent > 0:
            # Create a simple progress bar
            bar_width = 40
            filled_width = int(bar_width * percent)
            bar = '█' * filled_width + '-' * (bar_width - filled_width)
            click.echo(f"\r[{bar}] {percent*100:.1f}% {message}", nl=False)
        else:
            click.echo(f"\r{message}", nl=False)

@click.group()
def cli():
    """Remarks - Video processing toolbox"""
    pass

# Download commands
@cli.group()
def download():
    """Video download commands"""
    pass

@download.command('url')
@click.argument('url')
@click.option('--path', '-p', type=click.Path(), help='Download path')
@click.option('--format', '-f', default='best', help='Video format')
@click.option('--cookie-file', '-c', type=click.Path(exists=True), help='Cookie file')
def download_url(url: str, path: Optional[str], format: str, cookie_file: Optional[str]):
    """Download a video from URL"""
    click.echo(f"Downloading video from: {url}")
    
    success, message, file_path = download_video(
        url=url,
        download_path=path,
        format_option=format,
        cookie_file=cookie_file,
        progress_callback=cli_progress_callback
    )
    
    # Add a newline after progress output
    click.echo()
    
    if success:
        click.secho(f"Success: {message}", fg="green")
        click.echo(f"File: {file_path}")
    else:
        click.secho(f"Failed: {message}", fg="red")

@download.command('info')
@click.argument('url')
@click.option('--cookie-file', '-c', type=click.Path(exists=True), help='Cookie file')
def get_info(url: str, cookie_file: Optional[str]):
    """Get video information without downloading"""
    click.echo(f"Getting info for: {url}")
    
    info = get_video_info(url, cookie_file)
    
    if "error" in info:
        click.secho(f"Error: {info['error']}", fg="red")
    else:
        click.secho(f"Title: {info.get('title', 'Unknown')}", fg="green")
        click.echo(f"Duration: {info.get('duration_string', 'Unknown')}")
        click.echo(f"Uploader: {info.get('uploader', 'Unknown')}")
        
        # Show available formats
        click.echo("\nAvailable formats:")
        for format in info.get('formats', []):
            format_id = format.get('format_id', 'unknown')
            format_note = format.get('format_note', '')
            ext = format.get('ext', '')
            resolution = format.get('resolution', '')
            
            if format_note and resolution:
                click.echo(f"  - {format_id}: {format_note} ({resolution}, {ext})")

# Transcribe commands
@cli.group()
def transcribe():
    """Video transcription commands"""
    pass

@transcribe.command('video')
@click.argument('video_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output transcript path')
@click.option('--language', '-l', default='en', help='Language code')
def transcribe_video_cmd(video_path: str, output: Optional[str], language: str):
    """Transcribe a video file"""
    click.echo(f"Transcribing video: {video_path}")
    
    success, message, transcript_path, _ = transcribe_video(
        video_path=video_path,
        output_path=output,
        progress_callback=cli_progress_callback
    )
    
    # Add a newline after progress output
    click.echo()
    
    if success:
        click.secho(f"Success: {message}", fg="green")
        click.echo(f"Transcript: {transcript_path}")
        
        # Display part of the transcript
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)
                text = transcript_data.get('text', '')
                preview = text[:200] + '...' if len(text) > 200 else text
                click.echo(f"\nTranscript preview:\n{preview}")
        except Exception as e:
            click.echo(f"Could not read transcript: {e}")
    else:
        click.secho(f"Failed: {message}", fg="red")

@transcribe.command('fcpxml')
@click.argument('fcpxml_path', type=click.Path(exists=True))
def transcribe_fcpxml_cmd(fcpxml_path: str):
    """Parse FCPXML and prepare for transcription"""
    click.echo(f"Parsing FCPXML: {fcpxml_path}")
    
    success, message, clips_data = parse_fcpxml(
        fcpxml_path=fcpxml_path,
        progress_callback=cli_progress_callback
    )
    
    # Add a newline after progress output
    click.echo()
    
    if success:
        click.secho(f"Success: {message}", fg="green")
        if clips_data:
            click.echo(f"Found {len(clips_data.get('clips', []))} clips")
    else:
        click.secho(f"Failed: {message}", fg="red")

# Config commands
@cli.group()
def config():
    """Configuration commands"""
    pass

@config.command('show')
def show_config():
    """Show current configuration"""
    config = load_config()
    click.echo(json.dumps(config.model_dump(), indent=2))

@config.command('set-download-path')
@click.argument('path', type=click.Path())
def set_download_path(path: str):
    """Set default download path"""
    if update_download_path(path):
        click.secho(f"Download path updated to: {path}", fg="green")
    else:
        click.secho("Failed to update download path", fg="red")

@config.command('set-cookie-file')
@click.argument('path', type=click.Path(exists=True))
def set_cookie_file(path: str):
    """Set cookie file for downloads"""
    if update_cookie_file(path):
        click.secho(f"Cookie file updated to: {path}", fg="green")
    else:
        click.secho("Failed to update cookie file", fg="red")

@config.command('set-openai-api-key')
@click.argument('api_key')
def set_openai_api_key(api_key: str):
    """Set OpenAI API key for transcription"""
    if update_openai_api_key(api_key):
        click.secho("OpenAI API key updated", fg="green")
    else:
        click.secho("Failed to update OpenAI API key", fg="red")

if __name__ == '__main__':
    cli() 