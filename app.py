"""Streamlit entrypoint for the compact AI Resume Scanner app."""

from pathlib import Path
import runpy
import sys


APP_DIR = Path(__file__).resolve().parent / "AIResumeScanner"
sys.path.insert(0, str(APP_DIR))

runpy.run_path(str(APP_DIR / "app.py"), run_name="__main__")
