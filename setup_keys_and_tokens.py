#!/usr/bin/env python3
"""
Setup Script cho Subnet1 - Tạo Key và Xin Token để Test
"""

import os
import sys
import logging
import asyncio
import getpass
from pathlib import Path
from dotenv import load_dotenv, set_key
from rich.console import Console
from rich.logging import RichHandler
from rich.prompt import Prompt, Confirm
from rich.table import Table
from typing import Optional, Dict, Any

# Add project root to sys.path
project_root = Path(__file__).parent
parent_root = project_root.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(parent_root))

try:
    from mt_aptos.keymanager.wallet_manager import WalletManager
    from mt_aptos.account import Account
    from mt_aptos.async_client import RestClient
    from mt_aptos.client import FaucetClient
    from mt_aptos.config.settings import settings
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("🔧 Run: pip install -e . from the project root")
    sys.exit(1)

# Setup logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, show_time=True, show_path=False)]
)
logger = logging.getLogger(__name__)

class Subnet1Setup:
    def __init__(self):
        self.project_root = project_root
        self.env_path = self.project_root / '.env'
        self.console = Console()
        self.wallet_manager = None
        
    def load_env(self):
        """Load existing .env file if exists"""
        if self.env_path.exists():
            load_dotenv(self.env_path)
            logger.info(f"📄 Loaded existing .env from {self.env_path}")
        else:
            logger.info(f"📄 No existing .env found, will create new one")
            
    def setup_network_config(self):
        """Setup Aptos network configuration"""
        self.console.print("\n[bold blue]🌐 APTOS NETWORK CONFIGURATION[/bold blue]")
        
        networks = {
            "1": {
                "name": "Testnet",
                "node_url": "https://fullnode.testnet.aptoslabs.com/v1",
                "faucet_url": "https://faucet.testnet.aptoslabs.com",
                "chain_id": 2
            },
            "2": {
                "name": "Devnet", 
                "node_url": "https://fullnode.devnet.aptoslabs.com/v1",
                "faucet_url": "https://faucet.devnet.aptoslabs.com",
                "chain_id": 42
            },
            "3": {
                "name": "Mainnet",
                "node_url": "https://fullnode.mainnet.aptoslabs.com/v1", 
                "faucet_url": None,
                "chain_id": 1
            }
        }
        
        table = Table(title="Available Networks")
        table.add_column("Option", style="cyan")
        table.add_column("Network", style="green")
        table.add_column("Description", style="yellow")
        
        for key, net in networks.items():
            desc = "Production (No Faucet)" if net["name"] == "Mainnet" else "Has Faucet for Testing"
            table.add_row(key, net["name"], desc)
            
        self.console.print(table)
        
        choice = Prompt.ask("Select network", choices=["1", "2", "3"], default="1")
        selected_network = networks[choice]
        
        self.console.print(f"✅ Selected: [green]{selected_network['name']}[/green]")
        
        return selected_network
        
    def create_or_load_keys(self, network_config: Dict[str, Any]):
        """Create new keys or load existing ones"""
        self.console.print("\n[bold blue]🔑 KEY MANAGEMENT[/bold blue]")
        
        # Initialize WalletManager
        base_dir = self.project_root / "wallets"
        base_dir.mkdir(exist_ok=True)
        
        self.wallet_manager = WalletManager(
            network=network_config["name"].lower(),
            base_dir=str(base_dir)
        )
        
        # Check if we have existing keys
        action = Prompt.ask(
            "What would you like to do?",
            choices=["create", "load", "list"],
            default="create"
        )
        
        if action == "list":
            self.list_existing_keys()
            action = Prompt.ask(
                "Now what?",
                choices=["create", "load"], 
                default="create"
            )
            
        if action == "create":
            return self.create_new_keys()
        else:
            return self.load_existing_keys()
            
    def list_existing_keys(self):
        """List existing wallet keys"""
        wallets_dir = self.project_root / "wallets"
        if not wallets_dir.exists():
            self.console.print("📁 No wallets directory found")
            return
            
        coldkeys = [d for d in wallets_dir.iterdir() if d.is_dir()]
        if not coldkeys:
            self.console.print("🔍 No existing coldkeys found")
            return
            
        table = Table(title="Existing Coldkeys")
        table.add_column("Name", style="cyan")
        table.add_column("Path", style="yellow")
        
        for coldkey_dir in coldkeys:
            table.add_row(coldkey_dir.name, str(coldkey_dir))
            
        self.console.print(table)
        
    def create_new_keys(self):
        """Create new coldkey and hotkeys"""
        self.console.print("\n[bold yellow]🆕 Creating New Keys[/bold yellow]")
        
        # Coldkey name
        coldkey_name = Prompt.ask("Enter coldkey name", default="subnet1_coldkey")
        
        # Password
        password = getpass.getpass("Enter password for coldkey encryption: ")
        confirm_password = getpass.getpass("Confirm password: ")
        
        if password != confirm_password:
            self.console.print("[red]❌ Passwords don't match![/red]")
            return None
            
        try:
            # Create coldkey
            self.console.print("🔨 Creating coldkey...")
            mnemonic = self.wallet_manager.create_coldkey(coldkey_name, password)
            
            if mnemonic:
                self.console.print(f"✅ Coldkey '{coldkey_name}' created successfully!")
                self.console.print(f"🔑 [bold red]BACKUP THIS MNEMONIC:[/bold red] {mnemonic}")
                
                # Create hotkeys for validator and miner
                validator_hotkey = "validator_hotkey"
                miner_hotkey = "miner_hotkey"
                
                self.console.print(f"🔨 Creating validator hotkey '{validator_hotkey}'...")
                self.wallet_manager.add_hotkey(coldkey_name, validator_hotkey, password)
                
                self.console.print(f"🔨 Creating miner hotkey '{miner_hotkey}'...")
                self.wallet_manager.add_hotkey(coldkey_name, miner_hotkey, password)
                
                self.console.print("✅ All keys created successfully!")
                
                return {
                    "coldkey_name": coldkey_name,
                    "validator_hotkey": validator_hotkey,
                    "miner_hotkey": miner_hotkey,
                    "password": password
                }
            else:
                self.console.print("[red]❌ Failed to create coldkey[/red]") 
                return None
                
        except Exception as e:
            self.console.print(f"[red]❌ Error creating keys: {e}[/red]")
            return None
            
    def load_existing_keys(self):
        """Load existing keys"""
        self.console.print("\n[bold yellow]📂 Loading Existing Keys[/bold yellow]")
        
        coldkey_name = Prompt.ask("Enter coldkey name")
        password = getpass.getpass("Enter coldkey password: ")
        
        try:
            coldkey_info = self.wallet_manager.load_coldkey(coldkey_name, password)
            if coldkey_info:
                self.console.print(f"✅ Coldkey '{coldkey_name}' loaded successfully!")
                
                # List available hotkeys
                hotkeys = self.wallet_manager.list_hotkeys(coldkey_name)
                if hotkeys:
                    table = Table(title="Available Hotkeys")
                    table.add_column("Name", style="cyan")
                    table.add_column("Address", style="yellow")
                    
                    for hotkey_name, hotkey_info in hotkeys.items():
                        table.add_row(hotkey_name, hotkey_info.get("address", "N/A"))
                    
                    self.console.print(table)
                    
                    validator_hotkey = Prompt.ask("Enter validator hotkey name", default="validator_hotkey")
                    miner_hotkey = Prompt.ask("Enter miner hotkey name", default="miner_hotkey")
                else:
                    self.console.print("🔍 No hotkeys found, creating new ones...")
                    validator_hotkey = "validator_hotkey"
                    miner_hotkey = "miner_hotkey"
                    
                    self.wallet_manager.add_hotkey(coldkey_name, validator_hotkey, password)
                    self.wallet_manager.add_hotkey(coldkey_name, miner_hotkey, password)
                
                return {
                    "coldkey_name": coldkey_name,
                    "validator_hotkey": validator_hotkey,
                    "miner_hotkey": miner_hotkey,
                    "password": password
                }
            else:
                self.console.print("[red]❌ Failed to load coldkey[/red]")
                return None
                
        except Exception as e:
            self.console.print(f"[red]❌ Error loading keys: {e}[/red]")
            return None
            
    async def request_tokens(self, keys_info: Dict[str, str], network_config: Dict[str, Any]):
        """Request test tokens from faucet"""
        self.console.print("\n[bold blue]💰 TOKEN FAUCET[/bold blue]")
        
        if not network_config.get("faucet_url"):
            self.console.print("[yellow]⚠️ This network doesn't have a faucet (likely Mainnet)[/yellow]")
            return
            
        try:
            # Get account addresses
            validator_info = self.wallet_manager.get_hotkey_info(
                keys_info["coldkey_name"], 
                keys_info["validator_hotkey"]
            )
            miner_info = self.wallet_manager.get_hotkey_info(
                keys_info["coldkey_name"],
                keys_info["miner_hotkey"] 
            )
            
            if not validator_info or not miner_info:
                self.console.print("[red]❌ Could not get hotkey addresses[/red]")
                return
                
            validator_address = validator_info["address"]
            miner_address = miner_info["address"]
            
            self.console.print(f"🎯 Validator Address: {validator_address}")
            self.console.print(f"🎯 Miner Address: {miner_address}")
            
            # Request tokens
            faucet_client = FaucetClient(network_config["faucet_url"])
            
            self.console.print("💸 Requesting tokens for validator...")
            await faucet_client.fund_account(validator_address, 100_000_000)  # 1 APT
            
            self.console.print("💸 Requesting tokens for miner...")  
            await faucet_client.fund_account(miner_address, 100_000_000)  # 1 APT
            
            self.console.print("✅ Tokens requested successfully!")
            
            # Check balances
            await self.check_balances(network_config, validator_address, miner_address)
            
        except Exception as e:
            self.console.print(f"[red]❌ Error requesting tokens: {e}[/red]")
            logger.exception("Token request failed")
            
    async def check_balances(self, network_config: Dict[str, Any], validator_addr: str, miner_addr: str):
        """Check account balances"""
        try:
            rest_client = RestClient(network_config["node_url"])
            
            self.console.print("\n💰 Checking balances...")
            
            # Check validator balance
            try:
                val_balance = await rest_client.account_balance(validator_addr)
                val_apt = val_balance / 100_000_000  # Convert to APT
                self.console.print(f"🎯 Validator Balance: {val_apt:.4f} APT")
            except Exception as e:
                self.console.print(f"⚠️ Could not check validator balance: {e}")
                
            # Check miner balance  
            try:
                miner_balance = await rest_client.account_balance(miner_addr)
                miner_apt = miner_balance / 100_000_000  # Convert to APT
                self.console.print(f"🎯 Miner Balance: {miner_apt:.4f} APT")
            except Exception as e:
                self.console.print(f"⚠️ Could not check miner balance: {e}")
                
        except Exception as e:
            self.console.print(f"[red]❌ Error checking balances: {e}[/red]")
            
    def save_env_config(self, keys_info: Dict[str, str], network_config: Dict[str, Any]):
        """Save configuration to .env file"""
        self.console.print("\n[bold blue]💾 SAVING CONFIGURATION[/bold blue]")
        
        try:
            # Get account addresses and private keys
            validator_info = self.wallet_manager.get_hotkey_info(
                keys_info["coldkey_name"],
                keys_info["validator_hotkey"]
            )
            miner_info = self.wallet_manager.get_hotkey_info(
                keys_info["coldkey_name"],
                keys_info["miner_hotkey"]
            )
            
            # Get private keys (need password)
            from mt_aptos.keymanager.decryption_utils import decode_hotkey_account
            
            validator_account = decode_hotkey_account(
                base_dir=str(self.project_root / "wallets"),
                coldkey_name=keys_info["coldkey_name"],
                hotkey_name=keys_info["validator_hotkey"],
                password=keys_info["password"]
            )
            
            miner_account = decode_hotkey_account(
                base_dir=str(self.project_root / "wallets"),
                coldkey_name=keys_info["coldkey_name"], 
                hotkey_name=keys_info["miner_hotkey"],
                password=keys_info["password"]
            )
            
            if not validator_account or not miner_account:
                self.console.print("[red]❌ Could not decode accounts[/red]")
                return
                
            # Configuration values
            env_config = {
                # Network Configuration
                "APTOS_NODE_URL": network_config["node_url"],
                "APTOS_CHAIN_ID": str(network_config["chain_id"]),
                "APTOS_CONTRACT_ADDRESS": "0x1234567890abcdef1234567890abcdef12345678",  # Placeholder
                
                # Validator Configuration
                "SUBNET1_VALIDATOR_ID": "subnet1_validator_001",
                "SUBNET1_VALIDATOR_HOST": "0.0.0.0",
                "SUBNET1_VALIDATOR_PORT": "8001", 
                "VALIDATOR_API_ENDPOINT": "http://localhost:8001",
                "APTOS_PRIVATE_KEY": validator_account.private_key.hex(),
                
                # Miner Configuration  
                "SUBNET1_MINER_ID": "subnet1_miner_001",
                "SUBNET1_MINER_HOST": "0.0.0.0",
                "SUBNET1_MINER_PORT": "9001",
                "SUBNET1_VALIDATOR_URL": "http://localhost:8001/v1/miner/submit_result",
                "SUBNET1_VALIDATOR_API_ENDPOINT": "http://localhost:8001",
                
                # Agent Configuration
                "MINER_AGENT_CHECK_INTERVAL": "300",
                
                # Logging
                "LOG_LEVEL": "INFO"
            }
            
            # Save to .env file
            for key, value in env_config.items():
                set_key(str(self.env_path), key, value)
                
            self.console.print(f"✅ Configuration saved to {self.env_path}")
            
            # Display summary
            self.display_summary(keys_info, network_config, validator_info, miner_info)
            
        except Exception as e:
            self.console.print(f"[red]❌ Error saving configuration: {e}[/red]")
            logger.exception("Failed to save configuration")
            
    def display_summary(self, keys_info: Dict[str, str], network_config: Dict[str, Any], 
                       validator_info: Dict[str, str], miner_info: Dict[str, str]):
        """Display setup summary"""
        self.console.print("\n[bold green]🎉 SETUP COMPLETE![/bold green]")
        
        table = Table(title="Subnet1 Configuration Summary")
        table.add_column("Component", style="cyan")
        table.add_column("Value", style="yellow")
        
        table.add_row("Network", network_config["name"])
        table.add_row("Node URL", network_config["node_url"])
        table.add_row("Coldkey", keys_info["coldkey_name"])
        table.add_row("Validator Hotkey", keys_info["validator_hotkey"])
        table.add_row("Validator Address", validator_info["address"])
        table.add_row("Miner Hotkey", keys_info["miner_hotkey"])
        table.add_row("Miner Address", miner_info["address"])
        
        self.console.print(table)
        
        self.console.print("\n[bold blue]📋 NEXT STEPS:[/bold blue]")
        self.console.print("1. Update APTOS_CONTRACT_ADDRESS in .env with actual contract")
        self.console.print("2. Run validator: python scripts/run_validator_aptos.py")
        self.console.print("3. Run miner: python scripts/run_miner_aptos.py")
        self.console.print("4. Check logs and monitor performance")

async def main():
    """Main setup function"""
    setup = Subnet1Setup()
    
    setup.console.print("[bold green]🚀 SUBNET1 APTOS SETUP[/bold green]")
    setup.console.print("This script will help you create keys and request tokens for testing\n")
    
    try:
        # Load existing environment
        setup.load_env()
        
        # Setup network configuration
        network_config = setup.setup_network_config()
        
        # Create or load keys
        keys_info = setup.create_or_load_keys(network_config)
        if not keys_info:
            setup.console.print("[red]❌ Key setup failed[/red]")
            return
            
        # Request tokens if testnet/devnet
        if network_config.get("faucet_url"):
            want_tokens = Confirm.ask("Request test tokens from faucet?", default=True)
            if want_tokens:
                await setup.request_tokens(keys_info, network_config)
        
        # Save configuration
        setup.save_env_config(keys_info, network_config)
        
        setup.console.print("\n[bold green]✅ Setup completed successfully![/bold green]")
        
    except KeyboardInterrupt:
        setup.console.print("\n[yellow]👋 Setup interrupted by user[/yellow]")
    except Exception as e:
        setup.console.print(f"[red]❌ Setup failed: {e}[/red]")
        logger.exception("Setup failed")

if __name__ == "__main__":
    asyncio.run(main()) 