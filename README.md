# Remarks Video Tool

A desktop application for downloading and managing video content, with support for transcription and FCPXML integration.

## Features

- **Web DL**: Download videos from YouTube and other supported sites
- **File Transcribe**: Transcribe video files to text
- **Transcribe from FCPXML**: Extract and transcribe clips from Final Cut Pro XML files
- **Settings**: Configure application preferences

## Installation

1. Make sure you have Python 3.11 or newer installed
2. Clone this repository
3. Create a virtual environment and install dependencies:

```bash
# Create virtual environment
python3.11 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### GUI Application

Run the application with a graphical interface:

```bash
python app.py
```

This will open the NiceGUI interface with tabs for different functionality.

### Command Line Interface

The application also provides a CLI for automation and scripting:

```bash
# Show help
python cli.py --help

# Download a video
python cli.py download url "https://www.youtube.com/watch?v=example"

# Transcribe a video file
python cli.py transcribe video path/to/video.mp4

# Show current configuration
python cli.py config show
```

## Project Structure

- `remarks/` - Main package
  - `downloader/` - Video downloading functionality
  - `transcriber/` - Video transcription functionality
  - `utils/` - Utility functions and configuration
  - `cli/` - Command-line interface
  - `api/` - API for programmatic access (future)
  - `app.py` - NiceGUI application

## Development

The project is designed with a modular architecture:

1. Backend functions are organized in separate modules
2. The CLI provides a command-line interface to these functions
3. The GUI provides a user-friendly interface to the same functions

This separation allows for easier testing and maintenance.

### Adding New Features

To add a new feature:

1. Implement the core functionality in the appropriate module
2. Add CLI commands to expose the functionality
3. Add GUI components to expose the functionality

## Requirements

- Python 3.11+
- NiceGUI
- yt-dlp
- ffmpeg-python
- OpenAI API key (for transcription features)

## License

[MIT License](LICENSE) 