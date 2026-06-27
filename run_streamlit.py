"""
Script to run MedAgentX Streamlit UI.

Usage:
    python run_streamlit.py
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    # Get the path to the Streamlit app
    streamlit_app_path = os.path.join(
        os.path.dirname(__file__),
        "medagentx",
        "ui",
        "streamlit_app.py"
    )
    
    if not os.path.exists(streamlit_app_path):
        print(f"Error: Streamlit app not found at {streamlit_app_path}")
        sys.exit(1)
    
    # Run Streamlit
    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        streamlit_app_path,
        "--server.port=8501",
        "--server.address=localhost",
    ])

