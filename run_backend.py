#!/usr/bin/env python3
"""
run_backend.py  –  Start the AeroAssist FastAPI server.
Usage: python run_backend.py
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
