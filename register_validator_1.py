#!/usr/bin/env python3
"""
Register Validator 1 to smart contract
"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from web3 import Web3
from eth_account import Account
from pathlib import Path


def register_validator_1():
    """Register Validator 1 to the smart contract"""

    print("🚀 REGISTERING VALIDATOR 1")
    print("=" * 50)

    # Load validator 1 data
    validator_1_path = "entities/validator_1.json"
    if not os.path.exists(validator_1_path):
        print(f"❌ Error: {validator_1_path} not found!")
        return

    with open(validator_1_path, "r") as f:
        validator_data = json.load(f)

    validator_address = validator_data["address"]
    private_key = validator_data["private_key"]
    api_endpoint = validator_data["api_endpoint"]
    stake_amount = float(validator_data["stake_amount"])

    print(f"✅ Loaded Validator 1:")
    print(f"   Address: {validator_address}")
    print(f"   Endpoint: {api_endpoint}")
    print(f"   Stake: {stake_amount} CORE")

    try:
        # Web3 setup
        rpc_url = "https://rpc.test.btcs.network"
        web3 = Web3(Web3.HTTPProvider(rpc_url))

        if not web3.is_connected():
            print("❌ Failed to connect to Core network")
            return

        print("✅ Connected to Core network")

        # Contract addresses from the updated system
        contract_address = "0x5f96BEA61E4ad2222c4B575fD6FFdCEd4DC04358"
core_token_address = "0x1361F20937a69aA841a37Ca943948463b8E6740C"

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

        # Create account from private key
        account = Account.from_key(private_key)
        print(f"✅ Account loaded: {account.address}")

        # Check if already registered
        print("\n🔍 Checking registration status...")
        try:
            validator_info = contract.functions.getValidatorInfo(
                validator_address
            ).call()
            uid_bytes = validator_info[0]
            uid_hex = uid_bytes.hex()

            print(f"   📋 Current UID: {uid_hex}")
            print(f"   📋 UID bytes: {uid_bytes}")
            print(f"   📋 Is zero UID: {uid_bytes == b'\\x00' * 32}")

            # Check if UID is non-zero (properly registered)
            if (
                uid_bytes != b"\\x00" * 32
                and uid_hex
                != "0000000000000000000000000000000000000000000000000000000000000000"
            ):
                print("⚠️ Validator 1 already registered!")
                print(f"   UID: {uid_hex}")
                print(f"   Status: {validator_info[3]}")
                print(f"   Endpoint: {validator_info[2]}")
                return
        except Exception as e:
            print(f"   🔍 Checking registration: {e}")

        print("📝 Validator 1 not registered, proceeding with registration...")

        # Setup token contract
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
        ]
        core_token = web3.eth.contract(address=core_token_address, abi=core_token_abi)

        # Use deployer account for minting
        deployer_private_key = (
            "0x3ace434e2cd05cd0e614eb5d423cf04e4b925c17db9869e9c598851f88f52840"
        )
        deployer_account = Account.from_key(deployer_private_key)
        print(f"🔑 Using deployer account: {deployer_account.address}")

        # Check current balance and mint if needed
        stake_wei = web3.to_wei(stake_amount, "ether")
        current_balance = core_token.functions.balanceOf(validator_address).call()

        print(f"💰 Current balance: {web3.from_wei(current_balance, 'ether')} CORE")
        print(f"💰 Required stake: {stake_amount} CORE")

        if current_balance < stake_wei:
            needed_amount = stake_wei * 2  # Mint 2x to be safe
            print(f"🏭 Minting {web3.from_wei(needed_amount, 'ether')} CORE tokens...")

            mint_tx = core_token.functions.mint(
                validator_address, needed_amount
            ).build_transaction(
                {
                    "from": deployer_account.address,
                    "gas": 100000,
                    "gasPrice": web3.to_wei("20", "gwei"),
                    "nonce": web3.eth.get_transaction_count(deployer_account.address),
                }
            )

            signed_mint = web3.eth.account.sign_transaction(
                mint_tx, deployer_private_key
            )
            mint_hash = web3.eth.send_raw_transaction(signed_mint.raw_transaction)
            mint_receipt = web3.eth.wait_for_transaction_receipt(mint_hash, timeout=60)

            if mint_receipt.status == 1:
                print(f"✅ Minted tokens successfully: {mint_hash.hex()}")
            else:
                print(f"❌ Mint transaction failed!")
                return

        # Approve contract to spend tokens
        print("\n📝 Approving token spending...")
        approve_tx = core_token.functions.approve(
            contract_address, stake_wei
        ).build_transaction(
            {
                "from": validator_address,
                "gas": 100000,
                "gasPrice": web3.to_wei("20", "gwei"),
                "nonce": web3.eth.get_transaction_count(validator_address),
            }
        )

        signed_approve = web3.eth.account.sign_transaction(approve_tx, private_key)
        approve_hash = web3.eth.send_raw_transaction(signed_approve.raw_transaction)
        approve_receipt = web3.eth.wait_for_transaction_receipt(
            approve_hash, timeout=60
        )

        if approve_receipt.status == 1:
            print(f"✅ Approved token spending: {approve_hash.hex()}")
        else:
            print(f"❌ Approve transaction failed!")
            return

        # Register validator
        print("\n📋 Registering validator...")
        register_tx = contract.functions.registerValidator(
            api_endpoint, stake_wei
        ).build_transaction(
            {
                "from": validator_address,
                "gas": 300000,
                "gasPrice": web3.to_wei("20", "gwei"),
                "nonce": web3.eth.get_transaction_count(validator_address),
            }
        )

        signed_register = web3.eth.account.sign_transaction(register_tx, private_key)
        register_hash = web3.eth.send_raw_transaction(signed_register.raw_transaction)
        register_receipt = web3.eth.wait_for_transaction_receipt(
            register_hash, timeout=60
        )

        if register_receipt.status == 1:
            print(f"✅ Validator registered: {register_hash.hex()}")
        else:
            print(f"❌ Registration transaction failed!")
            return

        # Verify registration
        print("\n✅ Verifying registration...")
        validator_info = contract.functions.getValidatorInfo(validator_address).call()

        if validator_info[0] != b"\\x00" * 32:
            print("🎉 VALIDATOR 1 REGISTRATION SUCCESSFUL!")
            print(f"   UID: {validator_info[0].hex()}")
            print(f"   Status: {validator_info[3]}")
            print(f"   Endpoint: {validator_info[2]}")
        else:
            print("❌ Registration verification failed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    register_validator_1()
