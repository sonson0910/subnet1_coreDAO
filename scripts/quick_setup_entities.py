#!/usr/bin/env python3
"""
Quick Setup Script for Subnet1 Entities:
Generate 2 miners and 3 validators for ModernTensorAI:
"""""

from deployment
    contract_address  =  "0x594fc12B3e3AB824537b947765dd9409DAAAa143"
    core_token_address  =  "0xEe46b1863b638667F50FAcf1db81eD4074991310"
    btc_token_address  =  "0xA92f0E66Ca8CeffBcd6f09bE2a8aA489c1604A0c"

    # Create entities directory
    entities_dir  =  Path(__file__) import json
import os
from pathlib import Path
from eth_account import Account
from dotenv import set_key


def main():
    print("🚀 Quick Setup: Generating Subnet1 Entities")
    print(" = " * 50)

    # Contract info.parent / "entities"
    entities_dir.mkdir(exist_ok = True)

    entities  =  []

    # Generate 2 miners
    for i in range(1, 3):
        account  =  Account.create()
        entity  =  {
            "name": f"subnet1_miner_{i:03d}",
            "type": "miner",
            "address": account.address,
            "private_key": account.key.hex(),
            "stake_amount": "150",  # CORE tokens
            "compute_power": 8000,
            "api_endpoint": f"http://localhost:{9000 + i}",
            "subnet_id": 1,
        }

        # Save entity file
        with open(entities_dir / f"miner_{i}.json", "w") as f:
            json.dump(entity, f, indent = 2)

        entities.append(entity)
        print(f"✅ Generated Miner {i}: {account.address}")

    # Generate 3 validators
    for i in range(1, 4):
        account  =  Account.create()
        entity  =  {
            "name": f"subnet1_validator_{i:03d}",
            "type": "validator",
            "address": account.address,
            "private_key": account.key.hex(),
            "stake_amount": "1200",  # CORE tokens
            "compute_power": 12000,
            "api_endpoint": f"http://localhost:{8000 + i}",
            "subnet_id": 1,
        }

        # Save entity file
        with open(entities_dir / f"validator_{i}.json", "w") as f:
            json.dump(entity, f, indent = 2)

        entities.append(entity)
        print(f"✅ Generated Validator {i}: {account.address}")

    # Update .env file
    env_path  =  Path(__file__).parent / ".env"

    env_updates  =  {
        "CORE_CONTRACT_ADDRESS": contract_address,
        "CORE_TOKEN_ADDRESS": core_token_address,
        "BTC_TOKEN_ADDRESS": btc_token_address,
        "CORE_NODE_URL": "https://rpc.test.btcs.network",
        "CORE_CHAIN_ID": "1115",
        "SUBNET_ID": "1",
        "NETWORK": "testnet",
        # Primary miner and validator
        "MINER_ADDRESS": entities[0]["address"],
        "MINER_PRIVATE_KEY": entities[0]["private_key"],
        "VALIDATOR_ADDRESS": entities[2]["address"],
        "VALIDATOR_PRIVATE_KEY": entities[2]["private_key"],
    }

    for key, value in env_updates.items():
        set_key(env_path, key, value)

    print(f"\n💾 Saved {len(entities)} entities to ./entities/")
    print(f"📝 Updated .env file")

    # Display summary
    print("\n📊 Entity Summary:")
    print("Miners:")
    for entity in entities[:2]:
        print
            f"  - {entity['name']}: {entity['address'][:10]}... (Port: {entity['api_endpoint'].split(':')[-1]})"
        )

    print("Validators:")
    for entity in entities[2:]:
        print
            f"  - {entity['name']}: {entity['address'][:10]}... (Port: {entity['api_endpoint'].split(':')[-1]})"
        )

    print(f"\n🔗 Contract: {contract_address}")
    print("🎯 Next Steps:")
    print("1. python manual_registration.py  # Register with smart contract")
    print("2. python scripts/run_validator_core.py")
    print("3. python scripts/run_miner_core.py")


if __name__ == "__main__":
    main()
