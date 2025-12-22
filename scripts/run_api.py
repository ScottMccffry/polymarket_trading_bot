#!/usr/bin/env python3
"""Script to run the API server."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import uvicorn
from polybot.config import get_settings


def main():
    settings = get_settings()
    uvicorn.run(
        "polybot.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
