#!/usr/bin/env python3
"""
Convenience script to run Validator 2
"""
import subprocess
import sys
from pathlib import Path

script_path = Path(__file__).parent / "scripts" / "run_validator_core_v2.py"

print("🛡️ Starting Validator 2 (Port 8002)...")
subprocess.run([sys.executable, str(script_path), "--validator", "2"], check=False)
