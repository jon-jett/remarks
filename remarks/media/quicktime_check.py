import os
import subprocess
import json
from typing import Tuple, Dict, Any, List, Optional
import ffmpeg

def is_quicktime_compatible(file_path: str) -> Tuple[bool, str]:
    """
    Check if a video file is QuickTime compatible.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Tuple of (is_compatible, reason)
    """
    if not os.path.exists(file_path):
        return False, f"File does not exist: {file_path}"
    
    try:
        # Use ffprobe to get file information
        probe = ffmpeg.probe(file_path)
        
        # Get video streams
        video_streams = [stream for stream in probe.get('streams', []) if stream.get('codec_type') == 'video']
        
        if not video_streams:
            return False, "No video stream found"
        
        # Get primary video stream
        video = video_streams[0]
        codec_name = video.get('codec_name', '').lower()
        
        # Check if codec is QuickTime compatible
        # QuickTime primarily supports: h264, hevc (h265), ProRes, MJPEG, and a few others
        qt_compatible_codecs = ['h264', 'hevc', 'prores', 'mjpeg', 'mpeg4', 'mpeg2video', 'motion_jpeg']
        
        if codec_name in qt_compatible_codecs:
            return True, f"Compatible codec: {codec_name}"
        else:
            return False, f"Incompatible codec: {codec_name}"
    
    except Exception as e:
        return False, f"Error checking compatibility: {str(e)}"

def get_media_info(file_path: str) -> Dict[str, Any]:
    """
    Get detailed information about a media file.
    
    Args:
        file_path: Path to the media file
        
    Returns:
        Dictionary containing file information
    """
    if not os.path.exists(file_path):
        return {"error": f"File does not exist: {file_path}"}
    
    try:
        # Use ffprobe to get file information
        probe = ffmpeg.probe(file_path)
        
        # Extract key information
        result = {
            "filename": os.path.basename(file_path),
            "format": probe.get('format', {}).get('format_name', 'unknown'),
            "duration": float(probe.get('format', {}).get('duration', 0)),
            "size_bytes": int(probe.get('format', {}).get('size', 0)),
            "bit_rate": int(probe.get('format', {}).get('bit_rate', 0)),
            "video_streams": [],
            "audio_streams": [],
            "is_quicktime_compatible": False,
            "compatibility_reason": ""
        }
        
        # Add video stream information
        for stream in probe.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_info = {
                    "codec": stream.get('codec_name', 'unknown'),
                    "width": stream.get('width', 0),
                    "height": stream.get('height', 0),
                    "frame_rate": eval(stream.get('r_frame_rate', '0/1')),
                    "bit_depth": stream.get('bits_per_raw_sample', 'unknown'),
                    "pixel_format": stream.get('pix_fmt', 'unknown')
                }
                result["video_streams"].append(video_info)
            
            elif stream.get('codec_type') == 'audio':
                audio_info = {
                    "codec": stream.get('codec_name', 'unknown'),
                    "sample_rate": stream.get('sample_rate', 'unknown'),
                    "channels": stream.get('channels', 0),
                    "bit_depth": stream.get('bits_per_sample', 'unknown')
                }
                result["audio_streams"].append(audio_info)
        
        # Check QuickTime compatibility
        is_compatible, reason = is_quicktime_compatible(file_path)
        result["is_quicktime_compatible"] = is_compatible
        result["compatibility_reason"] = reason
        
        return result
    
    except Exception as e:
        return {"error": f"Error getting media info: {str(e)}"}

if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        compatible, reason = is_quicktime_compatible(file_path)
        print(f"Is QuickTime compatible: {compatible}")
        print(f"Reason: {reason}")
        
        print("\nDetailed Media Info:")
        info = get_media_info(file_path)
        print(json.dumps(info, indent=2)) 