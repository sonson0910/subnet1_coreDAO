#!/usr/bin/env python3
"""
Tạo Ví Mới cho Subnet1
Script đơn giản để tạo validator và miner wallets
"""""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import set_key

# Add parent directory to path
parent_dir  =  Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from mt_aptos.account from mt_aptos import Account
   .async_client from mt_aptos import RestClient
   .client import FaucetClient
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("🔧 Đảm bảo đang trong môi trường conda aptos")
    sys.exit(1)

async def create_new_wallets():
    """Tạo ví mới cho validator và miner"""""
    print("🚀 TẠO VÍ MỚI CHO SUBNET1")
    print(" = "*50)
    
    try:
        # Tạo validator account
        print("🔑 Generating validator account...")
        validator_account  =  Account.generate()
        validator_address  =  str(validator_account.address())
        validator_private_key  =  str(validator_account.private_key)
        
        print(f"✅ Validator Address: {validator_address}")
        print(f"🔐 Validator Private Key: {validator_private_key}")
        
        # Tạo miner account  
        print("\n🔑 Generating miner account...")
        miner_account  =  Account.generate()
        miner_address  =  str(miner_account.address())
        miner_private_key  =  str(miner_account.private_key)
        
        print(f"✅ Miner Address: {miner_address}")
        print(f"🔐 Miner Private Key: {miner_private_key}")
        
        # Lưu vào file backup
        subnet1_dir  =  Path(__file__).parent
        backup_file  =  subnet1_dir / "wallet_backup.txt"
        
        with open(backup_file, 'w') as f:
            f.write("SUBNET1 WALLET BACKUP\n")
            f.write(" = "*50 + "\n")
            f.write(f"Generated: {os.popen('date').read().strip()}\n\n")
            
            f.write("VALIDATOR WALLET:\n")
            f.write(f"Address: {validator_address}\n")
            f.write(f"Private Key: {validator_private_key}\n\n")
            
            f.write("MINER WALLET:\n")
            f.write(f"Address: {miner_address}\n")
            f.write(f"Private Key: {miner_private_key}\n\n")
            
            f.write("⚠️ KEEP THESE KEYS SAFE! ⚠️\n")
            f.write("⚠️ NEVER SHARE OR COMMIT TO GIT! ⚠️\n")
        
        print(f"\n💾 Keys backed up to: {backup_file}")
        
        # Kiểm tra balance hiện tại
        print("\n💰 Checking current balances...")
        node_url  =  "https://fullnode.testnet.aptoslabs.com/v1"
        rest_client  =  RestClient(node_url)
        
        try:
            val_balance  =  await rest_client.account_balance(validator_address)
            val_apt  =  val_balance / 100_000_000
            print(f"🎯 Validator Balance: {val_apt:.4f} APT")
        except:
            print("🎯 Validator Balance: 0.0000 APT (new account)")
            
        try:
            miner_balance  =  await rest_client.account_balance(miner_address)
            miner_apt  =  miner_balance / 100_000_000
            print(f"🎯 Miner Balance: {miner_apt:.4f} APT")
        except:
            print("🎯 Miner Balance: 0.0000 APT (new account)")
        
        # Xin token từ faucet
        request_tokens  =  input("\n💰 Request testnet tokens from faucet? (y/n): ").strip().lower()
        if request_tokens in ['y', 'yes', '']:
            try:
                print("💸 Requesting tokens from testnet faucet...")
                faucet_client  =  FaucetClient("https://faucet.testnet.aptoslabs.com")
                
                print("  💸 Funding validator account...")
                await faucet_client.fund_account(validator_address, 100_000_000)  # 1 APT
                
                print("  💸 Funding miner account...")
                await faucet_client.fund_account(miner_address, 100_000_000)  # 1 APT
                
                print("✅ Tokens requested successfully!")
                
                # Check balance again
                print("\n💰 Updated balances:")
                try:
                    val_balance  =  await rest_client.account_balance(validator_address)
                    val_apt  =  val_balance / 100_000_000
                    print(f"🎯 Validator Balance: {val_apt:.4f} APT")
                    
                    miner_balance  =  await rest_client.account_balance(miner_address)
                    miner_apt  =  miner_balance / 100_000_000
                    print(f"🎯 Miner Balance: {miner_apt:.4f} APT")
                except Exception as e:
                    print(f"⚠️ Could not check updated balances: {e}")
                    
            except Exception as e:
                print(f"❌ Error requesting tokens: {e}")
                print("💡 You can request tokens manually later from:")
                print("   https://faucet.testnet.aptoslabs.com")
        
        # Lưu config vào .env
        env_file  =  subnet1_dir / '.env'
        print(f"\n💾 Saving configuration to {env_file}")
        
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
            "APTOS_PRIVATE_KEY": validator_private_key,
            "VALIDATOR_ADDRESS": validator_address,
            
            # Miner Configuration
            "SUBNET1_MINER_ID": "subnet1_miner_001",
            "SUBNET1_MINER_HOST": "0.0.0.0",
            "SUBNET1_MINER_PORT": "9001",
            "SUBNET1_VALIDATOR_URL": "http://localhost:8001/v1/miner/submit_result",
            "SUBNET1_VALIDATOR_API_ENDPOINT": "http://localhost:8001",
            "MINER_PRIVATE_KEY": miner_private_key,
            "MINER_ADDRESS": miner_address,
            
            # Agent Configuration
            "MINER_AGENT_CHECK_INTERVAL": "300",
            "LOG_LEVEL": "INFO"
        }
        
        # Save to .env file
        for key, value in config.items():
            set_key(str(env_file), key, value)
            
        print("✅ Configuration saved!")
        
        # Display summary
        print("\n" + " = "*60)
        print("🎉 WALLET CREATION COMPLETE!")
        print(" = "*60)
        print(f"📍 Network: Aptos Testnet")
        print(f"🎯 Validator Address: {validator_address}")
        print(f"🎯 Miner Address: {miner_address}")
        print(f"📁 Config saved to: {env_file}")
        print(f"🔐 Keys backed up to: {backup_file}")
        
        print("\n📋 NEXT STEPS:")
        print("1. Update APTOS_CONTRACT_ADDRESS in .env với real contract")
        print("2. Run validator: python scripts/run_validator_aptos.py")
        print("3. Run miner: python scripts/run_miner_aptos.py")
        print("4. Check setup: python check_setup.py")
        print(" = "*60)
        
        print("\n⚠️  SECURITY REMINDERS:")
        print("- Backup file chứa private keys, giữ an toàn!")
        print("- Không commit .env hoặc backup file vào git")
        print("- Đây là testnet, không dùng cho production")
        
    except Exception as e:
        print(f"❌ Error creating wallets: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function"""""
    try:
        await create_new_wallets()
    except KeyboardInterrupt:
        print("\n👋 Wallet creation interrupted by user")
    except Exception as e:
        print(f"❌ Wallet creation failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 