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
    from mt_aptos.async_client import RestClient
    import httpx
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

async def get_balance(rest_client, address, name):
    """Get balance for an address"""
    try:
        resources = await rest_client.account_resources(address)
        
        for resource in resources:
            if resource.get("type") == "0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>":
                coin_value = resource.get("data", {}).get("coin", {}).get("value", "0")
                balance_octas = int(coin_value)
                balance_apt = balance_octas / 100_000_000
                return balance_apt, balance_octas
        
        return 0.0, 0
        
    except Exception as e:
        return None, None

async def monitor_tokens():
    """Monitor token arrivals"""
    print("🔍 TOKEN MONITOR")
    print("="*60)
    
    # Load environment
    env_file = Path(__file__).parent / '.env'
    if not env_file.exists():
        print("❌ File .env không tồn tại!")
        return
        
    load_dotenv(env_file)
    
    validator_address = os.getenv('VALIDATOR_ADDRESS')
    miner_address = os.getenv('MINER_ADDRESS')
    node_url = os.getenv('APTOS_NODE_URL', 'https://fullnode.testnet.aptoslabs.com/v1')
    
    print(f"🌐 Network: {node_url}")
    print(f"🎯 Validator: {validator_address}")
    print(f"🎯 Miner: {miner_address}")
    print()
    
    # Manual faucet instructions
    print("📋 MANUAL FAUCET REQUEST REQUIRED!")
    print("="*60)
    print("🌐 Mở browser và đi đến: https://faucet.testnet.aptoslabs.com")
    print()
    print("📝 STEP BY STEP:")
    print("1. Copy validator address:")
    print(f"   {validator_address}")
    print("2. Paste vào form faucet và click 'Fund Account'")
    print("3. Đợi 30-60 giây")
    print("4. Copy miner address:")
    print(f"   {miner_address}")  
    print("5. Paste vào form faucet và click 'Fund Account'")
    print("6. Đợi kết quả ở dưới...")
    print()
    print("🔗 DIRECT LINKS (có thể không work, prefer manual):")
    print(f"   Validator: https://faucet.testnet.aptoslabs.com/?address={validator_address}")
    print(f"   Miner: https://faucet.testnet.aptoslabs.com/?address={miner_address}")
    print()
    print("⏰ Monitoring every 10 seconds...")
    print("="*60)
    
    rest_client = RestClient(node_url)
    
    total_attempts = 0
    while True:
        total_attempts += 1
        current_time = time.strftime('%H:%M:%S')
        
        print(f"\n🕐 [{current_time}] Check #{total_attempts}")
        
        # Check validator
        val_apt, val_octas = await get_balance(rest_client, validator_address, "Validator")
        if val_apt is not None:
            if val_apt > 0:
                print(f"🎉 Validator: {val_apt:.4f} APT ({val_octas:,} octas) ✅")
            else:
                print(f"⏳ Validator: 0.0000 APT (waiting...)")
        else:
            print(f"❌ Validator: Error checking balance")
            
        # Check miner  
        miner_apt, miner_octas = await get_balance(rest_client, miner_address, "Miner")
        if miner_apt is not None:
            if miner_apt > 0:
                print(f"🎉 Miner: {miner_apt:.4f} APT ({miner_octas:,} octas) ✅")
            else:
                print(f"⏳ Miner: 0.0000 APT (waiting...)")
        else:
            print(f"❌ Miner: Error checking balance")
            
        # Check if we have tokens
        total_apt = 0
        if val_apt is not None and miner_apt is not None:
            total_apt = val_apt + miner_apt
            
        if total_apt > 0:
            print(f"\n🎊 SUCCESS! Total: {total_apt:.4f} APT")
            print("✅ Tokens received! You can now:")
            print("   • Run validator scripts")  
            print("   • Run miner scripts")
            print("   • Test subnet functionality")
            break
            
        # Instructions reminder every 5 attempts
        if total_attempts % 5 == 0:
            print(f"\n💡 [{total_attempts} attempts] Still waiting...")
            print("🔄 Make sure you've completed the manual faucet steps above!")
            print("🌐 Faucet: https://faucet.testnet.aptoslabs.com")
            
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