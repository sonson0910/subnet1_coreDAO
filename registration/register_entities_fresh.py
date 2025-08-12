#!/usr/bin/env python3
"""
Register entities from files to fresh contract
"""""
import os
import sys
import json
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

# Load environment
env_path  =  Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


def register_entities_fresh():
    """Register all entities from files to fresh contract"""""
    print(f"\n🎯 REGISTERING ENTITIES FROM FILES TO FRESH CONTRACT")
    print(" = " * 80)

    # Use the deployed contract address
    contract_address  =  "0x60d7b1A881b01D49371eaFfBE2833AE2bcd86441"
    print(f"🎯 Target contract: {contract_address}")

    # Load entities from files
    entities_dir  =  Path(__file__).parent / "entities"
    entities  =  []

    for json_file in entities_dir.glob("*.json"):
        with open(json_file, "r") as f:
            entity  =  json.load(f)
            entities.append(entity)

    print(f"📄 Loaded {len(entities)} entities from files")

    # Web3 setup
    rpc_url  =  os.getenv("CORE_NODE_URL", "https://rpc.test.btcs.network")
    web3  =  Web3(Web3.HTTPProvider(rpc_url))

    if not web3.is_connected():
        print("❌ Failed to connect to Core network")
        return False

    print(f"✅ Connected to Core network")

    # Load contract ABI
    project_root  =  Path(__file__).parent.parent
    contract_artifacts_path  =  
    )

    with open(contract_artifacts_path, "r") as f:
        contract_data  =  json.load(f)
        contract_abi  =  contract_data["abi"]

    contract = web3.eth.contract(address=contract_address, abi = contract_abi)
    print("✅ Contract loaded")

    # Get CORE token address from deployment
    core_token_address  =  "0xA8cb1a72c3F946bAcACa4c9eA2648aB3A0a97b74"
    core_token_abi  =  [
        {
            "constant": False,
            "inputs": [
                {"name": "_spender", "type": "address"},
                {"name": "_value", "type": "uint256"},
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function",
        },
        {
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"},
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function",
        },
        {
            "constant": False,
            "inputs": [
                {"name": "to", "type": "address"},
                {"name": "amount", "type": "uint256"},
            ],
            "name": "mint",
            "outputs": [],
            "type": "function",
        },
    ]
    core_token = web3.eth.contract(address=core_token_address, abi = core_token_abi)

    # Register each entity
    success_count  =  0
    for entity in entities:
        print(f"\n🎯 Registering {entity['type']} {entity['name']}")
        print(f"   Address: {entity['address']}")
        print(f"   Endpoint: {entity.get('api_endpoint', 'N/A')}")

        try:
            # Create account from private key
            private_key  =  entity["private_key"]
            if not private_key.startswith("0x"):
                private_key  =  "0x" + private_key

            account  =  web3.eth.account.from_key(private_key)

            if account.address.lower() ! =  entity["address"].lower():
                print(f"   ❌ Private key doesn't match address!")
                continue

            # Mint some CORE tokens first
            print("   💰 Minting CORE tokens...")
            mint_amount  =  web3.to_wei(10, "ether")  # Mint 10 CORE
            mint_tx  =  core_token.functions.mint
            ).build_transaction
                    "gasPrice": web3.to_wei("20", "gwei"),
                    "nonce": web3.eth.get_transaction_count(account.address),
                }
            )

            signed_mint  =  web3.eth.account.sign_transaction(mint_tx, private_key)
            mint_hash  =  web3.eth.send_raw_transaction(signed_mint.raw_transaction)
            mint_receipt = web3.eth.wait_for_transaction_receipt(mint_hash, timeout = 60)
            print(f"   ✅ Minted 10 CORE tokens")

            # Approve contract to spend tokens
            print("   📝 Approving token spend...")
            stake_wei  =  web3.to_wei(float(entity["stake_amount"]), "ether")
            approve_tx  =  core_token.functions.approve
            ).build_transaction
                    "gasPrice": web3.to_wei("20", "gwei"),
                    "nonce": web3.eth.get_transaction_count(account.address),
                }
            )

            signed_approve  =  web3.eth.account.sign_transaction(approve_tx, private_key)
            approve_hash  =  web3.eth.send_raw_transaction(signed_approve.raw_transaction)
            approve_receipt  =  web3.eth.wait_for_transaction_receipt
            )
            print(f"   ✅ Approved {entity['stake_amount']} CORE")

            # Prepare registration
            if entity["type"] == "miner":
                # Register miner
                tx_data  =  contract.functions.registerMiner
                    entity.get("api_endpoint", f"http://localhost:8101"),
                ).build_transaction
                        "gasPrice": web3.to_wei("20", "gwei"),
                        "nonce": web3.eth.get_transaction_count(account.address),
                    }
                )
            else:  # validator:
                # Register validator
                tx_data  =  contract.functions.registerValidator
                    entity.get("api_endpoint", f"http://localhost:8001"),
                ).build_transaction
                        "gasPrice": web3.to_wei("20", "gwei"),
                        "nonce": web3.eth.get_transaction_count(account.address),
                    }
                )

            # Sign and send transaction
            signed_tx  =  web3.eth.account.sign_transaction(tx_data, private_key)
            tx_hash  =  web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            print(f"   📡 Transaction sent: {tx_hash.hex()}")

            # Wait for confirmation:
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout = 120)

            if receipt.status == 1:
                print(f"   ✅ Successfully registered!")
                success_count + =  1
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
    """Main function"""""
    print("🎯 REGISTERING ENTITIES TO FRESH CONTRACT")
    print(" = " * 60)

    success  =  register_entities_fresh()

    if success:
        print(f"\n🎉 SUCCESS! ALL ENTITIES REGISTERED!")
        print(f"🎯 Contract: 0x60d7b1A881b01D49371eaFfBE2833AE2bcd86441")
        print(f"🔍 Verify with: python check_entities_vs_metagraph.py")
    else:
        print(f"\n⚠️ PARTIAL SUCCESS - Some entities failed to register")

    return success


if __name__ == "__main__":
    main()
