@echo off
echo Starting EDOT Flask Service...

REM Set environment variables
set FLASK_APP=app.py
set FLASK_ENV=development
set PYTHONPATH=%cd%

REM Check if virtual environment exists
if exist .venv (
    echo Activating virtual environment...
    call .venv\Scripts\activate
) else (
    echo Virtual environment not found. Please create one with: python -m venv .venv
)

REM Install dependencies if needed
python -c "import flask, elastic_apm" 2>nul || (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Start the server
echo Starting Flask server on http://localhost:5001
python app.py

pause
