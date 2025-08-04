#!/usr/bin/env python3
"""
Deploy fresh contract and register entities from files
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


def deploy_fresh_contract():
    """Deploy a fresh contract using Hardhat"""
    print("🚀 DEPLOYING FRESH CONTRACT")
    print("=" * 60)

    # Change to contract directory
    contract_dir = (
        Path(__file__).parent.parent
        / "moderntensor_aptos"
        / "mt_core"
        / "smartcontract"
    )

    print(f"📁 Contract directory: {contract_dir}")

    # Deploy using Hardhat
    try:
        print("🔨 Compiling and deploying contract...")

        # Run hardhat deploy
        result = subprocess.run(
            [
                "npx",
                "hardhat",
                "run",
                "scripts/deploy_v2_localhost.js",
                "--network",
                "core_testnet",
            ],
            cwd=contract_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            print("✅ Contract deployed successfully!")
            print("📄 Output:")
            print(result.stdout)

            # Extract contract address from output
            for line in result.stdout.split("\n"):
                if "ModernTensorAI v2.0:" in line:
                    new_contract_address = line.split(":")[-1].strip()
                    print(f"🎯 New contract address: {new_contract_address}")
                    return new_contract_address
        else:
            print("❌ Deployment failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return None

    except subprocess.TimeoutExpired:
        print("❌ Deployment timed out!")
        return None
    except Exception as e:
        print(f"❌ Error during deployment: {e}")
        return None


def update_env_contract(new_address):
    """Update .env with new contract address"""
    print(f"\n📝 UPDATING .ENV WITH NEW CONTRACT")
    print("=" * 60)

    env_file = Path(__file__).parent / ".env"

    # Read current .env
    with open(env_file, "r") as f:
        content = f.read()

    # Replace contract address
    import re

    updated_content = re.sub(
        r"CORE_CONTRACT_ADDRESS=0x[a-fA-F0-9]{40}",
        f"CORE_CONTRACT_ADDRESS={new_address}",
        content,
    )

    # Write back
    with open(env_file, "w") as f:
        f.write(updated_content)

    print(f"✅ Updated CORE_CONTRACT_ADDRESS to {new_address}")


def register_entities_from_files(contract_address):
    """Register all entities from files to new contract"""
    print(f"\n🎯 REGISTERING ENTITIES FROM FILES")
    print("=" * 60)

    # Load entities from files
    entities_dir = Path(__file__).parent / "entities"
    entities = []

    for json_file in entities_dir.glob("*.json"):
        with open(json_file, "r") as f:
            entity = json.load(f)
            entities.append(entity)

    print(f"📄 Loaded {len(entities)} entities from files")

    # Web3 setup
    rpc_url = os.getenv("CORE_NODE_URL", "https://rpc.test.btcs.network")
    web3 = Web3(Web3.HTTPProvider(rpc_url))

    if not web3.is_connected():
        print("❌ Failed to connect to Core network")
        return False

    print(f"✅ Connected to Core network")

    # Load contract ABI
    project_root = Path(__file__).parent.parent
    contract_artifacts_path = (
        project_root
        / "moderntensor_aptos"
        / "mt_core"
        / "smartcontract"
        / "artifacts"
        / "contracts"
        / "ModernTensorAI_Optimized.sol"
        / "ModernTensorAI_Optimized.json"
    )

    with open(contract_artifacts_path, "r") as f:
        contract_data = json.load(f)
        contract_abi = contract_data["abi"]

    contract = web3.eth.contract(address=contract_address, abi=contract_abi)
    print("✅ Contract loaded")

    # Register each entity
    success_count = 0
    for entity in entities:
        print(f"\n🎯 Registering {entity['type']} {entity['name']}")
        print(f"   Address: {entity['address']}")
        print(f"   Endpoint: {entity.get('api_endpoint', 'N/A')}")

        try:
            # Create account from private key
            private_key = entity["private_key"]
            if not private_key.startswith("0x"):
                private_key = "0x" + private_key

            account = web3.eth.account.from_key(private_key)

            if account.address.lower() != entity["address"].lower():
                print(f"   ❌ Private key doesn't match address!")
                continue

            # Prepare registration
            stake_wei = web3.to_wei(float(entity["stake_amount"]), "ether")

            if entity["type"] == "miner":
                # Register miner
                tx_data = contract.functions.registerMiner(
                    0,  # subnetId
                    stake_wei,  # coreStake
                    0,  # btcStake
                    entity.get("api_endpoint", f"http://localhost:8101"),
                ).build_transaction(
                    {
                        "from": account.address,
                        "gas": 500000,
                        "gasPrice": web3.to_wei("20", "gwei"),
                        "nonce": web3.eth.get_transaction_count(account.address),
                    }
                )
            else:  # validator
                # Register validator
                tx_data = contract.functions.registerValidator(
                    0,  # subnetId
                    stake_wei,  # coreStake
                    0,  # btcStake
                    entity.get("api_endpoint", f"http://localhost:8001"),
                ).build_transaction(
                    {
                        "from": account.address,
                        "gas": 500000,
                        "gasPrice": web3.to_wei("20", "gwei"),
                        "nonce": web3.eth.get_transaction_count(account.address),
                    }
                )

            # Sign and send transaction
            signed_tx = web3.eth.account.sign_transaction(tx_data, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

            print(f"   📡 Transaction sent: {tx_hash.hex()}")

            # Wait for confirmation
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt.status == 1:
                print(f"   ✅ Successfully registered!")
                success_count += 1
            else:
                print(f"   ❌ Transaction failed")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n📊 REGISTRATION SUMMARY:")
    print(f"   Total entities: {len(entities)}")
    print(f"   Successfully registered: {success_count}")
    print(f"   Failed: {len(entities) - success_count}")

    return success_count == len(entities)


def main():
    """Main function"""
    print("🔥 FRESH START: DEPLOY CONTRACT & REGISTER ENTITIES")
    print("=" * 80)

    # Step 1: Deploy fresh contract
    new_contract_address = deploy_fresh_contract()
    if not new_contract_address:
        print("❌ Contract deployment failed!")
        return False

    # Step 2: Update .env
    update_env_contract(new_contract_address)

    # Step 3: Register entities
    success = register_entities_from_files(new_contract_address)

    if success:
        print(f"\n🎉 SUCCESS! ALL ENTITIES REGISTERED!")
        print(f"🎯 New contract: {new_contract_address}")
        print(f"✅ Updated .env file")
        print(f"🔍 Verify with: python check_entities_vs_metagraph.py")
    else:
        print(f"\n⚠️ PARTIAL SUCCESS - Some entities failed to register")

    return success


if __name__ == "__main__":
    main()
