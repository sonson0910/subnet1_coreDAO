#!/usr/bin/env python3
"""
Convenience script to run Validator 1
"""""
import subprocess
import sys
from pathlib import Path

script_path  =  Path(__file__).parent / "scripts" / "run_validator_core_v2.py"

print("🛡️ Starting Validator 1 (Port 8001)...")
subprocess.run([sys.executable, str(script_path), "--validator", "1"], check = False)
