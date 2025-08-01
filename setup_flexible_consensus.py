#!/usr/bin/env python3
"""
Setup Script for Flexible Consensus in Subnet1

This script helps users set up and configure flexible consensus features:
- Install dependencies
- Configure environment
- Create entity accounts
- Test network connectivity
- Generate startup scripts
"""

import os
import sys
import json
import logging
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

# --- Setup paths ---
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent / "moderntensor_aptos"))

# --- Import configuration ---
try:
    from flexible_config import get_config_manager, FlexibleConfigManager
except ImportError as e:
    print(f"❌ FATAL: Cannot import flexible_config: {e}")
    sys.exit(1)

console = Console()
logger = logging.getLogger(__name__)


class FlexibleConsensusSetup:
    """
    Setup manager for flexible consensus features.
    """
    
    def __init__(self):
        self.project_root = project_root
        self.config_manager = get_config_manager()
        self.setup_status = {}
        
        # Paths
        self.env_file = self.project_root / ".env"
        self.entities_dir = self.project_root / "entities"
        self.scripts_dir = self.project_root / "scripts"
        
        console.print("\n🔧 Flexible Consensus Setup Manager")
        console.print("=" * 60)
    
    async def run_full_setup(self, interactive: bool = True):
        """Run complete setup process."""
        console.print("🚀 Starting Flexible Consensus Setup")
        
        steps = [
            ("check_dependencies", "Checking dependencies"),
            ("setup_directories", "Setting up directories"),
            ("configure_environment", "Configuring environment"),
            ("create_entity_accounts", "Creating entity accounts"),
            ("test_connectivity", "Testing network connectivity"),
            ("generate_startup_scripts", "Generating startup scripts"),
            ("show_usage_guide", "Showing usage guide"),
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            for step_name, description in steps:
                task = progress.add_task(f"[cyan]{description}...", total=None)
                
                try:
                    if interactive:
                        # Ask user before each step
                        if not Confirm.ask(f"\n📋 Execute: {description}?", default=True):
                            progress.update(task, description=f"[yellow]Skipped: {description}")
                            continue
                    
                    # Execute step
                    step_method = getattr(self, step_name)
                    await step_method()
                    
                    progress.update(task, description=f"[green]✅ {description}")
                    self.setup_status[step_name] = "completed"
                    
                except Exception as e:
                    progress.update(task, description=f"[red]❌ {description}: {str(e)}")
                    self.setup_status[step_name] = f"failed: {str(e)}"
                    
                    if interactive:
                        if not Confirm.ask("❓ Continue with remaining steps?", default=True):
                            break
        
        # Show final status
        await self.show_setup_summary()
    
    async def check_dependencies(self):
        """Check required dependencies."""
        console.print("\n🔍 Checking Dependencies")
        
        required_packages = [
            "web3",
            "eth-account", 
            "rich",
            "asyncio",
            "pathlib",
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                console.print(f"   ✅ {package}")
            except ImportError:
                missing_packages.append(package)
                console.print(f"   ❌ {package}")
        
        if missing_packages:
            console.print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
            console.print("📋 Install with: pip install " + " ".join(missing_packages))
            
            if Confirm.ask("🔧 Install missing packages now?", default=True):
                import subprocess
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install"
                ] + missing_packages)
                console.print("✅ Packages installed successfully")
        else:
            console.print("✅ All dependencies satisfied")
    
    async def setup_directories(self):
        """Setup required directories."""
        console.print("\n📁 Setting up directories")
        
        directories = [
            self.entities_dir,
            self.project_root / "slot_coordination",
            self.project_root / "flexible_configs",
            self.project_root / "logs",
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
            console.print(f"   📁 {directory.name}")
        
        console.print("✅ Directories created")
    
    async def configure_environment(self):
        """Configure environment variables."""
        console.print("\n⚙️ Configuring Environment")
        
        # Check if .env exists
        if self.env_file.exists():
            console.print("   📄 .env file exists")
            if not Confirm.ask("🔄 Update .env file?", default=False):
                return
        
        # Default environment configuration
        env_config = {
            "# Core Blockchain Configuration": "",
            "CORE_NODE_URL": "https://rpc.test.btcs.network",
            "CORE_CHAIN_ID": "1115",
            "CORE_CONTRACT_ADDRESS": "",
            "": "",
            "# Flexible Consensus Configuration": "",
            "CONSENSUS_MODE": "balanced",
            "MINER_MODE": "adaptive",
            "ENABLE_FLEXIBLE_CONSENSUS": "true",
            " ": "",
            "# Logging Configuration": "",
            "LOG_LEVEL": "INFO",
            "ENABLE_RICH_LOGGING": "true",
        }
        
        # Get user input for important values
        console.print("\n📋 Configuration Values:")
        
        core_node_url = Prompt.ask(
            "🌐 Core Node URL", 
            default=env_config["CORE_NODE_URL"]
        )
        env_config["CORE_NODE_URL"] = core_node_url
        
        contract_address = Prompt.ask(
            "📝 Core Contract Address",
            default=env_config.get("CORE_CONTRACT_ADDRESS", "")
        )
        env_config["CORE_CONTRACT_ADDRESS"] = contract_address
        
        consensus_mode = Prompt.ask(
            "🔄 Default Consensus Mode",
            choices=["rigid", "balanced", "ultra_flexible", "performance"],
            default="balanced"
        )
        env_config["CONSENSUS_MODE"] = consensus_mode
        
        miner_mode = Prompt.ask(
            "⛏️ Default Miner Mode", 
            choices=["traditional", "adaptive", "responsive", "patient"],
            default="adaptive"
        )
        env_config["MINER_MODE"] = miner_mode
        
        # Write .env file
        with open(self.env_file, "w") as f:
            for key, value in env_config.items():
                if key.startswith("#") or key.strip() == "":
                    f.write(f"{key}\n")
                else:
                    f.write(f"{key}={value}\n")
        
        console.print(f"✅ Environment configured in {self.env_file}")
    
    async def create_entity_accounts(self):
        """Create validator and miner accounts."""
        console.print("\n🔑 Creating Entity Accounts")
        
        # Ask how many entities to create
        num_validators = int(Prompt.ask("🛡️ Number of validators", default="2"))
        num_miners = int(Prompt.ask("⛏️ Number of miners", default="3"))
        
        # Create validator accounts
        for i in range(1, num_validators + 1):
            await self._create_entity_account("validator", i)
        
        # Create miner accounts  
        for i in range(1, num_miners + 1):
            await self._create_entity_account("miner", i)
        
        console.print("✅ Entity accounts created")
    
    async def _create_entity_account(self, entity_type: str, entity_id: int):
        """Create a single entity account."""
        from eth_account import Account
        import time
        
        entity_file = self.entities_dir / f"{entity_type}_{entity_id}.json"
        
        if entity_file.exists():
            console.print(f"   📄 {entity_type} {entity_id} already exists")
            return
        
        # Create new account
        account = Account.create()
        entity_uid = f"subnet1_{entity_type}_{entity_id:03d}"
        
        account_data = {
            "entity_id": entity_uid,
            "entity_type": entity_type,
            "entity_number": entity_id,
            "address": account.address,
            "private_key": account.key.hex(),
            "api_endpoint": f"http://localhost:{8000 + entity_id if entity_type == 'validator' else 9000 + entity_id}",
            "created_at": time.time(),
            "flexible_consensus_ready": True,
        }
        
        # Save account data
        with open(entity_file, "w") as f:
            json.dump(account_data, f, indent=2)
        
        console.print(f"   🔑 Created {entity_type} {entity_id}: {account.address[:10]}...")
        
        # Add to .env file
        self._add_entity_to_env(entity_type, entity_id, account_data)
    
    def _add_entity_to_env(self, entity_type: str, entity_id: int, account_data: Dict):
        """Add entity configuration to .env file."""
        env_additions = [
            f"\n# {entity_type.title()} {entity_id} Configuration",
            f"{entity_type.upper()}_{entity_id}_ID={account_data['entity_id']}",
            f"{entity_type.upper()}_{entity_id}_ADDRESS={account_data['address']}",
            f"{entity_type.upper()}_{entity_id}_PRIVATE_KEY={account_data['private_key']}",
            f"{entity_type.upper()}_{entity_id}_API_ENDPOINT={account_data['api_endpoint']}",
        ]
        
        with open(self.env_file, "a") as f:
            for line in env_additions:
                f.write(line + "\n")
    
    async def test_connectivity(self):
        """Test network connectivity."""
        console.print("\n🌐 Testing Network Connectivity")
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv(self.env_file)
        
        # Test Core blockchain connectivity
        core_node_url = os.getenv("CORE_NODE_URL")
        if core_node_url:
            try:
                from web3 import Web3
                w3 = Web3(Web3.HTTPProvider(core_node_url))
                
                if w3.is_connected():
                    latest_block = w3.eth.block_number
                    console.print(f"   ✅ Core blockchain connected (block: {latest_block})")
                else:
                    console.print(f"   ❌ Core blockchain connection failed")
            except Exception as e:
                console.print(f"   ❌ Core blockchain error: {e}")
        
        # Test contract connectivity if address is provided
        contract_address = os.getenv("CORE_CONTRACT_ADDRESS")
        if contract_address and contract_address.strip():
            try:
                # This would test contract connectivity
                console.print(f"   📝 Contract address configured: {contract_address[:10]}...")
            except Exception as e:
                console.print(f"   ⚠️ Contract test failed: {e}")
        
        console.print("✅ Connectivity tests completed")
    
    async def generate_startup_scripts(self):
        """Generate convenient startup scripts."""
        console.print("\n📜 Generating Startup Scripts")
        
        # Load entities
        entity_files = list(self.entities_dir.glob("*.json"))
        validators = []
        miners = []
        
        for entity_file in entity_files:
            with open(entity_file, "r") as f:
                data = json.load(f)
            
            if data["entity_type"] == "validator":
                validators.append(data)
            elif data["entity_type"] == "miner": 
                miners.append(data)
        
        # Generate individual startup scripts
        for validator in validators:
            script_content = self._generate_validator_script(validator)
            script_file = self.scripts_dir / f"start_validator_{validator['entity_number']}.sh"
            
            with open(script_file, "w") as f:
                f.write(script_content)
            
            script_file.chmod(0o755)
            console.print(f"   📜 {script_file.name}")
        
        for miner in miners:
            script_content = self._generate_miner_script(miner)
            script_file = self.scripts_dir / f"start_miner_{miner['entity_number']}.sh"
            
            with open(script_file, "w") as f:
                f.write(script_content)
            
            script_file.chmod(0o755)
            console.print(f"   📜 {script_file.name}")
        
        # Generate network startup script
        network_script = self._generate_network_script(validators, miners)
        network_script_file = self.scripts_dir / "start_flexible_network.sh"
        
        with open(network_script_file, "w") as f:
            f.write(network_script)
        
        network_script_file.chmod(0o755)
        console.print(f"   📜 {network_script_file.name}")
        
        console.print("✅ Startup scripts generated")
    
    def _generate_validator_script(self, validator_data: Dict) -> str:
        """Generate startup script for a validator."""
        return f"""#!/bin/bash
# Flexible Validator {validator_data['entity_number']} Startup Script
# Generated by setup_flexible_consensus.py

echo "🛡️ Starting Flexible Validator {validator_data['entity_number']}"
echo "📍 Address: {validator_data['address']}"
echo "👂 Endpoint: {validator_data['api_endpoint']}"

cd "$(dirname "$0")/.."

python scripts/run_flexible_validator_subnet1.py \\
    --validator {validator_data['entity_number']} \\
    --mode balanced \\
    --auto-adapt \\
    --log-level INFO

echo "🛑 Validator {validator_data['entity_number']} stopped"
"""
    
    def _generate_miner_script(self, miner_data: Dict) -> str:
        """Generate startup script for a miner."""
        return f"""#!/bin/bash
# Flexible Miner {miner_data['entity_number']} Startup Script
# Generated by setup_flexible_consensus.py

echo "⛏️ Starting Flexible Miner {miner_data['entity_number']}"
echo "📍 Address: {miner_data['address']}"
echo "👂 Endpoint: {miner_data['api_endpoint']}"

cd "$(dirname "$0")/.."

python scripts/run_flexible_miner_subnet1.py \\
    --miner {miner_data['entity_number']} \\
    --mode adaptive \\
    --auto-detect-validators \\
    --log-level INFO

echo "🛑 Miner {miner_data['entity_number']} stopped"
"""
    
    def _generate_network_script(self, validators: List[Dict], miners: List[Dict]) -> str:
        """Generate network startup script."""
        return f"""#!/bin/bash
# Flexible Network Startup Script
# Generated by setup_flexible_consensus.py

echo "🌐 Starting Flexible Consensus Network"
echo "🛡️ Validators: {len(validators)}"
echo "⛏️ Miners: {len(miners)}"

cd "$(dirname "$0")/.."

python scripts/run_flexible_network.py start \\
    --validators {len(validators)} \\
    --miners {len(miners)} \\
    --consensus-mode balanced \\
    --miner-mode adaptive \\
    --staggered \\
    --monitor

echo "🛑 Network stopped"
"""
    
    async def show_usage_guide(self):
        """Show usage guide."""
        console.print("\n📚 Flexible Consensus Usage Guide")
        
        usage_text = """
🚀 GETTING STARTED:

1. Start Individual Entities:
   ./scripts/start_validator_1.sh    # Start validator 1
   ./scripts/start_miner_1.sh        # Start miner 1

2. Start Complete Network:
   ./scripts/start_flexible_network.sh

3. Use Python Scripts Directly:
   python scripts/run_flexible_validator_subnet1.py --validator 1 --mode balanced
   python scripts/run_flexible_miner_subnet1.py --miner 1 --mode adaptive

🔧 FLEXIBILITY MODES:

Consensus Modes (Validators):
• rigid         - Traditional fixed timing
• balanced      - Balanced flexibility (recommended)
• ultra_flexible - Maximum flexibility (development)
• performance   - Performance optimized

Miner Modes:
• traditional   - Fixed timing
• adaptive      - Adapts to network (recommended)
• responsive    - Fast response mode
• patient       - Patient long-term mode

📊 CONFIGURATION:

View configs:      python scripts/run_flexible_network.py config
Demo features:     python scripts/run_flexible_network.py demo
Custom configs:    Edit flexible_configs/ directory

🔍 MONITORING:

Network status:    python scripts/run_flexible_network.py start --monitor
Entity logs:       Check individual entity outputs
Debug mode:        Add --log-level DEBUG to any script

💡 KEY FEATURES:

✅ Start validators anytime during consensus
✅ Automatic network synchronization
✅ Adaptive timing based on conditions
✅ Graceful handling of offline entities
✅ Backward compatibility with rigid mode
        """
        
        console.print(Panel(usage_text.strip(), title="Usage Guide", style="green"))
    
    async def show_setup_summary(self):
        """Show setup completion summary."""
        console.print("\n📋 Setup Summary")
        
        table = Table(title="Setup Status")
        table.add_column("Step", style="cyan")
        table.add_column("Status", style="green")
        
        for step, status in self.setup_status.items():
            if status == "completed":
                status_display = "✅ Completed"
                style = "green"
            elif status.startswith("failed"):
                status_display = f"❌ {status}"
                style = "red"
            else:
                status_display = f"⚠️ {status}"
                style = "yellow"
            
            table.add_row(step.replace("_", " ").title(), status_display)
        
        console.print(table)
        
        # Show next steps
        completed_steps = sum(1 for status in self.setup_status.values() if status == "completed")
        total_steps = len(self.setup_status)
        
        if completed_steps == total_steps:
            next_steps = """
🎉 SETUP COMPLETE!

Next steps:
1. Start your network: ./scripts/start_flexible_network.sh
2. Or start individual entities with the generated scripts
3. Check the usage guide above for more options

Your flexible consensus network is ready to run!
            """
        else:
            next_steps = f"""
⚠️ Setup partially complete ({completed_steps}/{total_steps} steps)

Consider re-running failed steps or continue with manual configuration.
Check the error messages above for details.
            """
        
        console.print(Panel(next_steps.strip(), title="Next Steps", style="blue"))


async def run_setup(args):
    """Run the setup process."""
    setup = FlexibleConsensusSetup()
    
    if args.step:
        # Run specific step
        step_method = getattr(setup, args.step, None)
        if step_method:
            await step_method()
        else:
            console.print(f"❌ Unknown step: {args.step}")
            return
    else:
        # Run full setup
        await setup.run_full_setup(interactive=args.interactive)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Setup Flexible Consensus for Subnet1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup_flexible_consensus.py                    # Full interactive setup
  python setup_flexible_consensus.py --non-interactive  # Automated setup
  python setup_flexible_consensus.py --step configure_environment  # Run specific step
        """,
    )
    
    parser.add_argument(
        "--step",
        help="Run specific setup step only"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        default=True,
        help="Interactive mode (default: True)"
    )
    
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Non-interactive automated setup"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Handle non-interactive flag
    if args.non_interactive:
        args.interactive = False
    
    try:
        asyncio.run(run_setup(args))
    except KeyboardInterrupt:
        console.print("\n👋 Setup interrupted by user")
    except Exception as e:
        console.print(f"\n💥 Setup error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()