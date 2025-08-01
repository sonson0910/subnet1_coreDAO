#!/usr/bin/env python3
"""
Test script to debug port handling in validator
"""
import os
import sys
from pathlib import Path

# Set VALIDATOR_ID for testing
os.environ["VALIDATOR_ID"] = "2"

# Load environment
project_root = Path(__file__).parent
env_path = project_root / ".env"

print("🔍 DEBUGGING PORT HANDLING")
print("=" * 50)

# Check environment variables
print(f"📋 Environment Variables:")
print(f"   VALIDATOR_ID: {os.getenv('VALIDATOR_ID')}")
print(f"   VALIDATOR_2_PORT: {os.getenv('VALIDATOR_2_PORT')}")
print(f"   VALIDATOR_2_API_ENDPOINT: {os.getenv('VALIDATOR_2_API_ENDPOINT')}")
print(f"   VALIDATOR_2_ID: {os.getenv('VALIDATOR_2_ID')}")

# Load dotenv
from dotenv import load_dotenv

if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env from {env_path}")
else:
    print(f"❌ .env file not found at {env_path}")

print(f"\n📋 After Loading .env:")
print(f"   VALIDATOR_ID: {os.getenv('VALIDATOR_ID')}")
print(f"   VALIDATOR_2_PORT: {os.getenv('VALIDATOR_2_PORT')}")
print(f"   VALIDATOR_2_API_ENDPOINT: {os.getenv('VALIDATOR_2_API_ENDPOINT')}")
print(f"   VALIDATOR_2_ID: {os.getenv('VALIDATOR_2_ID')}")

# Test the logic from run_validator_core_v2.py
validator_id = os.getenv("VALIDATOR_ID", "1")
print(f"\n🎯 Validator Logic Test:")
print(f"   validator_id: {validator_id}")

if validator_id == "2":
    validator_port = int(os.getenv("VALIDATOR_2_PORT", "8002"))
    validator_api_endpoint = os.getenv("VALIDATOR_2_API_ENDPOINT")
    print(f"   Using Validator 2 settings:")
    print(f"   - validator_port: {validator_port}")
    print(f"   - validator_api_endpoint: {validator_api_endpoint}")
else:
    validator_port = int(os.getenv("VALIDATOR_1_PORT", "8001"))
    validator_api_endpoint = os.getenv("VALIDATOR_1_API_ENDPOINT")
    print(f"   Using Validator 1 settings:")
    print(f"   - validator_port: {validator_port}")
    print(f"   - validator_api_endpoint: {validator_api_endpoint}")

print(f"\n✅ Final Decision:")
print(f"   Port to use: {validator_port}")
print(f"   Expected: 8002 for Validator 2")
print(f"   Match: {'✅ YES' if validator_port == 8002 else '❌ NO'}")
