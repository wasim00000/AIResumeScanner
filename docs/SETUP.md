# Setup Guide

This guide helps you set up and run the AI Resume Scanner on Windows using PowerShell.

## Prerequisites

- Python 3.10+ installed and on PATH
- PowerShell

## 1. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

## 2. Install dependencies

```powershell
pip install -r requirements.txt
```

## 3. Launch the app

```powershell
.\.venv\Scripts\python -m streamlit run .\app.py --server.port 8502
```

Open [http://localhost:8502](http://localhost:8502) in your browser.

## Tips

- If the default port is busy, change `--server.port` to another value (e.g., 8503) or configure `.streamlit/config.toml`.
- Always run Streamlit using the venv python to ensure the correct packages are used.

## Docker (alternative)

Build and run with Docker:

```powershell
docker build -t ai-resume-scanner .
docker run --rm -it -p 8502:8502 ai-resume-scanner
```

Or with docker-compose:

```powershell
docker compose up --build
```

Then open [http://localhost:8502](http://localhost:8502)
