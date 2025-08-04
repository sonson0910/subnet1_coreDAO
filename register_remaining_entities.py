#!/usr/bin/env python3
"""
Register remaining entities with correct parameters
"""

import json
from pathlib import Path
from web3 import Web3
from eth_account import Account


def register_remaining_entities():
    print("🚀 REGISTERING REMAINING ENTITIES")
    print("=" * 45)

    # Configuration - using working parameters
    contract_address = "0x594fc12B3e3AB824537b947765dd9409DAAAa143"
    core_token_address = "0x7B74e4868c8C500D6143CEa53a5d2F94e94c7637"
    rpc_url = "https://rpc.test.btcs.network"

    # WORKING PARAMETERS (discovered from successful registration)
    subnet_id = 1  # Use subnet 1
    stake_amount = int(0.01 * 10**18)  # 0.01 CORE minimum

    print(
        f"🎯 Using: Subnet {subnet_id}, Stake {Web3.from_wei(stake_amount, 'ether')} CORE"
    )

    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    # Load contract ABI
    try:
        abi_path = "../moderntensor_aptos/mt_core/smartcontract/artifacts/contracts/ModernTensor.sol/ModernTensor.json"
        with open(abi_path, "r") as f:
            contract_data = json.load(f)
            contract_abi = contract_data["abi"]
    except Exception as e:
        print(f"❌ Error loading contract ABI: {e}")
        return False

    # Create contract instance
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    print("✅ Contract loaded")

    # ERC20 ABI for approval
    erc20_abi = [
        {
            "constant": False,
            "inputs": [
                {"name": "_spender", "type": "address"},
                {"name": "_value", "type": "uint256"},
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function",
        }
    ]
    core_token = w3.eth.contract(address=core_token_address, abi=erc20_abi)

    # Load entities
    entities_dir = Path("entities")

    # Load miners (skip miner_1 since it's already registered)
    miners = []
    for i in range(2, 3):  # Only miner_2
        miner_file = entities_dir / f"miner_{i}.json"
        if miner_file.exists():
            with open(miner_file, "r") as f:
                miners.append(json.load(f))

    # Load validators
    validators = []
    for i in range(1, 4):  # All 3 validators
        validator_file = entities_dir / f"validator_{i}.json"
        if validator_file.exists():
            with open(validator_file, "r") as f:
                validators.append(json.load(f))

    print(
        f"📋 Found {len(miners)} remaining miners and {len(validators)} validators to register"
    )

    success_count = 0
    total_count = len(miners) + len(validators)

    # Register remaining miners
    if miners:
        print(f"\n🔨 REGISTERING REMAINING MINERS:")
        for i, miner in enumerate(miners):
            address = miner["address"]
            private_key = miner["private_key"]
            api_endpoint = miner["api_endpoint"]

            print(f"\nMiner {i+2}: {address}")  # +2 because we skip miner_1

            try:
                # Approve tokens
                nonce = w3.eth.get_transaction_count(address)

                approve_txn = core_token.functions.approve(
                    contract_address, stake_amount
                ).build_transaction(
                    {
                        "from": address,
                        "nonce": nonce,
                        "gas": 100000,
                        "gasPrice": w3.to_wei("50", "gwei"),
                    }
                )

                signed_approve = w3.eth.account.sign_transaction(
                    approve_txn, private_key
                )
                approve_hash = w3.eth.send_raw_transaction(
                    signed_approve.raw_transaction
                )
                w3.eth.wait_for_transaction_receipt(approve_hash, timeout=60)
                print(f"  ✅ Tokens approved")

                # Register miner
                nonce = w3.eth.get_transaction_count(address)

                register_txn = contract.functions.registerMiner(
                    subnet_id, stake_amount, 0, api_endpoint  # bitcoin stake
                ).build_transaction(
                    {
                        "from": address,
                        "nonce": nonce,
                        "gas": 500000,
                        "gasPrice": w3.to_wei("50", "gwei"),
                    }
                )

                signed_register = w3.eth.account.sign_transaction(
                    register_txn, private_key
                )
                register_hash = w3.eth.send_raw_transaction(
                    signed_register.raw_transaction
                )

                print(f"  📡 Registration sent: {register_hash.hex()}")
                receipt = w3.eth.wait_for_transaction_receipt(
                    register_hash, timeout=120
                )

                if receipt.status == 1:
                    print(f"  🎉 MINER REGISTERED SUCCESSFULLY!")
                    success_count += 1
                else:
                    print(f"  ❌ Registration failed")

            except Exception as e:
                print(f"  ❌ Error: {e}")

    # Register validators
    if validators:
        print(f"\n✅ REGISTERING VALIDATORS:")
        for i, validator in enumerate(validators):
            address = validator["address"]
            private_key = validator["private_key"]
            api_endpoint = validator["api_endpoint"]

            print(f"\nValidator {i+1}: {address}")

            try:
                # Approve tokens
                nonce = w3.eth.get_transaction_count(address)

                approve_txn = core_token.functions.approve(
                    contract_address, stake_amount
                ).build_transaction(
                    {
                        "from": address,
                        "nonce": nonce,
                        "gas": 100000,
                        "gasPrice": w3.to_wei("50", "gwei"),
                    }
                )

                signed_approve = w3.eth.account.sign_transaction(
                    approve_txn, private_key
                )
                approve_hash = w3.eth.send_raw_transaction(
                    signed_approve.raw_transaction
                )
                w3.eth.wait_for_transaction_receipt(approve_hash, timeout=60)
                print(f"  ✅ Tokens approved")

                # Register validator
                nonce = w3.eth.get_transaction_count(address)

                register_txn = contract.functions.registerValidator(
                    subnet_id, stake_amount, 0, api_endpoint  # bitcoin stake
                ).build_transaction(
                    {
                        "from": address,
                        "nonce": nonce,
                        "gas": 500000,
                        "gasPrice": w3.to_wei("50", "gwei"),
                    }
                )

                signed_register = w3.eth.account.sign_transaction(
                    register_txn, private_key
                )
                register_hash = w3.eth.send_raw_transaction(
                    signed_register.raw_transaction
                )

                print(f"  📡 Registration sent: {register_hash.hex()}")
                receipt = w3.eth.wait_for_transaction_receipt(
                    register_hash, timeout=120
                )

                if receipt.status == 1:
                    print(f"  🎉 VALIDATOR REGISTERED SUCCESSFULLY!")
                    success_count += 1
                else:
                    print(f"  ❌ Registration failed")

            except Exception as e:
                print(f"  ❌ Error: {e}")

    # Final status
    print(f"\n📊 REGISTRATION SUMMARY:")
    print(f"  ✅ Successful: {success_count}/{total_count}")
    print(f"  🎯 Success Rate: {success_count/total_count*100:.1f}%")

    # Check final network stats
    try:
        network_stats = contract.functions.getNetworkStats().call()
        print(f"\n🌐 FINAL NETWORK STATUS:")
        print(f"  👥 Total Miners: {network_stats[0]}")
        print(f"  🛡️ Total Validators: {network_stats[1]}")
        print(f"  💰 Total Staked: {Web3.from_wei(network_stats[2], 'ether')} CORE")

        if network_stats[0] >= 2 and network_stats[1] >= 2:
            print(f"\n🎉 NETWORK READY FOR OPERATION!")
            print(f"✅ Sufficient entities registered")
            print(f"✅ Ready to start consensus")
        else:
            print(f"\n⚠️ Network needs more entities:")
            print(f"   Miners: {network_stats[0]}/2")
            print(f"   Validators: {network_stats[1]}/2")

    except Exception as e:
        print(f"❌ Error checking network stats: {e}")

    return success_count == total_count


if __name__ == "__main__":
    register_remaining_entities()
