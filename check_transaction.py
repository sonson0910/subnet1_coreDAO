#!/usr/bin/env python3
"""
Kiểm tra Transaction Details
Script để check chi tiết của một transaction
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(parent_dir / 'moderntensor'))

try:
    from aptos_sdk.async_client import RestClient
    import httpx
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("🔧 Đảm bảo đang trong môi trường conda aptos")
    sys.exit(1)

async def check_transaction_details(tx_hash):
    """Check transaction details"""
    print(f"🔍 KIỂM TRA TRANSACTION: {tx_hash}")
    print("="*80)
    
    # Load environment variables
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
    
    validator_address = os.getenv('VALIDATOR_ADDRESS', '')
    miner_address = os.getenv('MINER_ADDRESS', '')
    node_url = os.getenv('APTOS_NODE_URL', 'https://fullnode.testnet.aptoslabs.com/v1')
    
    print(f"🌐 Network: {node_url}")
    print(f"🎯 Your Validator: {validator_address}")  
    print(f"🎯 Your Miner: {miner_address}")
    print()
    
    try:
        # Method 1: Use RestClient
        rest_client = RestClient(node_url)
        
        try:
            # Get transaction by hash
            tx_info = await rest_client.transaction_by_hash(tx_hash)
            
            print("✅ Transaction found!")
            print(f"📋 Type: {tx_info.get('type', 'unknown')}")
            print(f"🏷️ Version: {tx_info.get('version', 'unknown')}")
            print(f"📍 Hash: {tx_info.get('hash', 'unknown')}")
            print(f"🏛️ Sender: {tx_info.get('sender', 'unknown')}")
            print(f"✅ Success: {tx_info.get('success', False)}")
            print(f"⛽ Gas Used: {tx_info.get('gas_used', 'unknown')}")
            print(f"💰 Gas Price: {tx_info.get('gas_unit_price', 'unknown')}")
            
            # Check payload
            payload = tx_info.get('payload', {})
            if payload:
                print(f"\n📦 Payload Type: {payload.get('type', 'unknown')}")
                if payload.get('function'):
                    print(f"🔧 Function: {payload.get('function')}")
                if payload.get('arguments'):
                    print(f"📝 Arguments: {payload.get('arguments')}")
            
            # Check changes/events
            changes = tx_info.get('changes', [])
            if changes:
                print(f"\n🔄 Changes ({len(changes)}):")
                for i, change in enumerate(changes[:5]):  # Show first 5 changes
                    print(f"  {i+1}. Type: {change.get('type', 'unknown')}")
                    if change.get('address'):
                        print(f"     Address: {change.get('address')}")
                        
                        # Check if this involves our wallets
                        if change.get('address') == validator_address:
                            print(f"     🎯 *** THIS INVOLVES YOUR VALIDATOR WALLET! ***")
                        elif change.get('address') == miner_address:
                            print(f"     🎯 *** THIS INVOLVES YOUR MINER WALLET! ***")
                            
                    if change.get('data'):
                        data = change.get('data', {})
                        if data.get('type'):
                            print(f"     Data Type: {data.get('type')}")
                        if 'coin' in str(data).lower():
                            print(f"     💰 Coin related: {data}")
            
            # Check events
            events = tx_info.get('events', [])
            if events:
                print(f"\n🎉 Events ({len(events)}):")
                for i, event in enumerate(events[:3]):  # Show first 3 events
                    print(f"  {i+1}. Type: {event.get('type', 'unknown')}")
                    if event.get('data'):
                        print(f"     Data: {event.get('data')}")
            
            # Summary
            print(f"\n" + "="*80)
            sender = tx_info.get('sender', '')
            
            if sender == validator_address:
                print("🎯 *** TRANSACTION FROM YOUR VALIDATOR WALLET ***")
            elif sender == miner_address:
                print("🎯 *** TRANSACTION FROM YOUR MINER WALLET ***")
            elif any(change.get('address') in [validator_address, miner_address] for change in changes):
                print("🎯 *** TRANSACTION INVOLVES YOUR WALLETS ***")
            else:
                print("ℹ️  Transaction không liên quan đến wallets của bạn")
                print("💡 Có thể đây là transaction của user khác")
            
        except Exception as e:
            print(f"❌ Lỗi khi get transaction từ RestClient: {e}")
            
            # Method 2: Direct HTTP call
            print("\n🔄 Thử method backup...")
            url = f"{node_url}/transactions/by_hash/{tx_hash}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    tx_data = response.json()
                    print("✅ Got transaction via HTTP!")
                    print(json.dumps(tx_data, indent=2)[:1000] + "...")
                else:
                    print(f"❌ HTTP Error: {response.status_code}")
                    print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")

async def main():
    """Main function"""
    if len(sys.argv) > 1:
        tx_hash = sys.argv[1]
    else:
        tx_hash = "0x3ef8d61a31c267484b8eeb7abde3261a4a70761983bcbd717e1723d4c8eae353"
        print(f"⚠️ No transaction hash provided. Using default: {tx_hash}")

    try:
        await check_transaction_details(tx_hash)
    except KeyboardInterrupt:
        print("\n👋 Check interrupted by user")
    except Exception as e:
        print(f"❌ Check failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 