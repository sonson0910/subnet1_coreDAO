#!/usr/bin/env python3
"""
Initialize Accounts Script
Khởi tạo accounts để có thể nhận APT
"""

import os
import sys
import asyncio
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
    print("🔧 Đảm bảo đang trong môi trường conda aptos")
    sys.exit(1)

async def try_web_faucet(address):
    """Try to get tokens from web faucet using browser-like request"""
    print(f"🌐 Trying web faucet for {address[:10]}...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/json',
        'Origin': 'https://faucet.testnet.aptoslabs.com',
        'Referer': 'https://faucet.testnet.aptoslabs.com/',
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try different faucet endpoints
            endpoints = [
                "https://faucet.testnet.aptoslabs.com/mint",
                "https://faucet.testnet.aptoslabs.com/api/v1/mint", 
                "https://fullnode.testnet.aptoslabs.com/mint"
            ]
            
            for endpoint in endpoints:
                print(f"  Trying {endpoint}...")
                
                # Different payload formats
                payloads = [
                    {"address": address, "amount": 100000000},
                    {"address": address},
                    {"account": address, "amount": 100000000},
                    {"accounts": [address]},
                ]
                
                for payload in payloads:
                    try:
                        response = await client.post(endpoint, json=payload, headers=headers)
                        print(f"    Status: {response.status_code}")
                        
                        if response.status_code == 200:
                            print(f"    ✅ Success! Response: {response.text[:200]}")
                            return True
                        elif response.status_code != 404:
                            print(f"    Response: {response.text[:200]}")
                            
                    except Exception as e:
                        print(f"    Error: {e}")
                        continue
                        
        return False
        
    except Exception as e:
        print(f"❌ Web faucet error: {e}")
        return False

async def check_account_exists(rest_client, address):
    """Check if account exists and is initialized"""
    try:
        # Try to get account info
        account_info = await rest_client.account(address)
        print(f"✅ Account {address[:10]}... exists!")
        print(f"   Sequence: {account_info.get('sequence_number', 'unknown')}")
        return True
    except Exception as e:
        print(f"⚠️ Account {address[:10]}... not found: {e}")
        return False

async def initialize_accounts():
    """Initialize accounts để có thể nhận token"""
    print("🚀 KHỞI TẠO ACCOUNTS")
    print("="*50)
    
    # Load environment variables
    env_file = Path(__file__).parent / '.env'
    if not env_file.exists():
        print("❌ File .env không tồn tại!")
        return
        
    load_dotenv(env_file)
    
    validator_address = os.getenv('VALIDATOR_ADDRESS')
    miner_address = os.getenv('MINER_ADDRESS')
    node_url = os.getenv('APTOS_NODE_URL', 'https://fullnode.testnet.aptoslabs.com/v1')
    
    if not all([validator_address, miner_address]):
        print("❌ Missing wallet info in .env!")
        return
        
    print(f"🌐 Network: {node_url}")
    print(f"🎯 Validator: {validator_address}")
    print(f"🎯 Miner: {miner_address}")
    print()
    
    try:
        rest_client = RestClient(node_url)
        
        # Check if accounts exist
        val_exists = await check_account_exists(rest_client, validator_address)
        miner_exists = await check_account_exists(rest_client, miner_address)
        
        print()
        
        # Try web faucet for both accounts
        addresses_to_fund = []
        if not val_exists:
            addresses_to_fund.append(("Validator", validator_address))
        if not miner_exists:
            addresses_to_fund.append(("Miner", miner_address))
            
        if not addresses_to_fund:
            print("✅ Both accounts already exist!")
            return
            
        print(f"🎯 Need to initialize {len(addresses_to_fund)} accounts")
        print()
        
        # Try web faucet
        for name, address in addresses_to_fund:
            print(f"💰 Funding {name} account...")
            success = await try_web_faucet(address)
            
            if success:
                print(f"✅ {name} funded successfully!")
                
                # Wait a bit and check
                await asyncio.sleep(3)
                exists = await check_account_exists(rest_client, address)
                if exists:
                    print(f"🎉 {name} account now initialized!")
                else:
                    print(f"⚠️ {name} account still not showing up, might need more time")
            else:
                print(f"❌ Failed to fund {name} account via web faucet")
                
            print()
            
        # Final check
        print("="*50)
        print("🔍 FINAL STATUS CHECK")
        
        val_exists_final = await check_account_exists(rest_client, validator_address)
        miner_exists_final = await check_account_exists(rest_client, miner_address)
        
        if val_exists_final and miner_exists_final:
            print("🎉 Both accounts are now initialized!")
            print("💡 You can now receive tokens and run tests")
        else:
            print("⚠️ Some accounts still not initialized")
            print("💡 Try manual faucet request:")
            print(f"   🌐 Validator: https://faucet.testnet.aptoslabs.com/?address={validator_address}")
            print(f"   🌐 Miner: https://faucet.testnet.aptoslabs.com/?address={miner_address}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    """Main function"""
    try:
        await initialize_accounts()
    except KeyboardInterrupt:
        print("\n👋 Initialization interrupted by user")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 