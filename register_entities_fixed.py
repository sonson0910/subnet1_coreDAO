#!/usr/bin/env python3
"""
Fixed registration script with proper token minting
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


def register_entities_fixed():
    """Register all entities with proper token handling"""
    print(f"\n🎯 FIXED REGISTRATION FOR ALL ENTITIES")
    print("=" * 80)

    # Use the deployed contract address
    contract_address = "0x5f96BEA61E4ad2222c4B575fD6FFdCEd4DC04358"
core_token_address = "0x1361F20937a69aA841a37Ca943948463b8E6740C"

    print(f"🎯 Target contract: {contract_address}")
    print(f"🪙 CORE token: {core_token_address}")

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
        / "ModernTensorAI_v2_Bittensor.sol"
        / "ModernTensorAI_v2_Bittensor.json"
    )

    with open(contract_artifacts_path, "r") as f:
        contract_data = json.load(f)
        contract_abi = contract_data["abi"]

    contract = web3.eth.contract(address=contract_address, abi=contract_abi)
    print("✅ Contract loaded")

    # Setup token contract for minting
    core_token_abi = [
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
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [
                {"name": "_owner", "type": "address"},
                {"name": "_spender", "type": "address"},
            ],
            "name": "allowance",
            "outputs": [{"name": "remaining", "type": "uint256"}],
            "type": "function",
        },
    ]
    core_token = web3.eth.contract(address=core_token_address, abi=core_token_abi)

    # Use deployer account (miner 2) to mint tokens for others
    deployer_private_key = (
        "0x3ace434e2cd05cd0e614eb5d423cf04e4b925c17db9869e9c598851f88f52840"
    )
    deployer_account = web3.eth.account.from_key(deployer_private_key)
    print(f"🔑 Using deployer account: {deployer_account.address}")

    # Register each entity
    success_count = 0
    for entity in entities:
        print(f"\n🎯 Processing {entity['type']} {entity['name']}")
        print(f"   Address: {entity['address']}")
        print(f"   Endpoint: {entity.get('api_endpoint', 'N/A')}")

        # Check if already registered
        try:
            if entity["type"] == "miner":
                entity_info = contract.functions.getMinerInfo(entity["address"]).call()
            else:
                entity_info = contract.functions.getValidatorInfo(
                    entity["address"]
                ).call()

            if entity_info[0] != b"\\x00" * 32:  # Non-zero UID means registered
                print(f"   ✅ Already registered with UID: {entity_info[0].hex()}")
                success_count += 1
                continue
        except Exception as e:
            print(f"   🔍 Checking registration status: {e}")

        try:
            # Create account from private key
            private_key = entity["private_key"]
            if not private_key.startswith("0x"):
                private_key = "0x" + private_key

            account = web3.eth.account.from_key(private_key)

            if account.address.lower() != entity["address"].lower():
                print(f"   ❌ Private key doesn't match address!")
                continue

            # Check current balance
            current_balance = core_token.functions.balanceOf(account.address).call()
            stake_wei = web3.to_wei(float(entity["stake_amount"]), "ether")

            print(
                f"   💰 Current balance: {web3.from_wei(current_balance, 'ether')} CORE"
            )
            print(f"   💰 Required stake: {entity['stake_amount']} CORE")

            # Mint tokens if insufficient balance
            if current_balance < stake_wei:
                needed_amount = stake_wei * 2  # Mint 2x stake amount to be safe
                print(
                    f"   🏭 Minting {web3.from_wei(needed_amount, 'ether')} CORE tokens..."
                )

                mint_tx = core_token.functions.mint(
                    account.address, needed_amount
                ).build_transaction(
                    {
                        "from": deployer_account.address,
                        "gas": 100000,
                        "gasPrice": web3.to_wei("20", "gwei"),
                        "nonce": web3.eth.get_transaction_count(
                            deployer_account.address
                        ),
                    }
                )

                signed_mint = web3.eth.account.sign_transaction(
                    mint_tx, deployer_private_key
                )
                mint_hash = web3.eth.send_raw_transaction(signed_mint.raw_transaction)
                mint_receipt = web3.eth.wait_for_transaction_receipt(
                    mint_hash, timeout=60
                )

                if mint_receipt.status == 1:
                    print(f"   ✅ Minted tokens successfully")
                else:
                    print(f"   ❌ Failed to mint tokens")
                    continue

            # Approve contract to spend tokens
            print("   📝 Approving token spend...")
            approve_tx = core_token.functions.approve(
                contract_address, stake_wei
            ).build_transaction(
                {
                    "from": account.address,
                    "gas": 100000,
                    "gasPrice": web3.to_wei("20", "gwei"),
                    "nonce": web3.eth.get_transaction_count(account.address),
                }
            )

            signed_approve = web3.eth.account.sign_transaction(approve_tx, private_key)
            approve_hash = web3.eth.send_raw_transaction(signed_approve.raw_transaction)
            approve_receipt = web3.eth.wait_for_transaction_receipt(
                approve_hash, timeout=60
            )

            if approve_receipt.status != 1:
                print(f"   ❌ Failed to approve tokens")
                continue

            print(f"   ✅ Approved {entity['stake_amount']} CORE")

            # Prepare registration
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
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

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

    print(f"\n📊 FINAL REGISTRATION SUMMARY:")
    print(f"   Total entities: {len(entities)}")
    print(f"   Successfully registered: {success_count}")
    print(f"   Failed: {len(entities) - success_count}")

    return success_count == len(entities)


def main():
    """Main function"""
    print("🎯 FIXED ENTITY REGISTRATION")
    print("=" * 60)

    success = register_entities_fixed()

    if success:
        print(f"\n🎉 SUCCESS! ALL ENTITIES REGISTERED!")
        print(f"🎯 Contract: 0x60d7b1A881b01D49371eaFfBE2833AE2bcd86441")
        print(f"🔍 Verify with: python test_metagraph_integration.py")
    else:
        print(f"\n⚠️ PARTIAL SUCCESS - Some entities failed to register")

    return success


if __name__ == "__main__":
    main()
