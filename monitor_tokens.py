#!/usr/bin/env python3
"""
Monitor Tokens Script
Theo dõi khi nào có token trong ví
"""

import os
import sys
import asyncio
import time
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from moderntensor_aptos.mt_core.async_client import ModernTensorCoreClient
    import httpx
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)


async def get_balance(client, address, name):
    """Get balance for an address"""
    try:
        balance_wei = await client.get_balance(address)
        balance_core = balance_wei / 10**18  # Convert wei to CORE
        return balance_core, balance_wei

    except Exception as e:
        return None, None


async def monitor_tokens():
    """Monitor token arrivals"""
    print("🔍 TOKEN MONITOR")
    print("=" * 60)

    # Load environment
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("❌ File .env không tồn tại!")
        return

    load_dotenv(env_file)

    validator_address = os.getenv("VALIDATOR_ADDRESS")
    miner_address = os.getenv("MINER_ADDRESS")
    node_url = os.getenv("CORE_NODE_URL", "https://rpc.test.btcs.network")

    print(f"🌐 Network: {node_url}")
    print(f"🎯 Validator: {validator_address}")
    print(f"🎯 Miner: {miner_address}")
    print()

    # Manual faucet instructions
    print("📋 MANUAL FAUCET REQUEST REQUIRED!")
    print("=" * 60)
    print("🌐 Mở browser và đi đến: https://faucet.test.btcs.network")
    print()
    print("📝 STEP BY STEP:")
    print("1. Copy validator address:")
    print(f"   {validator_address}")
    print("2. Paste vào form faucet và click 'Request Tokens'")
    print("3. Đợi 30-60 giây")
    print("4. Copy miner address:")
    print(f"   {miner_address}")
    print("5. Paste vào form faucet và click 'Request Tokens'")
    print("6. Đợi kết quả ở dưới...")
    print()
    print("🔗 DIRECT LINKS (có thể không work, prefer manual):")
    print(
        f"   Validator: https://faucet.test.btcs.network/?address={validator_address}"
    )
    print(f"   Miner: https://faucet.test.btcs.network/?address={miner_address}")
    print()
    print("⏰ Monitoring every 10 seconds...")
    print("=" * 60)

    client = ModernTensorCoreClient(node_url)

    total_attempts = 0
    while True:
        total_attempts += 1
        current_time = time.strftime("%H:%M:%S")

        print(f"\n🕐 [{current_time}] Check #{total_attempts}")

        # Check validator
        val_core, val_wei = await get_balance(client, validator_address, "Validator")
        if val_core is not None:
            if val_core > 0:
                print(f"🎉 Validator: {val_core:.4f} CORE ({val_wei:,} wei) ✅")
            else:
                print(f"⏳ Validator: 0.0000 CORE (waiting...)")
        else:
            print(f"❌ Validator: Error checking balance")

        # Check miner
        miner_core, miner_wei = await get_balance(client, miner_address, "Miner")
        if miner_core is not None:
            if miner_core > 0:
                print(f"🎉 Miner: {miner_core:.4f} CORE ({miner_wei:,} wei) ✅")
            else:
                print(f"⏳ Miner: 0.0000 CORE (waiting...)")
        else:
            print(f"❌ Miner: Error checking balance")

        # Check if we have tokens
        total_core = 0
        if val_core is not None and miner_core is not None:
            total_core = val_core + miner_core

        if total_core > 0:
            print(f"\n🎊 SUCCESS! Total: {total_core:.4f} CORE")
            print("✅ Tokens received! You can now:")
            print("   • Run validator scripts")
            print("   • Run miner scripts")
            print("   • Test subnet functionality")
            break

        # Instructions reminder every 5 attempts
        if total_attempts % 5 == 0:
            print(f"\n💡 [{total_attempts} attempts] Still waiting...")
            print("🔄 Make sure you've completed the manual faucet steps above!")
            print("🌐 Faucet: https://faucet.test.btcs.network")

        # Wait 10 seconds
        await asyncio.sleep(10)


async def main():
    """Main function"""
    try:
        await monitor_tokens()
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped by user")
        print("💡 You can resume monitoring anytime with: python monitor_tokens.py")
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
