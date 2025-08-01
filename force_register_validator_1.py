#!/usr/bin/env python3
"""
FORCE REGISTER VALIDATOR 1 - NO CHECKS, JUST DO IT!
"""

import os
import sys
import json
from pathlib import Path
from web3 import Web3
from eth_account import Account


def force_register_validator_1():
    """FORCE register Validator 1 - no more checks!"""

    print("🔥 FORCE REGISTERING VALIDATOR 1 - NO MORE GAMES!")
    print("=" * 60)

    # Load validator 1 data
    with open("entities/validator_1.json", "r") as f:
        validator_data = json.load(f)

    validator_address = validator_data["address"]
    private_key = validator_data["private_key"]
    api_endpoint = validator_data["api_endpoint"]
    stake_amount = float(validator_data["stake_amount"])

    print(f"🎯 Validator 1: {validator_address}")
    print(f"🎯 Endpoint: {api_endpoint}")
    print(f"🎯 Stake: {stake_amount} CORE")

    # Web3 setup
    web3 = Web3(Web3.HTTPProvider("https://rpc.test.btcs.network"))
    print(f"✅ Web3 connected: {web3.is_connected()}")

    # Contract addresses
    contract_address = "0x60d7b1A881b01D49371eaFfBE2833AE2bcd86441"
    core_token_address = "0xA8cb1a72c3F946bAcACa4c9eA2648aB3A0a97b74"

    # Load contract ABI
    project_root = Path(__file__).parent.parent
    abi_path = (
        project_root
        / "moderntensor_aptos"
        / "mt_core"
        / "smartcontract"
        / "artifacts"
        / "contracts"
        / "ModernTensorAI_v2_Bittensor.sol"
        / "ModernTensorAI_v2_Bittensor.json"
    )

    with open(abi_path, "r") as f:
        contract_abi = json.load(f)["abi"]

    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    # Token contract
    token_abi = [
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
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function",
        },
    ]
    token = web3.eth.contract(address=core_token_address, abi=token_abi)

    # Accounts
    validator_account = Account.from_key(private_key)
    deployer_key = "0x3ace434e2cd05cd0e614eb5d423cf04e4b925c17db9869e9c598851f88f52840"
    deployer_account = Account.from_key(deployer_key)

    print(f"🔑 Validator account: {validator_account.address}")
    print(f"🔑 Deployer account: {deployer_account.address}")

    try:
        # Step 1: Check current UID (for debugging)
        print("\n🔍 Current status:")
        validator_info = contract.functions.getValidatorInfo(validator_address).call()
        current_uid = validator_info[0].hex()
        print(f"   Current UID: {current_uid}")

        # Step 2: Mint tokens (force it)
        stake_wei = web3.to_wei(stake_amount, "ether")
        mint_amount = stake_wei * 3  # Mint extra

        print(f"\n💰 Force minting {web3.from_wei(mint_amount, 'ether')} CORE...")

        mint_tx = token.functions.mint(
            validator_address, mint_amount
        ).build_transaction(
            {
                "from": deployer_account.address,
                "gas": 200000,
                "gasPrice": web3.to_wei("25", "gwei"),
                "nonce": web3.eth.get_transaction_count(deployer_account.address),
            }
        )

        signed_mint = web3.eth.account.sign_transaction(mint_tx, deployer_key)
        mint_hash = web3.eth.send_raw_transaction(signed_mint.raw_transaction)
        mint_receipt = web3.eth.wait_for_transaction_receipt(mint_hash, timeout=120)

        print(f"✅ Minted: {mint_hash.hex()} (Status: {mint_receipt.status})")

        # Step 3: Approve tokens (force it)
        print(f"\n📝 Force approving {web3.from_wei(stake_wei, 'ether')} CORE...")

        approve_tx = token.functions.approve(
            contract_address, stake_wei
        ).build_transaction(
            {
                "from": validator_address,
                "gas": 150000,
                "gasPrice": web3.to_wei("25", "gwei"),
                "nonce": web3.eth.get_transaction_count(validator_address),
            }
        )

        signed_approve = web3.eth.account.sign_transaction(approve_tx, private_key)
        approve_hash = web3.eth.send_raw_transaction(signed_approve.raw_transaction)
        approve_receipt = web3.eth.wait_for_transaction_receipt(
            approve_hash, timeout=120
        )

        print(f"✅ Approved: {approve_hash.hex()} (Status: {approve_receipt.status})")

        # Step 4: Register validator (FORCE IT!)
        print(f"\n🚀 FORCE REGISTERING VALIDATOR...")

        register_tx = contract.functions.registerValidator(
            api_endpoint, stake_wei
        ).build_transaction(
            {
                "from": validator_address,
                "gas": 500000,  # High gas limit
                "gasPrice": web3.to_wei("30", "gwei"),  # High gas price
                "nonce": web3.eth.get_transaction_count(validator_address),
            }
        )

        signed_register = web3.eth.account.sign_transaction(register_tx, private_key)
        register_hash = web3.eth.send_raw_transaction(signed_register.raw_transaction)
        register_receipt = web3.eth.wait_for_transaction_receipt(
            register_hash, timeout=180
        )

        print(
            f"🎉 REGISTERED: {register_hash.hex()} (Status: {register_receipt.status})"
        )

        # Step 5: Verify final status
        print(f"\n✅ FINAL VERIFICATION:")
        final_info = contract.functions.getValidatorInfo(validator_address).call()
        final_uid = final_info[0].hex()
        final_status = final_info[3]
        final_endpoint = final_info[2]

        print(f"   Final UID: {final_uid}")
        print(f"   Status: {final_status}")
        print(f"   Endpoint: {final_endpoint}")

        if (
            final_uid
            != "0000000000000000000000000000000000000000000000000000000000000000"
        ):
            print("🎉🎉🎉 VALIDATOR 1 SUCCESSFULLY REGISTERED! 🎉🎉🎉")
        else:
            print("❌❌❌ STILL FAILED - UID IS ZERO! ❌❌❌")

    except Exception as e:
        print(f"💥 ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    force_register_validator_1()
