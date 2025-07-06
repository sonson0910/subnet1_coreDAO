#!/usr/bin/env python3
"""
Kiểm tra Balance của Wallet
Script nhanh để check số dư token trong ví
"""

import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(parent_dir / 'moderntensor'))

try:
    from aptos_sdk.async_client import RestClient
    from aptos_sdk.account_address import AccountAddress
    import httpx
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("🔧 Đảm bảo đang trong môi trường conda aptos")
    sys.exit(1)

async def get_account_balance(rest_client, address: str, node_url):
    """Get balance using direct API call"""
    try:
        # Use the simple account_balance function from the SDK
        account_address = AccountAddress.from_hex(address)
        balance = await rest_client.account_balance(account_address)
        return balance
    except Exception as e:
        print(f"⚠️ Lỗi khi check balance: {e}")
        # The account might not exist yet, which is a valid case (balance 0)
        if "Resource not found" in str(e):
             return 0
        return None

async def check_wallet_balances():
    """Kiểm tra balance của các wallet"""
    print("💰 KIỂM TRA BALANCE WALLET")
    print("="*50)
    
    # Load environment variables
    env_file = Path(__file__).parent / '.env'
    if not env_file.exists():
        print("❌ File .env không tồn tại!")
        return
        
    load_dotenv(env_file)
    
    # Get addresses from .env
    validator_address = os.getenv('VALIDATOR_ADDRESS')
    miner_address = os.getenv('MINER_ADDRESS')
    node_url = os.getenv('APTOS_NODE_URL', 'https://fullnode.testnet.aptoslabs.com/v1')
    
    if not validator_address or not miner_address:
        print("❌ Không tìm thấy addresses trong .env file")
        return
        
    print(f"🌐 Network: {node_url}")
    print(f"🎯 Validator Address: {validator_address}")
    print(f"🎯 Miner Address: {miner_address}")
    print()
    
    try:
        # Connect to Aptos network
        rest_client = RestClient(node_url)
        
        # Check validator balance
        print("💰 Checking validator balance...")
        val_balance = await get_account_balance(rest_client, validator_address, node_url)
        
        if val_balance is not None:
            val_apt = val_balance / 100_000_000  # Convert octas to APT
            print(f"✅ Validator Balance: {val_apt:.4f} APT ({val_balance:,} octas)")
            
            if val_apt > 0:
                print("🎉 Validator đã có token!")
            else:
                print("⚠️ Validator chưa có token (account chưa được khởi tạo)")
        else:
            print("❌ Không thể check validator balance")
            val_apt = 0
            
        # Check miner balance
        print("\n💰 Checking miner balance...")
        miner_balance = await get_account_balance(rest_client, miner_address, node_url)
        
        if miner_balance is not None:
            miner_apt = miner_balance / 100_000_000  # Convert octas to APT
            print(f"✅ Miner Balance: {miner_apt:.4f} APT ({miner_balance:,} octas)")
            
            if miner_apt > 0:
                print("🎉 Miner đã có token!")
            else:
                print("⚠️ Miner chưa có token (account chưa được khởi tạo)")
        else:
            print("❌ Không thể check miner balance")
            miner_apt = 0
            
        # Summary
        print("\n" + "="*50)
        total_apt = val_apt + miner_apt
        print(f"💰 Tổng balance: {total_apt:.4f} APT")
            
        if total_apt > 0:
            print("✅ Ví đã có token, có thể bắt đầu test!")
            print("💡 Recommended: Keep at least 0.1 APT cho transaction fees")
        else:
            # Determine faucet URL based on network
            if 'devnet' in node_url:
                faucet_url = "https://faucet.devnet.aptoslabs.com"
                network_name = "DEVNET"
            else:
                faucet_url = "https://faucet.testnet.aptoslabs.com"
                network_name = "TESTNET"
                
            print(f"⚠️ Ví chưa có token, cần request từ {network_name} faucet:")
            print(f"   🌐 {faucet_url}")
            print("   📋 Copy paste addresses vào form faucet")
            print("   💡 Mỗi address có thể xin 1 APT mỗi giờ")
            
        # Show direct faucet links
        print("\n🔗 Direct faucet links:")
        if 'devnet' in node_url:
            print(f"   Validator: https://faucet.devnet.aptoslabs.com/?address={validator_address}")
            print(f"   Miner: https://faucet.devnet.aptoslabs.com/?address={miner_address}")
        else:
            print(f"   Validator: https://faucet.testnet.aptoslabs.com/?address={validator_address}")
            print(f"   Miner: https://faucet.testnet.aptoslabs.com/?address={miner_address}")
            
    except Exception as e:
        print(f"❌ Lỗi kết nối network: {e}")
        print("💡 Kiểm tra internet connection và node URL")

async def main():
    """Main function"""
    try:
        await check_wallet_balances()
    except KeyboardInterrupt:
        print("\n👋 Check interrupted by user")
    except Exception as e:
        print(f"❌ Check failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 