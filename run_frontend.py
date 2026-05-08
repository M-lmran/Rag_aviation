#!/usr/bin/env python3
"""
run_frontend.py  –  Launch the AeroAssist Streamlit UI.
Usage: python run_frontend.py
"""
import subprocess, sys

subprocess.run([
    sys.executable, "-m", "streamlit", "run",
    "frontend/app.py",
    "--server.port", "8501",
    "--server.headless", "false",
    "--server.maxUploadSize", "1024",
])
