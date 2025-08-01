#!/usr/bin/env python3
"""
ModernTensorAI Registration Script for Subnet1
Register miners and validators with deployed smart contract
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv, set_key
from web3 import Web3
from eth_account import Account as EthAccount
from eth_account.signers.local import LocalAccount

# Add project root to sys.path
project_root = Path(__file__).parent
parent_root = project_root.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(parent_root))

# Setup logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, show_time=True, show_path=False)],
)
logger = logging.getLogger(__name__)


@dataclass
class EntityConfig:
    """Configuration for miner or validator entity"""

    name: str
    entity_type: str  # "miner" or "validator"
    private_key: str
    address: str
    stake_amount: str  # in CORE tokens
    compute_power: int
    api_endpoint: str
    subnet_id: int = 1


class ModernTensorRegistration:
    """Registration manager for ModernTensorAI smart contract"""

    def __init__(self):
        self.console = Console()
        self.project_root = project_root
        self.env_path = self.project_root / ".env"

        # Contract information (from deployment)
        self.contract_address = "0x56C2F2d0914DF10CE048e07EF1eCbac09AF80cd2"
        self.core_token_address = "0xEe46b1863b638667F50FAcf1db81eD4074991310"
        self.btc_token_address = "0xA92f0E66Ca8CeffBcd6f09bE2a8aA489c1604A0c"

        # Network configuration
        self.rpc_url = "https://rpc.test.btcs.network"
        self.chain_id = 1115
        self.explorer_url = "https://scan.test.btcs.network"

        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        # Load contract ABI
        self.contract_abi = self._load_contract_abi()
        self.contract = None

        # Entity storage
        self.entities: List[EntityConfig] = []

    def _load_contract_abi(self) -> List[Dict]:
        """Load contract ABI from artifacts"""
        try:
            abi_path = (
                parent_root
                / "moderntensor_aptos"
                / "mt_core"
                / "smartcontract"
                / "artifacts"
                / "contracts"
                / "ModernTensorAI_Optimized.sol"
                / "ModernTensorAI_Optimized.json"
            )

            if abi_path.exists():
                with open(abi_path, "r") as f:
                    contract_data = json.load(f)
                    return contract_data["abi"]
            else:
                logger.warning(f"ABI file not found at {abi_path}")
                return self._get_minimal_abi()

        except Exception as e:
            logger.error(f"Error loading ABI: {e}")
            return self._get_minimal_abi()

    def _get_minimal_abi(self) -> List[Dict]:
        """Minimal ABI for basic operations"""
        return [
            {
                "inputs": [
                    {"name": "minerData", "type": "bytes[]"},
                    {"name": "subnetId", "type": "uint64"},
                ],
                "name": "batchRegisterMiners",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function",
            },
            {
                "inputs": [
                    {"name": "validatorData", "type": "bytes[]"},
                    {"name": "subnetId", "type": "uint64"},
                ],
                "name": "batchRegisterValidators",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function",
            },
            {
                "inputs": [{"name": "miner", "type": "address"}],
                "name": "getPackedMinerInfo",
                "outputs": [
                    {
                        "components": [
                            {"name": "owner", "type": "address"},
                            {"name": "subnetId", "type": "uint64"},
                            {"name": "computePower", "type": "uint32"},
                            {"name": "coreStake", "type": "uint128"},
                            {"name": "btcStake", "type": "uint128"},
                        ],
                        "name": "",
                        "type": "tuple",
                    }
                ],
                "stateMutability": "view",
                "type": "function",
            },
        ]

    def generate_entity(self, entity_type: str, name: str) -> EntityConfig:
        """Generate new entity (miner or validator) with keys"""

        # Generate new Ethereum account
        account = EthAccount.create()
        private_key = account.key.hex()
        address = account.address

        # Determine stake amount based on type
        if entity_type == "miner":
            stake_amount = "150"  # 150 CORE (above minimum of 100)
            compute_power = 8000
            port = 9000 + len([e for e in self.entities if e.entity_type == "miner"])
        else:  # validator
            stake_amount = "1200"  # 1200 CORE (above minimum of 1000)
            compute_power = 12000
            port = 8000 + len(
                [e for e in self.entities if e.entity_type == "validator"]
            )

        api_endpoint = f"http://localhost:{port}"

        entity = EntityConfig(
            name=name,
            entity_type=entity_type,
            private_key=private_key,
            address=address,
            stake_amount=stake_amount,
            compute_power=compute_power,
            api_endpoint=api_endpoint,
            subnet_id=1,
        )

        self.entities.append(entity)
        logger.info(f"✅ Generated {entity_type}: {name} ({address})")

        return entity

    def setup_contract_connection(self, deployer_private_key: str) -> bool:
        """Setup contract connection with deployer account"""
        try:
            # Create account from private key
            if deployer_private_key.startswith("0x"):
                deployer_private_key = deployer_private_key[2:]

            account = EthAccount.from_key(deployer_private_key)

            # Initialize contract
            self.contract = self.w3.eth.contract(
                address=self.contract_address, abi=self.contract_abi
            )

            self.deployer_account = account

            # Check connection
            balance = self.w3.eth.get_balance(account.address)
            logger.info(f"✅ Connected to contract: {self.contract_address}")
            logger.info(f"📍 Deployer: {account.address}")
            logger.info(f"💰 Balance: {Web3.from_wei(balance, 'ether')} CORE")

            return True

        except Exception as e:
            logger.error(f"❌ Contract connection failed: {e}")
            return False

    async def register_miners(self, miners: List[EntityConfig]) -> bool:
        """Register miners with smart contract"""
        try:
            logger.info(f"🔄 Registering {len(miners)} miners...")

            # Prepare batch data
            miner_data = []
            for miner in miners:
                # Encode miner data: [address, coreStake, btcStake, computePower, specializations]
                stake_wei = Web3.to_wei(miner.stake_amount, "ether")
                btc_stake_wei = Web3.to_wei("0.1", "ether")  # Small BTC stake

                data = Web3.solidity_keccak(
                    ["address", "uint128", "uint128", "uint32", "uint8"],
                    [
                        miner.address,
                        stake_wei,
                        btc_stake_wei,
                        miner.compute_power,
                        7,  # Specializations bitpacked (all types)
                    ],
                )

                miner_data.append(data)

            # Build transaction
            transaction = self.contract.functions.batchRegisterMiners(
                miner_data, 1  # subnet_id
            ).build_transaction(
                {
                    "from": self.deployer_account.address,
                    "gas": 2000000,
                    "gasPrice": Web3.to_wei("40", "gwei"),
                    "nonce": self.w3.eth.get_transaction_count(
                        self.deployer_account.address
                    ),
                }
            )

            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction, self.deployer_account.key
            )
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            logger.info(f"⏳ Transaction sent: {tx_hash.hex()}")

            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status == 1:
                logger.info(f"✅ Miners registered successfully!")
                logger.info(f"🔗 TX: {self.explorer_url}/tx/{tx_hash.hex()}")
                return True
            else:
                logger.error(f"❌ Transaction failed")
                return False

        except Exception as e:
            logger.error(f"❌ Miner registration failed: {e}")
            return False

    async def register_validators(self, validators: List[EntityConfig]) -> bool:
        """Register validators with smart contract"""
        try:
            logger.info(f"🔄 Registering {len(validators)} validators...")

            # Prepare batch data (similar to miners but different function)
            validator_data = []
            for validator in validators:
                stake_wei = Web3.to_wei(validator.stake_amount, "ether")
                btc_stake_wei = Web3.to_wei(
                    "0.5", "ether"
                )  # Larger BTC stake for validators

                data = Web3.solidity_keccak(
                    ["address", "uint128", "uint128", "uint32", "uint8"],
                    [
                        validator.address,
                        stake_wei,
                        btc_stake_wei,
                        validator.compute_power,
                        15,  # Full specializations for validators
                    ],
                )

                validator_data.append(data)

            # Build transaction
            transaction = self.contract.functions.batchRegisterValidators(
                validator_data, 1  # subnet_id
            ).build_transaction(
                {
                    "from": self.deployer_account.address,
                    "gas": 2000000,
                    "gasPrice": Web3.to_wei("40", "gwei"),
                    "nonce": self.w3.eth.get_transaction_count(
                        self.deployer_account.address
                    ),
                }
            )

            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction, self.deployer_account.key
            )
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            logger.info(f"⏳ Transaction sent: {tx_hash.hex()}")

            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status == 1:
                logger.info(f"✅ Validators registered successfully!")
                logger.info(f"🔗 TX: {self.explorer_url}/tx/{tx_hash.hex()}")
                return True
            else:
                logger.error(f"❌ Transaction failed")
                return False

        except Exception as e:
            logger.error(f"❌ Validator registration failed: {e}")
            return False

    def save_entity_configs(self) -> None:
        """Save entity configurations to files"""

        # Create entities directory
        entities_dir = self.project_root / "entities"
        entities_dir.mkdir(exist_ok=True)

        # Save each entity
        for entity in self.entities:
            entity_file = entities_dir / f"{entity.name}.json"

            config = {
                "name": entity.name,
                "type": entity.entity_type,
                "address": entity.address,
                "private_key": entity.private_key,
                "stake_amount": entity.stake_amount,
                "compute_power": entity.compute_power,
                "api_endpoint": entity.api_endpoint,
                "subnet_id": entity.subnet_id,
                "contract_address": self.contract_address,
                "created_at": datetime.now().isoformat(),
            }

            with open(entity_file, "w") as f:
                json.dump(config, f, indent=2)

            logger.info(f"💾 Saved: {entity_file}")

    def update_env_file(self) -> None:
        """Update .env file with contract addresses and entity info"""

        env_updates = {
            "CORE_CONTRACT_ADDRESS": self.contract_address,
            "CORE_TOKEN_ADDRESS": self.core_token_address,
            "BTC_TOKEN_ADDRESS": self.btc_token_address,
            "CORE_NODE_URL": self.rpc_url,
            "CORE_CHAIN_ID": str(self.chain_id),
            "SUBNET_ID": "1",
            "NETWORK": "testnet",
        }

        # Add entity-specific configs
        miners = [e for e in self.entities if e.entity_type == "miner"]
        validators = [e for e in self.entities if e.entity_type == "validator"]

        if miners:
            env_updates["MINER_ADDRESS"] = miners[0].address
            env_updates["MINER_PRIVATE_KEY"] = miners[0].private_key
            env_updates["MINER_API_ENDPOINT"] = miners[0].api_endpoint

        if validators:
            env_updates["VALIDATOR_ADDRESS"] = validators[0].address
            env_updates["VALIDATOR_PRIVATE_KEY"] = validators[0].private_key
            env_updates["VALIDATOR_API_ENDPOINT"] = validators[0].api_endpoint

        # Write to .env
        for key, value in env_updates.items():
            set_key(self.env_path, key, value)

        logger.info(f"✅ Updated .env file: {self.env_path}")

    def display_summary(self) -> None:
        """Display registration summary"""

        table = Table(title="🎉 Registration Summary")
        table.add_column("Entity", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Address", style="green")
        table.add_column("Stake", style="yellow")
        table.add_column("API Endpoint", style="blue")

        for entity in self.entities:
            table.add_row(
                entity.name,
                entity.entity_type.upper(),
                f"{entity.address[:10]}...",
                f"{entity.stake_amount} CORE",
                entity.api_endpoint,
            )

        self.console.print(table)
        self.console.print("")

        # Display next steps
        self.console.print("🚀 [bold green]Next Steps:[/bold green]")
        self.console.print(
            "1. Run validators: [cyan]python scripts/run_validator_core.py[/cyan]"
        )
        self.console.print(
            "2. Run miners: [cyan]python scripts/run_miner_core.py[/cyan]"
        )
        self.console.print("3. Monitor network: [cyan]python monitor_tokens.py[/cyan]")
        self.console.print("")
        self.console.print(
            f"🔗 [bold blue]Contract:[/bold blue] {self.explorer_url}/address/{self.contract_address}"
        )


async def main():
    """Main registration workflow"""

    console = Console()
    console.print("🚀 [bold green]ModernTensorAI Entity Registration[/bold green]")
    console.print("=" * 60)

    # Initialize registration manager
    registration = ModernTensorRegistration()

    # Load deployer private key (from smart contract deployment)
    deployer_private_key = (
        "a07b6e0db803f9a21ffd1001c76b0aa0b313aaba8faab8c771af47301c4452b4"
    )

    # Setup contract connection
    if not registration.setup_contract_connection(deployer_private_key):
        console.print("❌ Failed to connect to smart contract")
        return

    console.print("\n📋 [bold]Generating Entities...[/bold]")

    # Generate 2 miners
    miner1 = registration.generate_entity("miner", "subnet1_miner_001")
    miner2 = registration.generate_entity("miner", "subnet1_miner_002")

    # Generate 3 validators
    validator1 = registration.generate_entity("validator", "subnet1_validator_001")
    validator2 = registration.generate_entity("validator", "subnet1_validator_002")
    validator3 = registration.generate_entity("validator", "subnet1_validator_003")

    console.print(f"\n✅ Generated {len(registration.entities)} entities")

    # Confirm registration
    if not Confirm.ask("\n🤔 Proceed with smart contract registration?"):
        console.print("❌ Registration cancelled")
        return

    console.print("\n🔄 [bold]Registering with Smart Contract...[/bold]")

    # Register miners
    miners = [e for e in registration.entities if e.entity_type == "miner"]
    if miners:
        success = await registration.register_miners(miners)
        if not success:
            console.print("❌ Miner registration failed")
            return

    # Register validators
    validators = [e for e in registration.entities if e.entity_type == "validator"]
    if validators:
        success = await registration.register_validators(validators)
        if not success:
            console.print("❌ Validator registration failed")
            return

    # Save configurations
    console.print("\n💾 [bold]Saving Configurations...[/bold]")
    registration.save_entity_configs()
    registration.update_env_file()

    # Display summary
    console.print("\n")
    registration.display_summary()

    console.print("\n🎊 [bold green]Registration completed successfully![/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
