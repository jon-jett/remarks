# Remarks

A modern application with a Python backend and Swift UI frontend.

## Project Structure

```
remarks/
├── backend/         # Python backend
│   ├── app/        # Main application code
│   ├── tests/      # Backend tests
│   └── requirements.txt
├── frontend/       # Swift UI frontend
│   └── Remarks/    # Main iOS app
└── README.md
```

## Setup Instructions

### Backend Setup
1. Create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Unix/macOS
   # or
   .\venv\Scripts\activate  # On Windows
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the development server:
   ```bash
   python app/main.py
   ```

### Frontend Setup
1. Open the Xcode project in the `frontend/Remarks` directory
2. Build and run the project in Xcode

## Development

- Backend runs on `http://localhost:8000` by default
- Frontend connects to the backend API 