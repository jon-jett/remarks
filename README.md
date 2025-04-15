# Video Processing Assistant

A macOS-native video processing tool with transcription and Final Cut Pro integration capabilities.

## Features

- Video downloading and processing
- AI-powered transcription (Deepgram + local whisper.cpp)
- Speaker identification
- Final Cut Pro XML export
- Drag-and-drop interface
- Optimized for Apple Silicon

## Project Structure

```
video-processing-assistant/
├── frontend/           # Electron application
│   ├── src/           # Source files
│   ├── public/        # Static assets
│   └── package.json   # Frontend dependencies
├── backend/           # Python FastAPI application
│   ├── app/          # Application code
│   ├── services/     # Core services
│   └── requirements.txt
└── README.md
```

## Setup Instructions

### Prerequisites

- Node.js 18+
- Python 3.9+
- FFmpeg
- whisper.cpp (for local transcription)

### Backend Setup

1. Create and activate virtual environment:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the backend server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

## Development

- Backend API runs on `http://localhost:8000`
- Frontend development server runs on `http://localhost:3000`
- API documentation available at `http://localhost:8000/docs`

## Building for Distribution

```bash
cd frontend
npm run build
```

This will create a macOS application bundle in the `dist` directory.

## License

Internal use only - Not for commercial distribution 