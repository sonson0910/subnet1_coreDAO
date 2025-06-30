#!/usr/bin/env python3
"""
Kiểm tra Setup của Subnet1
Script để validate configuration và test kết nối
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
    from mt_aptos.account import Account
    from mt_aptos.async_client import RestClient
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("🔧 Hãy chạy: pip install -e . từ thư mục gốc")
    sys.exit(1)

class SetupChecker:
    def __init__(self):
        self.console = Console()
        self.subnet1_dir = Path(__file__).parent
        self.env_file = self.subnet1_dir / '.env'
        self.config = {}
        
    def load_config(self):
        """Load configuration từ .env file"""
        if not self.env_file.exists():
            self.console.print(f"[red]❌ File .env không tồn tại: {self.env_file}[/red]")
            return False
            
        load_dotenv(self.env_file)
        
        required_keys = [
            'APTOS_NODE_URL',
            'APTOS_PRIVATE_KEY', 
            'SUBNET1_VALIDATOR_ID',
            'SUBNET1_MINER_ID',
            'VALIDATOR_ADDRESS',
            'MINER_ADDRESS'
        ]
        
        missing_keys = []
        for key in required_keys:
            value = os.getenv(key)
            if value:
                self.config[key] = value
            else:
                missing_keys.append(key)
                
        if missing_keys:
            self.console.print(f"[red]❌ Thiếu các config keys: {missing_keys}[/red]")
            return False
            
        self.console.print("[green]✅ Config loaded successfully[/green]")
        return True
        
    def validate_keys(self):
        """Validate private keys và addresses"""
        self.console.print("\n[blue]🔑 Validating Keys...[/blue]")
        
        try:
            # Validate validator key
            validator_key = self.config.get('APTOS_PRIVATE_KEY')
            if validator_key:
                validator_account = Account.load_key(validator_key)
                derived_address = validator_account.address().hex()
                stored_address = self.config.get('VALIDATOR_ADDRESS')
                
                if derived_address.lower() == stored_address.lower():
                    self.console.print("✅ Validator key valid")
                else:
                    self.console.print(f"[red]❌ Validator address mismatch[/red]")
                    self.console.print(f"   Derived: {derived_address}")
                    self.console.print(f"   Stored: {stored_address}")
                    
            # Validate miner key if exists
            miner_key = self.config.get('MINER_PRIVATE_KEY')
            if miner_key:
                miner_account = Account.load_key(miner_key)
                derived_miner_address = miner_account.address().hex()
                stored_miner_address = self.config.get('MINER_ADDRESS')
                
                if derived_miner_address.lower() == stored_miner_address.lower():
                    self.console.print("✅ Miner key valid")
                else:
                    self.console.print(f"[red]❌ Miner address mismatch[/red]")
                    self.console.print(f"   Derived: {derived_miner_address}")
                    self.console.print(f"   Stored: {stored_miner_address}")
                    
        except Exception as e:
            self.console.print(f"[red]❌ Key validation error: {e}[/red]")
            
    async def check_network_connection(self):
        """Kiểm tra kết nối network"""
        self.console.print("\n[blue]🌐 Checking Network Connection...[/blue]")
        
        node_url = self.config.get('APTOS_NODE_URL')
        if not node_url:
            self.console.print("[red]❌ APTOS_NODE_URL not configured[/red]")
            return
            
        try:
            rest_client = RestClient(node_url)
            
            # Test basic connection
            ledger_info = await rest_client.ledger_info()
            self.console.print(f"✅ Connected to Aptos network")
            self.console.print(f"   Chain ID: {ledger_info['chain_id']}")
            self.console.print(f"   Ledger Version: {ledger_info['ledger_version']}")
            
        except Exception as e:
            self.console.print(f"[red]❌ Network connection failed: {e}[/red]")
            
    async def check_account_balances(self):
        """Kiểm tra số dư accounts"""
        self.console.print("\n[blue]💰 Checking Account Balances...[/blue]")
        
        node_url = self.config.get('APTOS_NODE_URL')
        validator_address = self.config.get('VALIDATOR_ADDRESS')
        miner_address = self.config.get('MINER_ADDRESS')
        
        if not all([node_url, validator_address]):
            self.console.print("[red]❌ Missing network or address config[/red]")
            return
            
        try:
            rest_client = RestClient(node_url)
            
            # Check validator balance
            try:
                val_balance = await rest_client.account_balance(validator_address)
                val_apt = val_balance / 100_000_000
                self.console.print(f"🎯 Validator Balance: {val_apt:.4f} APT")
                
                if val_apt < 0.1:
                    self.console.print("[yellow]⚠️ Validator balance is low, consider requesting more tokens[/yellow]")
                    
            except Exception as e:
                self.console.print(f"⚠️ Could not check validator balance: {e}")
                
            # Check miner balance if address exists
            if miner_address:
                try:
                    miner_balance = await rest_client.account_balance(miner_address)
                    miner_apt = miner_balance / 100_000_000
                    self.console.print(f"🎯 Miner Balance: {miner_apt:.4f} APT")
                    
                    if miner_apt < 0.1:
                        self.console.print("[yellow]⚠️ Miner balance is low, consider requesting more tokens[/yellow]")
                        
                except Exception as e:
                    self.console.print(f"⚠️ Could not check miner balance: {e}")
                    
        except Exception as e:
            self.console.print(f"[red]❌ Balance check failed: {e}[/red]")
            
    def check_file_structure(self):
        """Kiểm tra cấu trúc file cần thiết"""
        self.console.print("\n[blue]📁 Checking File Structure...[/blue]")
        
        required_files = [
            'scripts/run_validator_aptos.py',
            'scripts/run_miner_aptos.py',
            'subnet1/validator.py',
            'subnet1/miner.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.subnet1_dir / file_path
            if full_path.exists():
                self.console.print(f"✅ {file_path}")
            else:
                self.console.print(f"[red]❌ {file_path}[/red]")
                missing_files.append(file_path)
                
        if missing_files:
            self.console.print(f"[red]⚠️ Missing {len(missing_files)} required files[/red]")
        else:
            self.console.print("[green]✅ All required files present[/green]")
            
    def display_config_summary(self):
        """Hiển thị tóm tắt config"""
        self.console.print("\n[blue]📋 Configuration Summary[/blue]")
        
        table = Table(title="Subnet1 Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="yellow")
        
        # Network settings
        table.add_row("Network URL", self.config.get('APTOS_NODE_URL', 'N/A'))
        table.add_row("Chain ID", self.config.get('APTOS_CHAIN_ID', 'N/A'))
        
        # Validator settings
        table.add_row("Validator ID", self.config.get('SUBNET1_VALIDATOR_ID', 'N/A'))
        table.add_row("Validator Address", self.config.get('VALIDATOR_ADDRESS', 'N/A'))
        table.add_row("Validator Port", self.config.get('SUBNET1_VALIDATOR_PORT', 'N/A'))
        
        # Miner settings
        table.add_row("Miner ID", self.config.get('SUBNET1_MINER_ID', 'N/A'))
        table.add_row("Miner Address", self.config.get('MINER_ADDRESS', 'N/A'))
        table.add_row("Miner Port", self.config.get('SUBNET1_MINER_PORT', 'N/A'))
        
        self.console.print(table)
        
    def provide_recommendations(self):
        """Đưa ra recommendations"""
        self.console.print("\n[blue]💡 Recommendations[/blue]")
        
        recommendations = []
        
        # Check if using placeholder contract address
        contract_addr = self.config.get('APTOS_CONTRACT_ADDRESS', '')
        if '1234567890abcdef' in contract_addr:
            recommendations.append("🔧 Update APTOS_CONTRACT_ADDRESS with real contract address")
            
        # Check balances
        node_url = self.config.get('APTOS_NODE_URL', '')
        if 'testnet' in node_url:
            recommendations.append("💰 For testnet, you can request more tokens from faucet if needed")
            
        if recommendations:
            for rec in recommendations:
                self.console.print(f"  • {rec}")
        else:
            self.console.print("✅ Configuration looks good!")

async def main():
    """Main function"""
    console = Console()
    
    console.print(Panel.fit("[bold blue]🔍 SUBNET1 SETUP CHECKER[/bold blue]", style="blue"))
    
    checker = SetupChecker()
    
    try:
        # Load config
        if not checker.load_config():
            return
            
        # Run all checks
        checker.validate_keys()
        await checker.check_network_connection()
        await checker.check_account_balances()
        checker.check_file_structure()
        
        # Display summary
        checker.display_config_summary()
        checker.provide_recommendations()
        
        console.print("\n[green]✅ Setup check completed![/green]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Check interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Check failed: {e}[/red]")

if __name__ == "__main__":
    asyncio.run(main()) 