import os
import subprocess
import time
import ffmpeg
from typing import Tuple, Dict, Any, List, Optional, Callable

from .quicktime_check import is_quicktime_compatible, get_media_info

class TranscodeProgress:
    """Class to track transcoding progress"""
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

def transcode_to_h264(
    input_file: str,
    output_file: Optional[str] = None,
    preset: str = 'medium',
    crf: int = 23,
    progress_callback: Optional[Callable[[str, float, str], None]] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Transcode a video file to H.264 (QuickTime compatible).
    
    Args:
        input_file: Path to the input video file
        output_file: Path for the output file (if None, auto-generated)
        preset: x264 preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
        crf: Constant Rate Factor (0-51, lower is better quality, 18-28 is typical)
        progress_callback: Callback function for progress updates
        
    Returns:
        Tuple of (success, message, output_file_path)
    """
    if not os.path.exists(input_file):
        return False, f"Input file does not exist: {input_file}", None
    
    # Initialize progress tracker
    progress = TranscodeProgress(progress_callback)
    progress.update("initializing", 0.0, "Checking input file...")
    
    # Check if the file is already QuickTime compatible
    is_compatible, reason = is_quicktime_compatible(input_file)
    if is_compatible:
        progress.update("complete", 1.0, "File is already QuickTime compatible")
        return True, "File is already QuickTime compatible", input_file
    
    # Generate output filename if not provided
    if output_file is None:
        file_dir = os.path.dirname(input_file)
        file_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(file_dir, f"{file_name}_h264.mp4")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        # Get media info for duration calculation
        media_info = get_media_info(input_file)
        total_duration = media_info.get('duration', 0)
        
        # Setup progress monitoring (requires separate process monitoring)
        progress.update("transcoding", 0.05, "Starting transcoding...")
        
        # Setup transcoding process
        process = (
            ffmpeg
            .input(input_file)
            .output(
                output_file,
                vcodec='libx264',
                preset=preset,
                crf=crf,
                acodec='aac',
                audio_bitrate='128k',
                **{'movflags': '+faststart'}  # This optimizes for streaming/web playback
            )
            .global_args('-y', '-v', 'warning', '-stats')
            .run_async(pipe_stderr=True)
        )
        
        # Monitor progress
        last_progress = 0
        line_buffer = ""
        
        while True:
            char = process.stderr.read(1)
            if not char:
                break
                
            if char == b'\r' or char == b'\n':
                if "time=" in line_buffer:
                    # Extract time
                    time_parts = line_buffer.split("time=")[1].split()[0].split(":")
                    if len(time_parts) == 3:
                        hours, minutes, seconds = time_parts
                        current_time = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
                        if total_duration > 0:
                            percent = min(current_time / total_duration, 0.99)
                            progress.update("transcoding", percent, f"Transcoding: {percent*100:.1f}%")
                            last_progress = percent
                
                line_buffer = ""
            else:
                line_buffer += char.decode('utf-8', errors='replace')
        
        # Wait for process to complete
        process.wait()
        
        # Check if transcoding was successful
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            # Verify the output file is indeed QuickTime compatible
            is_compatible, reason = is_quicktime_compatible(output_file)
            if is_compatible:
                progress.update("complete", 1.0, "Transcoding complete")
                return True, "Transcoding successful", output_file
            else:
                progress.update("error", 0.0, f"Transcoded file is not QuickTime compatible: {reason}")
                return False, f"Transcoded file is not QuickTime compatible: {reason}", output_file
        else:
            progress.update("error", 0.0, "Transcoding failed - output file not created")
            return False, "Transcoding failed - output file not created", None
            
    except Exception as e:
        error_message = f"Error during transcoding: {str(e)}"
        progress.update("error", 0.0, error_message)
        return False, error_message, None

def transcode_to_prores(
    input_file: str,
    output_file: Optional[str] = None,
    profile: int = 3,  # 0=Proxy, 1=LT, 2=Standard, 3=HQ
    progress_callback: Optional[Callable[[str, float, str], None]] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Transcode a video file to ProRes (high quality QuickTime compatible).
    
    Args:
        input_file: Path to the input video file
        output_file: Path for the output file (if None, auto-generated)
        profile: ProRes profile (0-4)
        progress_callback: Callback function for progress updates
        
    Returns:
        Tuple of (success, message, output_file_path)
    """
    if not os.path.exists(input_file):
        return False, f"Input file does not exist: {input_file}", None
    
    # Initialize progress tracker
    progress = TranscodeProgress(progress_callback)
    progress.update("initializing", 0.0, "Checking input file...")
    
    # Generate output filename if not provided
    if output_file is None:
        file_dir = os.path.dirname(input_file)
        file_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(file_dir, f"{file_name}_prores.mov")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        # Get media info for duration calculation
        media_info = get_media_info(input_file)
        total_duration = media_info.get('duration', 0)
        
        # Setup progress monitoring
        progress.update("transcoding", 0.05, "Starting transcoding to ProRes...")
        
        # Setup transcoding process
        process = (
            ffmpeg
            .input(input_file)
            .output(
                output_file,
                vcodec='prores_ks',
                profile=profile,
                acodec='pcm_s16le',  # Uncompressed PCM audio
                **{'pix_fmt': 'yuv422p10le'}  # 10-bit 4:2:2 color space
            )
            .global_args('-y', '-v', 'warning', '-stats')
            .run_async(pipe_stderr=True)
        )
        
        # Monitor progress
        last_progress = 0
        line_buffer = ""
        
        while True:
            char = process.stderr.read(1)
            if not char:
                break
                
            if char == b'\r' or char == b'\n':
                if "time=" in line_buffer:
                    # Extract time
                    time_parts = line_buffer.split("time=")[1].split()[0].split(":")
                    if len(time_parts) == 3:
                        hours, minutes, seconds = time_parts
                        current_time = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
                        if total_duration > 0:
                            percent = min(current_time / total_duration, 0.99)
                            progress.update("transcoding", percent, f"Transcoding: {percent*100:.1f}%")
                            last_progress = percent
                
                line_buffer = ""
            else:
                line_buffer += char.decode('utf-8', errors='replace')
        
        # Wait for process to complete
        process.wait()
        
        # Check if transcoding was successful
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            # Verify the output file is indeed QuickTime compatible
            is_compatible, reason = is_quicktime_compatible(output_file)
            if is_compatible:
                progress.update("complete", 1.0, "Transcoding to ProRes complete")
                return True, "Transcoding to ProRes successful", output_file
            else:
                progress.update("error", 0.0, f"Transcoded ProRes file is not QuickTime compatible: {reason}")
                return False, f"Transcoded ProRes file is not QuickTime compatible: {reason}", output_file
        else:
            progress.update("error", 0.0, "Transcoding to ProRes failed - output file not created")
            return False, "Transcoding to ProRes failed - output file not created", None
            
    except Exception as e:
        error_message = f"Error during ProRes transcoding: {str(e)}"
        progress.update("error", 0.0, error_message)
        return False, error_message, None

if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        print(f"Transcoding {input_file} to H.264...")
        
        def print_progress(status, percent, message):
            print(f"\r[{status}] {percent*100:.1f}% {message}", end="")
            
        success, message, output_file = transcode_to_h264(
            input_file,
            progress_callback=print_progress
        )
        
        print(f"\nSuccess: {success}")
        print(f"Message: {message}")
        print(f"Output: {output_file}") 