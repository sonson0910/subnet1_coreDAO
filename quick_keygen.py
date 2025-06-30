#!/usr/bin/env python3
"""
Quick Key Generator cho Subnet1
Script đơn giản để tạo key và xin token nhanh chóng
"""

import os
import sys
import asyncio
from pathlib import Path
from rich.prompt import Prompt, Confirm

# --- Add project root to sys.path ---
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'moderntensor'))

# --- Import required classes ---
try:
    from mt_aptos.account import Account
    from mt_aptos.config.settings import Settings
    from aptos_sdk.async_client import FaucetClient, RestClient
    from dotenv import set_key
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("🔧 Hãy chạy: pip install -e . từ thư mục gốc")
    sys.exit(1)

class QuickSetup:
    def __init__(self):
        self.subnet1_dir = Path(__file__).parent
        self.env_file = self.subnet1_dir / '.env'
        
    def generate_accounts(self):
        """Tạo validator và miner accounts"""
        print("🔑 Generating Aptos accounts...")
        
        # Tạo accounts
        validator_account = Account.generate()
        miner_account = Account.generate()
        
        validator_address = str(validator_account.address())
        miner_address = str(miner_account.address())
        
        print(f"✅ Validator Account: {validator_address}")
        print(f"✅ Miner Account: {miner_address}")
        
        return {
            'validator_account': validator_account,
            'miner_account': miner_account,
            'validator_address': validator_address,
            'miner_address': miner_address
        }
    
    async def request_testnet_tokens(self, accounts):
        """Xin token từ testnet faucet"""
        print("\n💰 Requesting testnet tokens...")
        
        node_url = "https://fullnode.testnet.aptoslabs.com/v1"
        faucet_url = "https://faucet.testnet.aptoslabs.com"
        
        rest_client = RestClient(node_url)
        faucet_client = FaucetClient(faucet_url, rest_client)
        
        try:
            # Xin token cho validator
            print("💸 Requesting tokens for validator...")
            await faucet_client.fund_account(accounts['validator_address'], 100_000_000)  # 1 APT
            
            # Xin token cho miner
            print("💸 Requesting tokens for miner...")
            await faucet_client.fund_account(accounts['miner_address'], 100_000_000)  # 1 APT
            
            print("✅ Tokens requested successfully!")
            
            # Kiểm tra balance
            await self.check_balances(accounts)
            
        except Exception as e:
            print(f"❌ Error requesting tokens: {e}")
        finally:
            await rest_client.close()
            
    async def check_balances(self, accounts):
        """Kiểm tra số dư tài khoản"""
        print("\n💰 Checking balances...")
        
        node_url = "https://fullnode.testnet.aptoslabs.com/v1"
        rest_client = RestClient(node_url)
        
        try:
            # Kiểm tra validator balance
            val_balance = await rest_client.account_balance(accounts['validator_address'])
            val_apt = val_balance / 100_000_000
            print(f"🎯 Validator Balance: {val_apt:.4f} APT")
            
            # Kiểm tra miner balance
            miner_balance = await rest_client.account_balance(accounts['miner_address'])
            miner_apt = miner_balance / 100_000_000
            print(f"🎯 Miner Balance: {miner_apt:.4f} APT")
            
        except Exception as e:
            print(f"⚠️ Could not check balances: {e}")
        finally:
            await rest_client.close()
            
    def save_env_config(self, accounts):
        """Lưu config vào file .env"""
        print(f"\n💾 Saving configuration to {self.env_file}")
        
        config = {
            # Network Configuration
            "APTOS_NODE_URL": "https://fullnode.testnet.aptoslabs.com/v1",
            "APTOS_CHAIN_ID": "2",
            "APTOS_CONTRACT_ADDRESS": "0x1234567890abcdef1234567890abcdef12345678",  # Placeholder
            
            # Validator Configuration
            "SUBNET1_VALIDATOR_ID": "subnet1_validator_001",
            "SUBNET1_VALIDATOR_HOST": "0.0.0.0",
            "SUBNET1_VALIDATOR_PORT": "8001",
            "VALIDATOR_API_ENDPOINT": "http://localhost:8001",
                         "APTOS_PRIVATE_KEY": accounts['validator_account'].private_key.hex(),
             
             # Miner Configuration
             "SUBNET1_MINER_ID": "subnet1_miner_001", 
             "SUBNET1_MINER_HOST": "0.0.0.0",
             "SUBNET1_MINER_PORT": "9001",
             "SUBNET1_VALIDATOR_URL": "http://localhost:8001/v1/miner/submit_result",
             "SUBNET1_VALIDATOR_API_ENDPOINT": "http://localhost:8001",
             
             # Additional keys for reference
             "MINER_PRIVATE_KEY": accounts['miner_account'].private_key.hex(),
            "VALIDATOR_ADDRESS": accounts['validator_address'],
            "MINER_ADDRESS": accounts['miner_address'],
            
            # Agent Configuration
            "MINER_AGENT_CHECK_INTERVAL": "300",
            "LOG_LEVEL": "INFO"
        }
        
        # Lưu từng key vào .env file
        for key, value in config.items():
            set_key(str(self.env_file), key, value)
            
        print("✅ Configuration saved!")
        
    def display_summary(self, accounts):
        """Hiển thị tóm tắt"""
        print("\n" + "="*60)
        print("🎉 SUBNET1 SETUP COMPLETE!")
        print("="*60)
        print(f"📍 Network: Aptos Testnet")
        print(f"🎯 Validator Address: {accounts['validator_address']}")
        print(f"🎯 Miner Address: {accounts['miner_address']}")
        print(f"📁 Config saved to: {self.env_file}")
        print("\n📋 NEXT STEPS:")
        print("1. Update APTOS_CONTRACT_ADDRESS in .env")
        print("2. Run: python scripts/run_validator_aptos.py")
        print("3. Run: python scripts/run_miner_aptos.py")
        print("="*60)
        
        # Save keys to text file for backup
        keys_file = self.subnet1_dir / "keys_backup.txt"
        with open(keys_file, 'w') as f:
            f.write(f"SUBNET1 KEYS BACKUP\n")
            f.write(f"Generated: {os.popen('date').read().strip()}\n\n")
            f.write(f"Validator Address: {accounts['validator_address']}\n")
            f.write(f"Validator Private Key: {accounts['validator_account'].private_key.hex()}\n\n")
            f.write(f"Miner Address: {accounts['miner_address']}\n")
            f.write(f"Miner Private Key: {accounts['miner_account'].private_key.hex()}\n\n")
            f.write("⚠️ KEEP THESE KEYS SAFE! ⚠️\n")
            
        print(f"🔐 Keys backup saved to: {keys_file}")

async def main():
    """Main function"""
    print("🚀 SUBNET1 QUICK SETUP")
    print("Tạo key và xin token cho testing nhanh chóng\n")
    
    setup = QuickSetup()
    
    try:
        # Tạo accounts
        accounts = setup.generate_accounts()
        
        # Xin token
        want_tokens = input("\n💰 Request testnet tokens? (y/n): ").strip().lower()
        if want_tokens in ['y', 'yes', '']:
            await setup.request_testnet_tokens(accounts)
        
        # Lưu config
        setup.save_env_config(accounts)
        
        # Hiển thị tóm tắt
        setup.display_summary(accounts)
        
    except KeyboardInterrupt:
        print("\n👋 Setup interrupted by user")
    except Exception as e:
        print(f"❌ Setup failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 