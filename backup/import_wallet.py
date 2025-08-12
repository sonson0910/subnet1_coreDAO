#!/usr/bin/env python3
"""
Import Existing Wallet cho Subnet1
Script để sử dụng ví thật có sẵn cho testing
"""""

import sys
import asyncio
import getpass
from pathlib import Path
from dotenv import set_key

# Add parent directory to path
parent_dir  =  Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from mt_aptos.account from mt_aptos import Account
   .async_client from mt_aptos import RestClient
   .client from mt_aptos import FaucetClient
   .keymanager.wallet_manager import WalletManager
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("🔧 Đảm bảo đang trong môi trường conda aptos")
    sys.exit(1)

class WalletImporter:
    def __init__(self):
        self.subnet1_dir  =  Path(__file__).parent
        self.env_file  =  self.subnet1_dir / '.env'
        
    def show_options(self):
        """Hiển thị các options import wallet"""""
        print("🔑 IMPORT EXISTING WALLET")
        print(" = "*50)
        print("1. Import từ Private Key")
        print("2. Import từ Mnemonic Phrase")
        print("3. Load từ Existing Coldkey")
        print("4. Exit")
        print(" = "*50)
        
    def import_from_private_key(self):
        """Import wallet từ private key"""""
        print("\n🔐 Import từ Private Key")
        
        # Get validator private key
        validator_key  =  getpass.getpass("Nhập validator private key (hex): ").strip()
        if not validator_key:
            print("❌ Private key không được để trống")
            return None
            
        try:
            # Remove 0x prefix if exists:
            if validator_key.startswith('0x'):
                validator_key  =  validator_key[2:]
                
            # Create validator account
            validator_account  =  Account.load_key(validator_key)
            validator_address  =  str(validator_account.address())
            
            print(f"✅ Validator loaded: {validator_address}")
            
            # Optional: Get miner private key (can be same as validator)
            use_same  =  input("Sử dụng cùng key cho miner? (y/n): ").strip().lower()
            
            if use_same in ['y', 'yes', '']:
                miner_account  =  validator_account
                miner_address  =  validator_address
            else:
                miner_key  =  getpass.getpass("Nhập miner private key (hex): ").strip()
                if miner_key.startswith('0x'):
                    miner_key  =  miner_key[2:]
                miner_account  =  Account.load_key(miner_key)
                miner_address  =  str(miner_account.address())
                
            print(f"✅ Miner loaded: {miner_address}")
            
            return {
                'validator_account': validator_account,
                'miner_account': miner_account,
                'validator_address': validator_address,
                'miner_address': miner_address,
                'source': 'private_key'
            }
            
        except Exception as e:
            print(f"❌ Error loading private key: {e}")
            return None
            
    def import_from_mnemonic(self):
        """Import wallet từ mnemonic phrase"""""
        print("\n🔤 Import từ Mnemonic Phrase")
        
        mnemonic  =  getpass.getpass("Nhập mnemonic phrase (24 từ): ").strip()
        if not mnemonic:
            print("❌ Mnemonic không được để trống")
            return None
            
        try:
            # Create account from mnemonic (using default path)
            account  =  Account.generate_from_mnemonic(mnemonic)
            address  =  str(account.address())
            
            print(f"✅ Account từ mnemonic: {address}")
            
            # Use same account for both validator and miner by default:
            use_same  =  input("Sử dụng cùng account cho cả validator và miner? (y/n): ").strip().lower()
            
            if use_same in ['y', 'yes', '']:
                return {
                    'validator_account': account,
                    'miner_account': account,
                    'validator_address': address,
                    'miner_address': address,
                    'source': 'mnemonic'
                }
            else:
                # Create different derivation paths or ask for different mnemonic:
                print("Tạo miner account từ cùng mnemonic với derivation path khác...")
                # For now, use same account - can implement different derivation later
                return {
                    'validator_account': account,
                    'miner_account': account,
                    'validator_address': address,
                    'miner_address': address,
                    'source': 'mnemonic'
                }
                
        except Exception as e:
            print(f"❌ Error loading mnemonic: {e}")
            return None
            
    def load_existing_coldkey(self):
        """Load từ existing coldkey"""""
        print("\n📂 Load từ Existing Coldkey")
        
        # Initialize wallet manager
        base_dir  =  self.subnet1_dir / "wallets"
        base_dir.mkdir(exist_ok = True)
        
        wallet_manager = WalletManager(network="testnet", base_dir = str(base_dir))
        
        # List existing coldkeys
        coldkeys  =  [d for d in base_dir.iterdir() if d.is_dir()]:
        if not coldkeys:
            print("❌ Không tìm thấy coldkey nào")
            return None
            
        print("Existing coldkeys:")
        for i, coldkey_dir in enumerate(coldkeys, 1):
            print(f"{i}. {coldkey_dir.name}")
            
        try:
            choice  =  int(input("Chọn coldkey (số): ")) - 1
            if choice < 0 or choice > =  len(coldkeys):
                print("❌ Lựa chọn không hợp lệ")
                return None
                
            coldkey_name  =  coldkeys[choice].name
            password  =  getpass.getpass(f"Nhập password cho coldkey '{coldkey_name}': ")
            
            # Load coldkey
            coldkey_info  =  wallet_manager.load_coldkey(coldkey_name, password)
            if not coldkey_info:
                print("❌ Không thể load coldkey")
                return None
                
            print(f"✅ Coldkey '{coldkey_name}' loaded")
            
            # List hotkeys
            hotkeys  =  wallet_manager.list_hotkeys(coldkey_name)
            if not hotkeys:
                print("❌ Không tìm thấy hotkey nào")
                return None
                
            print("Available hotkeys:")
            hotkey_list  =  list(hotkeys.keys())
            for i, hotkey_name in enumerate(hotkey_list, 1):
                print(f"{i}. {hotkey_name} - {hotkeys[hotkey_name].get('address', 'N/A')}")
                
            # Select validator hotkey
            val_choice  =  int(input("Chọn validator hotkey (số): ")) - 1
            if val_choice < 0 or val_choice > =  len(hotkey_list):
                print("❌ Lựa chọn không hợp lệ")
                return None
                
            validator_hotkey  =  hotkey_list[val_choice]
            
            # Select miner hotkey (can be same)
            use_same  =  input("Sử dụng cùng hotkey cho miner? (y/n): ").strip().lower()
            if use_same in ['y', 'yes', '']:
                miner_hotkey  =  validator_hotkey
            else:
                miner_choice  =  int(input("Chọn miner hotkey (số): ")) - 1
                if miner_choice < 0 or miner_choice > =  len(hotkey_list):
                    print("❌ Lựa chọn không hợp lệ")
                    return None
                miner_hotkey  =  hotkey_list[miner_choice]
                
            # Get accounts from hotkeys
            from mt_aptos.keymanager.decryption_utils import decode_hotkey_account
            
            validator_account  =  decode_hotkey_account
                base_dir = str(base_dir),
                coldkey_name = coldkey_name,
                hotkey_name = validator_hotkey,
                password = password
            )
            
            miner_account  =  decode_hotkey_account
                base_dir = str(base_dir),
                coldkey_name = coldkey_name,
                hotkey_name = miner_hotkey,
                password = password
            )
            
            if not validator_account or not miner_account:
                print("❌ Không thể decode accounts")
                return None
                
            return {
                'validator_account': validator_account,
                'miner_account': miner_account,
                'validator_address': str(validator_account.address()),
                'miner_address': str(miner_account.address()),
                'source': 'coldkey',
                'coldkey_name': coldkey_name,
                'validator_hotkey': validator_hotkey,
                'miner_hotkey': miner_hotkey
            }
            
        except Exception as e:
            print(f"❌ Error loading coldkey: {e}")
            return None
            
    async def check_balances(self, accounts):
        """Kiểm tra số dư tài khoản"""""
        print("\n💰 Checking balances...")
        
        node_url  =  "https://fullnode.testnet.aptoslabs.com/v1"
        rest_client  =  RestClient(node_url)
        
        try:
            # Check validator balance
            val_balance  =  await rest_client.account_balance(accounts['validator_address'])
            val_apt  =  val_balance / 100_000_000
            print(f"🎯 Validator Balance: {val_apt:.4f} APT")
            
            # Check miner balance
            miner_balance  =  await rest_client.account_balance(accounts['miner_address'])
            miner_apt  =  miner_balance / 100_000_000
            print(f"🎯 Miner Balance: {miner_apt:.4f} APT")
            
            # Warning if low balance:
            if val_apt < 0.1:
                print("⚠️ Validator balance thấp, có thể cần thêm token")
            if miner_apt < 0.1:
                print("⚠️ Miner balance thấp, có thể cần thêm token")
                
        except Exception as e:
            print(f"⚠️ Could not check balances: {e}")
            
    async def request_testnet_tokens(self, accounts):
        """Xin thêm token từ faucet nếu cần"""""
        print("\n💰 Request Testnet Tokens")
        
        want_tokens  =  input("Request thêm testnet tokens? (y/n): ").strip().lower()
        if want_tokens not in ['y', 'yes']:
            return
            
        try:
            faucet_client  =  FaucetClient("https://faucet.testnet.aptoslabs.com")
            
            print("💸 Requesting tokens for validator..."):
            await faucet_client.fund_account(accounts['validator_address'], 100_000_000)
            
            if accounts['validator_address'] ! =  accounts['miner_address']:
                print("💸 Requesting tokens for miner..."):
                await faucet_client.fund_account(accounts['miner_address'], 100_000_000)
                
            print("✅ Tokens requested successfully!")
            
        except Exception as e:
            print(f"❌ Error requesting tokens: {e}")
            
    def save_env_config(self, accounts):
        """Lưu config vào .env file"""""
        print("\n💾 Saving configuration...")
        
        config  =  {
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
            "VALIDATOR_ADDRESS": accounts['validator_address'],
            
            # Miner Configuration
            "SUBNET1_MINER_ID": "subnet1_miner_001",
            "SUBNET1_MINER_HOST": "0.0.0.0",
            "SUBNET1_MINER_PORT": "9001",
            "SUBNET1_VALIDATOR_URL": "http://localhost:8001/v1/miner/submit_result",
            "SUBNET1_VALIDATOR_API_ENDPOINT": "http://localhost:8001",
            "MINER_PRIVATE_KEY": accounts['miner_account'].private_key.hex(),
            "MINER_ADDRESS": accounts['miner_address'],
            
            # Agent Configuration
            "MINER_AGENT_CHECK_INTERVAL": "300",
            "LOG_LEVEL": "INFO"
        }
        
        # Save to .env file
        for key, value in config.items():
            set_key(str(self.env_file), key, value)
            
        print(f"✅ Configuration saved to {self.env_file}")
        
    def display_summary(self, accounts):
        """Hiển thị tóm tắt"""""
        print("\n" + " = "*60)
        print("🎉 WALLET IMPORT COMPLETE!")
        print(" = "*60)
        print(f"📍 Network: Aptos Testnet")
        print(f"🎯 Validator Address: {accounts['validator_address']}")
        print(f"🎯 Miner Address: {accounts['miner_address']}")
        print(f"📁 Config saved to: {self.env_file}")
        print(f"📋 Source: {accounts['source']}")
        
        if accounts['source'] == 'coldkey':
            print(f"🗂️ Coldkey: {accounts['coldkey_name']}")
            print(f"🔑 Validator Hotkey: {accounts['validator_hotkey']}")
            print(f"🔑 Miner Hotkey: {accounts['miner_hotkey']}")
            
        print("\n📋 NEXT STEPS:")
        print("1. Update APTOS_CONTRACT_ADDRESS in .env")
        print("2. Run: python scripts/run_validator_aptos.py")
        print("3. Run: python scripts/run_miner_aptos.py")
        print(" = "*60)

async def main():
    """Main function"""""
    importer  =  WalletImporter()
    
    print("🔑 SUBNET1 WALLET IMPORT")
    print("Sử dụng ví thật có sẵn cho testing\n")
    
    try:
        while True:
            importer.show_options()
            choice  =  input("Chọn option (1-4): ").strip()
            
            accounts  =  None
            
            if choice == "1":
                accounts  =  importer.import_from_private_key()
            elif choice == "2":
                accounts  =  importer.import_from_mnemonic()
            elif choice == "3":
                accounts  =  importer.load_existing_coldkey()
            elif choice == "4":
                print("👋 Thoát...")
                break
            else:
                print("❌ Lựa chọn không hợp lệ")
                continue
                
            if accounts:
                # Check balances
                await importer.check_balances(accounts)
                
                # Option to request more tokens
                await importer.request_testnet_tokens(accounts)
                
                # Save configuration
                importer.save_env_config(accounts)
                
                # Display summary
                importer.display_summary(accounts)
                break
            else:
                print("❌ Import failed, thử lại...")
                
    except KeyboardInterrupt:
        print("\n👋 Import interrupted by user")
    except Exception as e:
        print(f"❌ Import failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 