import ffmpeg
import os
from typing import Dict, Any
import asyncio
from pydub import AudioSegment
import json

class VideoProcessor:
    def __init__(self):
        self.supported_formats = ['.mp4', '.mov', '.avi', '.mkv']
    
    async def process_video(self, file_path: str) -> Dict[str, Any]:
        """Process a video file and extract metadata."""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Video file not found: {file_path}")
            
            # Get video metadata
            metadata = await self._get_video_metadata(file_path)
            
            # Extract audio for transcription
            audio_path = await self._extract_audio(file_path)
            
            return {
                "metadata": metadata,
                "audio_path": audio_path
            }
        except Exception as e:
            raise Exception(f"Error processing video: {str(e)}")
    
    async def _get_video_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract video metadata using ffmpeg."""
        try:
            probe = ffmpeg.probe(file_path)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            audio_info = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
            
            return {
                "duration": float(probe['format']['duration']),
                "width": int(video_info['width']),
                "height": int(video_info['height']),
                "fps": eval(video_info['r_frame_rate']),
                "codec": video_info['codec_name'],
                "audio_channels": audio_info['channels'],
                "audio_sample_rate": int(audio_info['sample_rate'])
            }
        except Exception as e:
            raise Exception(f"Error extracting metadata: {str(e)}")
    
    async def _extract_audio(self, file_path: str) -> str:
        """Extract audio from video file."""
        try:
            output_path = os.path.splitext(file_path)[0] + '.wav'
            
            # Use ffmpeg to extract audio
            stream = ffmpeg.input(file_path)
            stream = ffmpeg.output(stream, output_path, acodec='pcm_s16le', ac=1, ar='16k')
            await asyncio.to_thread(ffmpeg.run, stream, capture_stdout=True, capture_stderr=True)
            
            return output_path
        except Exception as e:
            raise Exception(f"Error extracting audio: {str(e)}")
    
    def convert_to_fcpxml(self, file_path: str, output_path: str) -> str:
        """Convert video to Final Cut Pro XML format."""
        try:
            # Basic FCPXML structure
            fcpxml = {
                "fcpxml": {
                    "version": "1.8",
                    "resources": {
                        "format": {
                            "id": "r1",
                            "name": "FFVideoFormat1080p30",
                            "frameDuration": "1/30s",
                            "width": "1920",
                            "height": "1080"
                        }
                    },
                    "library": {
                        "event": {
                            "name": "Imported Event",
                            "clip": {
                                "name": os.path.basename(file_path),
                                "format": "r1",
                                "src": file_path
                            }
                        }
                    }
                }
            }
            
            # Save FCPXML
            with open(output_path, 'w') as f:
                json.dump(fcpxml, f, indent=4)
            
            return output_path
        except Exception as e:
            raise Exception(f"Error creating FCPXML: {str(e)}") 