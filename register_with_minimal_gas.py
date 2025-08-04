#!/usr/bin/env python3

import os
import sys
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import json
from dotenv import load_dotenv

load_dotenv()


def main():
    print("🚀 REGISTER ENTITIES WITH MINIMAL GAS STRATEGY")
    print("=" * 60)

    # Connect to Core Testnet
    rpc_url = "https://rpc.test.btcs.network"
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    # Contract addresses
    contract_address = os.getenv("CORE_CONTRACT_ADDRESS")
    core_token_address = os.getenv("CORE_TOKEN_ADDRESS")

    # Load contract ABIs
    try:
        contract_abi_path = "../moderntensor_aptos/mt_core/smartcontract/artifacts/contracts/ModernTensor.sol/ModernTensor.json"
        with open(contract_abi_path, "r") as f:
            contract_data = json.load(f)
            contract_abi = contract_data["abi"]

        token_abi_path = "../moderntensor_aptos/mt_core/smartcontract/artifacts/contracts/MockCoreToken.sol/MockCoreToken.json"
        with open(token_abi_path, "r") as f:
            token_data = json.load(f)
            token_abi = token_data["abi"]
    except Exception as e:
        print(f"❌ Error loading ABIs: {e}")
        return

    # Create contract instances
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)
    core_token = web3.eth.contract(address=core_token_address, abi=token_abi)

    # Main account (has native CORE for gas)
    main_private_key = os.getenv("PRIVATE_KEY")
    main_account = web3.eth.account.from_key(main_private_key)

    print(
        f"💰 Main account balance: {web3.from_wei(web3.eth.get_balance(main_account.address), 'ether')} CORE"
    )

    # Entity configurations
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

    for entity in entities:
        try:
            print(f"\n🔧 Processing {entity['type'].title()} {entity['id']}...")

            entity_account = web3.eth.account.from_key(entity["private_key"])

            # Step 1: Send minimal gas (0.01 CORE) from main account
            print("   💸 Sending gas from main account...")
            gas_amount = web3.to_wei("0.01", "ether")

            gas_tx = {
                "to": entity_account.address,
                "value": gas_amount,
                "gas": 21000,
                "gasPrice": web3.to_wei("20", "gwei"),
                "nonce": web3.eth.get_transaction_count(main_account.address),
            }

            signed_gas_tx = main_account.sign_transaction(gas_tx)
            raw_gas_tx = getattr(
                signed_gas_tx,
                "rawTransaction",
                getattr(signed_gas_tx, "raw_transaction", None),
            )
            gas_tx_hash = web3.eth.send_raw_transaction(raw_gas_tx)
            web3.eth.wait_for_transaction_receipt(gas_tx_hash)
            print(f"   ✅ Gas sent: {gas_tx_hash.hex()}")

            # Step 2: Approve contract to spend ERC20 tokens
            print("   🔓 Approving contract to spend tokens...")
            stake_wei = web3.to_wei(entity["stake"], "ether")

            approve_tx = core_token.functions.approve(
                contract_address, stake_wei
            ).build_transaction(
                {
                    "from": entity_account.address,
                    "gas": 100000,
                    "gasPrice": web3.to_wei("20", "gwei"),
                    "nonce": web3.eth.get_transaction_count(entity_account.address),
                }
            )

            signed_approve_tx = entity_account.sign_transaction(approve_tx)
            raw_approve_tx = getattr(
                signed_approve_tx,
                "rawTransaction",
                getattr(signed_approve_tx, "raw_transaction", None),
            )
            approve_tx_hash = web3.eth.send_raw_transaction(raw_approve_tx)
            web3.eth.wait_for_transaction_receipt(approve_tx_hash)
            print(f"   ✅ Approved: {approve_tx_hash.hex()}")

            # Step 3: Register entity
            print(f"   📝 Registering {entity['type']}...")

            if entity["type"] == "miner":
                register_tx = contract.functions.registerMiner(
                    0,  # subnetId
                    stake_wei,  # coreStake
                    0,  # btcStake
                    entity["endpoint"],
                ).build_transaction(
                    {
                        "from": entity_account.address,
                        "gas": 500000,
                        "gasPrice": web3.to_wei("20", "gwei"),
                        "nonce": web3.eth.get_transaction_count(entity_account.address),
                    }
                )
            else:  # validator
                register_tx = contract.functions.registerValidator(
                    0,  # subnetId
                    stake_wei,  # coreStake
                    0,  # btcStake
                    entity["endpoint"],
                ).build_transaction(
                    {
                        "from": entity_account.address,
                        "gas": 500000,
                        "gasPrice": web3.to_wei("20", "gwei"),
                        "nonce": web3.eth.get_transaction_count(entity_account.address),
                    }
                )

            signed_register_tx = entity_account.sign_transaction(register_tx)
            raw_register_tx = getattr(
                signed_register_tx,
                "rawTransaction",
                getattr(signed_register_tx, "raw_transaction", None),
            )
            register_tx_hash = web3.eth.send_raw_transaction(raw_register_tx)
            web3.eth.wait_for_transaction_receipt(register_tx_hash)
            print(f"   ✅ Registered: {register_tx_hash.hex()}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Final network stats
    try:
        miners = contract.functions.getAllMiners().call()
        validators = contract.functions.getAllValidators().call()
        print(f"\n📊 FINAL NETWORK STATS:")
        print(f"   👥 Total Miners: {len(miners)}")
        print(f"   🛡️ Total Validators: {len(validators)}")
    except:
        print("\n📊 Could not fetch final stats")


if __name__ == "__main__":
    main()
