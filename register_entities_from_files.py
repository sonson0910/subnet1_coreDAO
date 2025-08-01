#!/usr/bin/env python3
"""
Register entities using keys from entities folder
"""
import os
import sys
import json
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add project path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "moderntensor_aptos"))


def main():
    print("🚀 REGISTERING ENTITIES FROM FILES")
    print("=" * 60)

    # Load entities from files
    entities_dir = Path(__file__).parent / "entities"

    entities = []
    for file_path in entities_dir.glob("*.json"):
        with open(file_path, "r") as f:
            entity = json.load(f)
            entities.append(entity)

    print(f"📄 Loaded {len(entities)} entities from files")

    # Web3 setup
    rpc_url = os.getenv("CORE_NODE_URL", "https://rpc.test.btcs.network")
    contract_address = os.getenv(
        "CORE_CONTRACT_ADDRESS", "0xF5e19326A4c266F24404155aaF434D27e1064833"
    )  # New contract with updateMinerScores

    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not web3.is_connected():
        print("❌ Failed to connect to Core network")
        return

    print(f"✅ Connected to Core network: {rpc_url}")
    print(f"📝 Contract address: {contract_address}")

    # Load contract ABI
    contract_artifacts_path = (
        project_root
        / "moderntensor_aptos"
        / "mt_core"
        / "smartcontract"
        / "artifacts"
        / "contracts"
        / "ModernTensorAI_v2_Bittensor.sol"
        / "ModernTensorAI_v2_Bittensor.json"
    )

    if not contract_artifacts_path.exists():
        print(f"❌ Contract artifacts not found: {contract_artifacts_path}")
        return

    with open(contract_artifacts_path, "r") as f:
        contract_data = json.load(f)
        contract_abi = contract_data["abi"]

    contract = web3.eth.contract(address=contract_address, abi=contract_abi)
    print("✅ Contract loaded")

    # Register entities
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

            # Check if already registered
            try:
                if entity["type"] == "miner":
                    existing = contract.functions.getMinerInfo(entity["address"]).call()
                    if existing[9] == 1:  # status == Active
                        print(f"   ⚠️ Already registered as active miner")
                        continue
                else:  # validator
                    existing = contract.functions.getValidatorInfo(
                        entity["address"]
                    ).call()
                    if existing[9] == 1:  # status == Active
                        print(f"   ⚠️ Already registered as active validator")
                        continue
            except:
                pass  # Not registered yet

            # Prepare transaction
            stake_wei = web3.to_wei(float(entity["stake_amount"]), "ether")

            if entity["type"] == "miner":
                # Register miner
                tx_data = contract.functions.registerMiner(
                    entity["address"],
                    entity.get("api_endpoint", f"http://localhost:8101"),
                    stake_wei,
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
                    entity["address"],
                    entity.get("api_endpoint", f"http://localhost:8001"),
                    stake_wei,
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
            else:
                print(f"   ❌ Transaction failed")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n✅ Registration process completed!")
    print(f"🔍 Check results with: python quick_key_check.py")


if __name__ == "__main__":
    main()
