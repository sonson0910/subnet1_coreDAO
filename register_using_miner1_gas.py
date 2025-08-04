#!/usr/bin/env python3

import os
import sys
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import json
from dotenv import load_dotenv

load_dotenv()


def main():
    print("🚀 REGISTER USING MINER 1 AS GAS SPONSOR")
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

    # Miner 1 account (has 0.1 native CORE)
    miner1_private_key = os.getenv("MINER_1_PRIVATE_KEY")
    miner1_account = web3.eth.account.from_key(miner1_private_key)

    print(
        f"💰 Miner 1 balance: {web3.from_wei(web3.eth.get_balance(miner1_account.address), 'ether')} CORE"
    )

    # Step 1: Register Miner 1 first (it has gas)
    print(f"\n🔧 Step 1: Register Miner 1...")
    try:
        # Approve
        stake_wei = web3.to_wei("0.05", "ether")
        approve_tx = core_token.functions.approve(
            contract_address, stake_wei
        ).build_transaction(
            {
                "from": miner1_account.address,
                "gas": 100000,
                "gasPrice": web3.to_wei("20", "gwei"),
                "nonce": web3.eth.get_transaction_count(miner1_account.address),
            }
        )

        signed_approve_tx = miner1_account.sign_transaction(approve_tx)
        raw_approve_tx = getattr(
            signed_approve_tx,
            "rawTransaction",
            getattr(signed_approve_tx, "raw_transaction", None),
        )
        approve_tx_hash = web3.eth.send_raw_transaction(raw_approve_tx)
        web3.eth.wait_for_transaction_receipt(approve_tx_hash)
        print(f"   ✅ Approved: {approve_tx_hash.hex()}")

        # Register
        register_tx = contract.functions.registerMiner(
            0,  # subnetId
            stake_wei,  # coreStake
            0,  # btcStake
            "http://localhost:8101",
        ).build_transaction(
            {
                "from": miner1_account.address,
                "gas": 500000,
                "gasPrice": web3.to_wei("20", "gwei"),
                "nonce": web3.eth.get_transaction_count(miner1_account.address),
            }
        )

        signed_register_tx = miner1_account.sign_transaction(register_tx)
        raw_register_tx = getattr(
            signed_register_tx,
            "rawTransaction",
            getattr(signed_register_tx, "raw_transaction", None),
        )
        register_tx_hash = web3.eth.send_raw_transaction(raw_register_tx)
        web3.eth.wait_for_transaction_receipt(register_tx_hash)
        print(f"   ✅ Registered: {register_tx_hash.hex()}")

    except Exception as e:
        print(f"   ❌ Error registering Miner 1: {e}")
        return

    # Step 2: Send gas to other entities
    print(f"\n🔧 Step 2: Send gas to other entities...")
    remaining_entities = [
        ("Miner 2", os.getenv("MINER_2_ADDRESS")),
        ("Validator 1", os.getenv("VALIDATOR_1_ADDRESS")),
        ("Validator 2", os.getenv("VALIDATOR_2_ADDRESS")),
    ]

    # Send 0.02 CORE to each for gas
    gas_amount = web3.to_wei("0.02", "ether")

    for name, address in remaining_entities:
        try:
            print(f"   💸 Sending gas to {name}...")

            gas_tx = {
                "to": address,
                "value": gas_amount,
                "gas": 21000,
                "gasPrice": web3.to_wei("20", "gwei"),
                "nonce": web3.eth.get_transaction_count(miner1_account.address),
            }

            signed_gas_tx = miner1_account.sign_transaction(gas_tx)
            raw_gas_tx = getattr(
                signed_gas_tx,
                "rawTransaction",
                getattr(signed_gas_tx, "raw_transaction", None),
            )
            gas_tx_hash = web3.eth.send_raw_transaction(raw_gas_tx)
            web3.eth.wait_for_transaction_receipt(gas_tx_hash)
            print(f"   ✅ Gas sent: {gas_tx_hash.hex()}")

        except Exception as e:
            print(f"   ❌ Error sending gas to {name}: {e}")

    # Step 3: Register remaining entities
    print(f"\n🔧 Step 3: Register remaining entities...")

    remaining_entity_configs = [
        {
            "type": "miner",
            "name": "Miner 2",
            "private_key": os.getenv("MINER_2_PRIVATE_KEY"),
            "stake": "0.05",
            "endpoint": "http://localhost:8102",
        },
        {
            "type": "validator",
            "name": "Validator 1",
            "private_key": os.getenv("VALIDATOR_1_PRIVATE_KEY"),
            "stake": "0.08",
            "endpoint": "http://localhost:8001",
        },
        {
            "type": "validator",
            "name": "Validator 2",
            "private_key": os.getenv("VALIDATOR_2_PRIVATE_KEY"),
            "stake": "0.08",
            "endpoint": "http://localhost:8002",
        },
    ]

    for entity in remaining_entity_configs:
        try:
            print(f"   🔧 Registering {entity['name']}...")

            entity_account = web3.eth.account.from_key(entity["private_key"])
            stake_wei = web3.to_wei(entity["stake"], "ether")

            # Approve
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
            print(f"     ✅ Approved: {approve_tx_hash.hex()}")

            # Register
            if entity["type"] == "miner":
                register_tx = contract.functions.registerMiner(
                    0, stake_wei, 0, entity["endpoint"]
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
                    0, stake_wei, 0, entity["endpoint"]
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
            print(f"     ✅ Registered: {register_tx_hash.hex()}")

        except Exception as e:
            print(f"     ❌ Error registering {entity['name']}: {e}")

    # Final stats
    try:
        miners = contract.functions.getAllMiners().call()
        validators = contract.functions.getAllValidators().call()
        print(f"\n🎉 REGISTRATION COMPLETE!")
        print(f"   👥 Total Miners: {len(miners)}")
        print(f"   🛡️ Total Validators: {len(validators)}")
        print(f"   📋 Miners: {miners}")
        print(f"   📋 Validators: {validators}")
    except Exception as e:
        print(f"\n❌ Error fetching final stats: {e}")


if __name__ == "__main__":
    main()
