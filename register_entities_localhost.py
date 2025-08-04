#!/usr/bin/env python3

import os
import sys
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    print("🚀 REGISTERING ENTITIES ON NEW SMART CONTRACT")
    print("=" * 60)

    # Connect to Core Testnet
    rpc_url = "https://rpc.test.btcs.network"
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    print(f"🔗 Connected to Core Testnet: {web3.is_connected()}")
    print(f"⛓️ Chain ID: {web3.eth.chain_id}")

    # Contract details
    contract_address = os.getenv("CORE_CONTRACT_ADDRESS")
    if not contract_address:
        print("❌ CORE_CONTRACT_ADDRESS not found in .env")
        return

    print(f"📋 Contract Address: {contract_address}")

    # Load contract ABI
    try:
        abi_path = "../moderntensor_aptos/mt_core/smartcontract/artifacts/contracts/ModernTensor.sol/ModernTensor.json"
        with open(abi_path, "r") as f:
            contract_data = json.load(f)
            contract_abi = contract_data["abi"]
    except Exception as e:
        print(f"❌ Error loading contract ABI: {e}")
        return

    # Create contract instance
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    # Entity configurations with localhost endpoints
    entities = [
        {
            "type": "miner",
            "id": 1,
            "private_key": os.getenv("MINER_1_PRIVATE_KEY"),
            "address": os.getenv("MINER_1_ADDRESS"),
            "endpoint": "http://localhost:8101",
            "stake": "0.05",
        },
        {
            "type": "miner",
            "id": 2,
            "private_key": os.getenv("MINER_2_PRIVATE_KEY"),
            "address": os.getenv("MINER_2_ADDRESS"),
            "endpoint": "http://localhost:8102",
            "stake": "0.05",
        },
        {
            "type": "validator",
            "id": 1,
            "private_key": os.getenv("VALIDATOR_1_PRIVATE_KEY"),
            "address": os.getenv("VALIDATOR_1_ADDRESS"),
            "endpoint": "http://localhost:8001",
            "stake": "0.08",
        },
        {
            "type": "validator",
            "id": 2,
            "private_key": os.getenv("VALIDATOR_2_PRIVATE_KEY"),
            "address": os.getenv("VALIDATOR_2_ADDRESS"),
            "endpoint": "http://localhost:8002",
            "stake": "0.08",
        },
    ]

    print(f"\n📊 REGISTERING {len(entities)} ENTITIES...")
    print("-" * 40)

    for entity in entities:
        try:
            print(f"\n🔧 Registering {entity['type'].title()} {entity['id']}...")
            print(f"   Address: {entity['address']}")
            print(f"   Endpoint: {entity['endpoint']}")
            print(f"   Stake: {entity['stake']} CORE")

            # Validate private key and address
            if not entity["private_key"] or not entity["address"]:
                print(
                    f"❌ Missing private key or address for {entity['type']} {entity['id']}"
                )
                continue

            # Create account from private key
            account = web3.eth.account.from_key(entity["private_key"])
            if account.address.lower() != entity["address"].lower():
                print(
                    f"❌ Private key doesn't match address for {entity['type']} {entity['id']}"
                )
                continue

            # Check balance
            balance = web3.eth.get_balance(account.address)
            balance_eth = web3.from_wei(balance, "ether")
            print(f"   Balance: {balance_eth} CORE")

            if balance_eth < float(entity["stake"]) + 0.01:  # Need extra for gas
                print(f"❌ Insufficient balance for {entity['type']} {entity['id']}")
                continue

            # Prepare transaction data
            stake_wei = web3.to_wei(entity["stake"], "ether")

            if entity["type"] == "miner":
                # Register Miner
                tx_data = contract.functions.registerMiner(
                    0, entity["endpoint"]  # subnet_id
                ).build_transaction(
                    {
                        "from": account.address,
                        "value": stake_wei,
                        "gas": 500000,
                        "gasPrice": web3.to_wei(30, "gwei"),
                        "nonce": web3.eth.get_transaction_count(account.address),
                    }
                )
            else:
                # Register Validator
                tx_data = contract.functions.registerValidator(
                    0, entity["endpoint"]  # subnet_id
                ).build_transaction(
                    {
                        "from": account.address,
                        "value": stake_wei,
                        "gas": 500000,
                        "gasPrice": web3.to_wei(30, "gwei"),
                        "nonce": web3.eth.get_transaction_count(account.address),
                    }
                )

            # Sign and send transaction
            signed_tx = web3.eth.account.sign_transaction(
                tx_data, entity["private_key"]
            )
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

            print(f"   📤 Transaction sent: {tx_hash.hex()}")

            # Wait for confirmation
            print("   ⏳ Waiting for confirmation...")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            if receipt.status == 1:
                print(
                    f"   ✅ {entity['type'].title()} {entity['id']} registered successfully!"
                )
                print(
                    f"   🧾 Block: {receipt.blockNumber}, Gas Used: {receipt.gasUsed}"
                )
            else:
                print(f"   ❌ Registration failed for {entity['type']} {entity['id']}")

        except Exception as e:
            print(f"   �� Error registering {entity['type']} {entity['id']}: {str(e)}")
            continue

    print(f"\n🎯 REGISTRATION COMPLETE!")
    print("=" * 60)

    # Check final network state
    try:
        stats = contract.functions.getNetworkStats().call()
        print(f"📊 Final Network Stats:")
        print(f"   👥 Total Miners: {stats[0]}")
        print(f"   🛡️ Total Validators: {stats[1]}")
        print(f"   💰 Total Staked: {web3.from_wei(stats[2], 'ether')} CORE")
    except Exception as e:
        print(f"❌ Error fetching network stats: {e}")


if __name__ == "__main__":
    main()
