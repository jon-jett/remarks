import os
import subprocess
import json
import time
from typing import Optional, Dict, Any, Callable, List, Tuple, Union
from pathlib import Path
import ffmpeg
import openai
from ..utils.config import get_openai_api_key, TranscriberSettings

class TranscriptionProgress:
    """Class to track transcription progress"""
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

def extract_audio(
    video_path: str, 
    output_path: Optional[str] = None,
    progress: Optional[TranscriptionProgress] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Extract audio from video file
    
    Args:
        video_path: Path to the video file
        output_path: Path where the audio will be saved (uses video directory if None)
        progress: Progress tracker
        
    Returns:
        Tuple of (success, message, audio_path)
    """
    try:
        if progress:
            progress.update("extracting_audio", 0.1, "Extracting audio from video...")
        
        # If output path is not provided, use the same directory as the video
        if output_path is None:
            video_dir = os.path.dirname(video_path)
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(video_dir, f"{video_name}.mp3")
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Extract audio using ffmpeg
        ffmpeg.input(video_path).output(
            output_path, 
            acodec='libmp3lame', 
            ab='128k', 
            ac=1,
            ar='44100'
        ).run(quiet=True, overwrite_output=True)
        
        if progress:
            progress.update("audio_extracted", 0.2, "Audio extraction complete")
        
        return True, "Audio extraction complete", output_path
    
    except Exception as e:
        error_message = f"Error extracting audio: {str(e)}"
        if progress:
            progress.update("error", 0, error_message)
        return False, error_message, None

def transcribe_with_openai(
    audio_path: str,
    api_key: Optional[str] = None,
    language: str = "en",
    output_path: Optional[str] = None,
    progress: Optional[TranscriptionProgress] = None
) -> Tuple[bool, str, Optional[str], Optional[Dict]]:
    """
    Transcribe audio using OpenAI Whisper API
    
    Args:
        audio_path: Path to the audio file
        api_key: OpenAI API key (uses config if None)
        language: Language code
        output_path: Path where the transcript will be saved (uses audio directory if None)
        progress: Progress tracker
        
    Returns:
        Tuple of (success, message, transcript_path, transcript_data)
    """
    try:
        # Use config API key if not provided
        if api_key is None:
            api_key = get_openai_api_key()
        
        if not api_key:
            return False, "OpenAI API key not configured", None, None
        
        if progress:
            progress.update("transcribing", 0.3, "Transcribing audio with OpenAI...")
        
        # Set OpenAI API key
        openai.api_key = api_key
        
        # Open the audio file
        with open(audio_path, "rb") as audio_file:
            # Transcribe using OpenAI Whisper API
            response = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language
            )
        
        transcript_text = response.text
        
        # Format transcript data
        transcript_data = {
            "text": transcript_text,
            "language": language,
            "source": "openai",
            "timestamp": time.time()
        }
        
        # If output path is not provided, use the same directory as the audio
        if output_path is None:
            audio_dir = os.path.dirname(audio_path)
            audio_name = os.path.splitext(os.path.basename(audio_path))[0]
            output_path = os.path.join(audio_dir, f"{audio_name}_transcript.json")
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save transcript to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        
        if progress:
            progress.update("complete", 1.0, "Transcription complete")
        
        return True, "Transcription complete", output_path, transcript_data
    
    except Exception as e:
        error_message = f"Error transcribing with OpenAI: {str(e)}"
        if progress:
            progress.update("error", 0, error_message)
        return False, error_message, None, None

def transcribe_video(
    video_path: str,
    output_path: Optional[str] = None,
    settings: Optional[TranscriberSettings] = None,
    progress_callback: Optional[Callable[[str, float, str], None]] = None
) -> Tuple[bool, str, Optional[str], Optional[Dict]]:
    """
    Transcribe a video file
    
    Args:
        video_path: Path to the video file
        output_path: Path where the transcript will be saved (uses video directory if None)
        settings: Transcription settings
        progress_callback: Callback function for progress updates
        
    Returns:
        Tuple of (success, message, transcript_path, transcript_data)
    """
    # Initialize progress tracker
    progress = TranscriptionProgress(progress_callback)
    progress.update("initializing", 0.0, "Preparing to transcribe...")
    
    # Extract audio from video
    audio_success, audio_message, audio_path = extract_audio(
        video_path, 
        output_path=None,  # Auto-generate in the same directory
        progress=progress
    )
    
    if not audio_success or audio_path is None:
        return False, audio_message, None, None
    
    # Transcribe the audio with OpenAI
    return transcribe_with_openai(
        audio_path,
        api_key=get_openai_api_key(),
        language="en",
        output_path=output_path,
        progress=progress
    )

def parse_fcpxml(
    fcpxml_path: str,
    progress_callback: Optional[Callable[[str, float, str], None]] = None
) -> Tuple[bool, str, Optional[Dict]]:
    """
    Parse FCPXML file to extract clips for transcription
    
    Args:
        fcpxml_path: Path to the FCPXML file
        progress_callback: Callback function for progress updates
        
    Returns:
        Tuple of (success, message, clips_data)
    """
    # This is a placeholder for FCPXML parsing functionality
    # We'll need to implement proper XML parsing for Final Cut Pro XML files
    
    try:
        progress = TranscriptionProgress(progress_callback)
        progress.update("parsing", 0.1, "Parsing FCPXML file...")
        
        # Placeholder for actual implementation
        # Here we would parse the XML and extract clip information
        
        progress.update("complete", 1.0, "FCPXML parsing complete")
        
        # Return a placeholder result
        return True, "FCPXML parsing complete", {
            "clips": [],
            "message": "FCPXML parsing placeholder - actual implementation needed"
        }
    
    except Exception as e:
        error_message = f"Error parsing FCPXML: {str(e)}"
        if progress_callback:
            progress_callback("error", 0, error_message)
        return False, error_message, None 