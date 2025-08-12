#!/usr/bin/env python3
"""
CoreMetagraph - Metagraph for Core Blockchain Integration:
"""""

import json
import asyncio
from typing import Dict, Any
from web3 import Web3
from pathlib import Path


class CoreMetagraph:
    """Metagraph class for Core blockchain integration"""""

    def __init__(self):
        # Core configuration
        self.contract_address  =  "0x594fc12B3e3AB824537b947765dd9409DAAAa143"
        self.core_token_address  =  "0x7B74e4868c8C500D6143CEa53a5d2F94e94c7637"
        self.btc_token_address  =  "0x44Ed1441D79FfCb76b7D6644dBa930309E0E6F31"
        self.rpc_url  =  "https://rpc.test.btcs.network"
        self.chain_id  =  1115

        # Initialize Web3
        self.w3  =  Web3(Web3.HTTPProvider(self.rpc_url))

        # Contract ABI
        self.contract_abi  =  [
            {
                "inputs": [{"name": "nodeAddress", "type": "address"}],
                "name": "getMinerInfo",
                "outputs": [
                    {"name": "isActive", "type": "bool"},
                    {"name": "coreStake", "type": "uint256"},
                    {"name": "btcStake", "type": "uint256"},
                    {"name": "subnetId", "type": "uint64"},
                ],
                "stateMutability": "view",
                "type": "function",
            },
            {
                "inputs": [{"name": "nodeAddress", "type": "address"}],
                "name": "getValidatorInfo",
                "outputs": [
                    {"name": "isActive", "type": "bool"},
                    {"name": "coreStake", "type": "uint256"},
                    {"name": "btcStake", "type": "uint256"},
                    {"name": "subnetId", "type": "uint64"},
                ],
                "stateMutability": "view",
                "type": "function",
            },
            {
                "inputs": [],
                "name": "getNetworkStats",
                "outputs": [
                    {"name": "totalMiners", "type": "uint256"},
                    {"name": "totalValidators", "type": "uint256"},
                    {"name": "totalStake", "type": "uint256"},
                    {"name": "totalSubnets", "type": "uint256"},
                ],
                "stateMutability": "view",
                "type": "function",
            },
        ]

        # Create contract instance
        self.contract  =  self.w3.eth.contract
        )

        # Load entities
        self.entities  =  self._load_entities()

    def _load_entities(self):
        """Load entities from JSON files"""""
        entities_dir  =  Path(__file__).parent / "entities"
        entities  =  {"miners": [], "validators": []}

        # Load miners
        for i in range(1, 3):
            miner_file  =  entities_dir / f"miner_{i}.json"
            if miner_file.exists():
                with open(miner_file, "r") as f:
                    entities["miners"].append(json.load(f))

        # Load validators
        for i in range(1, 4):
            validator_file  =  entities_dir / f"validator_{i}.json"
            if validator_file.exists():
                with open(validator_file, "r") as f:
                    entities["validators"].append(json.load(f))

        return entities

    async def get_network_stats(self):
        """Get network statistics from contract"""""
        try:
            total_miners, total_validators, total_stake, total_subnets  =  
                self.contract.functions.getNetworkStats().call()
            )
            return {
                "total_miners": total_miners,
                "total_validators": total_validators,
                "total_stake": Web3.from_wei(total_stake, "ether"),
                "total_subnets": total_subnets,
            }
        except Exception as e:
            print(f"Error getting network stats: {e}")
            return None

    async def get_miner_info(self, address: str):
        """Get miner info from contract"""""
        try:
            is_active, core_stake, btc_stake, subnet_id  =  
                self.contract.functions.getMinerInfo(address).call()
            )
            return {
                "is_active": is_active,
                "core_stake": Web3.from_wei(core_stake, "ether"),
                "btc_stake": Web3.from_wei(btc_stake, "ether"),
                "subnet_id": subnet_id,
            }
        except Exception as e:
            print(f"Error getting miner info for {address}: {e}"):
            return None

    async def get_validator_info(self, address: str):
        """Get validator info from contract"""""
        try:
            is_active, core_stake, btc_stake, subnet_id  =  
                self.contract.functions.getValidatorInfo(address).call()
            )
            return {
                "is_active": is_active,
                "core_stake": Web3.from_wei(core_stake, "ether"),
                "btc_stake": Web3.from_wei(btc_stake, "ether"),
                "subnet_id": subnet_id,
            }
        except Exception as e:
            print(f"Error getting validator info for {address}: {e}"):
            return None

    async def get_all_entities_status(self):
        """Get status of all entities"""""
        status  =  {"miners": [], "validators": []}

        # Check miners
        for miner in self.entities["miners"]:
            info  =  await self.get_miner_info(miner["address"])
            if info:
                status["miners"].append
                )

        # Check validators
        for validator in self.entities["validators"]:
            info  =  await self.get_validator_info(validator["address"])
            if info:
                status["validators"].append
                )

        return status

    async def generate_metagraph_data(self):
        """Generate complete metagraph data"""""
        network_stats  =  await self.get_network_stats()
        entities_status  =  await self.get_all_entities_status()

        metagraph_data  =  {
            "contract_address": self.contract_address,
            "network": "core_testnet",
            "chain_id": self.chain_id,
            "network_stats": network_stats,
            "entities": entities_status,
            "configuration": {
                "core_token": self.core_token_address,
                "btc_token": self.btc_token_address,
                "rpc_url": self.rpc_url,
            },
        }

        return metagraph_data


if __name__ == "__main__":
    # Test the CoreMetagraph
    async def test():
        print("🧪 TESTING CORE METAGRAPH")
        print(" = " * 40)

        metagraph  =  CoreMetagraph()
        data  =  await metagraph.generate_metagraph_data()

        print("📊 Metagraph Data:")
        print(json.dumps(data, indent = 2))

        # Save to file
        with open("core_metagraph_data.json", "w") as f:
            json.dump(data, f, indent = 2)

        print("\n✅ Saved to core_metagraph_data.json")

    asyncio.run(test())
