"""
Run the MedAgentX web server.

Usage:
    python run_server.py
"""

import uvicorn
from medagentx.api.server import app

if __name__ == "__main__":
    print("=" * 60)
    print("🧠 MedAgentX (E-Doctor OS) - Starting Server")
    print("=" * 60)
    print("Server will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("UI: http://localhost:8000/")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
    )

