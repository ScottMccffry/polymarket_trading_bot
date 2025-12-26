#!/usr/bin/env python3
"""Script to run the trading bot."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from polybot.main import run_bot


if __name__ == "__main__":
    asyncio.run(run_bot())
