#!/usr/bin/env python3
"""
Register Validator 2 specifically
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


def register_validator_2():
    """Register Validator 2 specifically"""
    print(f"\n🛡️ REGISTERING VALIDATOR 2")
    print("=" * 60)

    # Use the deployed contract address
    contract_address = "0x60d7b1A881b01D49371eaFfBE2833AE2bcd86441"
    core_token_address = "0xA8cb1a72c3F946bAcACa4c9eA2648aB3A0a97b74"

    print(f"🎯 Target contract: {contract_address}")
    print(f"🪙 CORE token: {core_token_address}")

    # Load validator 2 data
    validator_2_file = Path(__file__).parent / "entities" / "validator_2.json"
    with open(validator_2_file, "r") as f:
        validator_2 = json.load(f)

    print(f"📄 Loaded Validator 2: {validator_2['name']}")
    print(f"   Address: {validator_2['address']}")
    print(f"   Endpoint: {validator_2.get('api_endpoint', 'N/A')}")

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

    # Use deployer account (miner 2) to mint tokens
    deployer_private_key = (
        "0x3ace434e2cd05cd0e614eb5d423cf04e4b925c17db9869e9c598851f88f52840"
    )
    deployer_account = web3.eth.account.from_key(deployer_private_key)
    print(f"🔑 Using deployer account for minting: {deployer_account.address}")

    try:
        # Check if already registered
        try:
            validator_info = contract.functions.getValidatorInfo(
                validator_2["address"]
            ).call()
            if validator_info[0] != b"\x00" * 32:  # Non-zero UID means registered
                print(f"   ✅ Already registered with UID: {validator_info[0].hex()}")
                return True
        except Exception as e:
            print(f"   🔍 Checking registration status: {e}")

        # Create account from private key
        private_key = validator_2["private_key"]
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key

        account = web3.eth.account.from_key(private_key)

        if account.address.lower() != validator_2["address"].lower():
            print(f"   ❌ Private key doesn't match address!")
            return False

        # Check current balance and mint if needed
        current_balance = core_token.functions.balanceOf(account.address).call()
        stake_wei = web3.to_wei(float(validator_2["stake_amount"]), "ether")

        print(f"   💰 Current balance: {web3.from_wei(current_balance, 'ether')} CORE")
        print(f"   💰 Required stake: {validator_2['stake_amount']} CORE")

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
                    "nonce": web3.eth.get_transaction_count(deployer_account.address),
                }
            )

            signed_mint = web3.eth.account.sign_transaction(
                mint_tx, deployer_private_key
            )
            mint_hash = web3.eth.send_raw_transaction(signed_mint.raw_transaction)
            mint_receipt = web3.eth.wait_for_transaction_receipt(mint_hash, timeout=60)

            if mint_receipt.status == 1:
                print(f"   ✅ Minted tokens successfully")
            else:
                print(f"   ❌ Failed to mint tokens")
                return False

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
            return False

        print(f"   ✅ Approved {validator_2['stake_amount']} CORE")

        # Register validator
        print("   🛡️ Registering validator...")
        tx_data = contract.functions.registerValidator(
            0,  # subnetId
            stake_wei,  # coreStake
            0,  # btcStake
            validator_2.get("api_endpoint", "http://localhost:8002"),
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
            print(f"   ✅ Validator 2 registered successfully!")

            # Get the new validator info
            validator_info = contract.functions.getValidatorInfo(
                validator_2["address"]
            ).call()
            print(f"   🎯 New UID: {validator_info[0].hex()}")
            print(f"   🎯 Status: {validator_info[9]} (1=Active)")
            print(f"   🎯 Endpoint: {validator_info[11]}")

            return True
        else:
            print(f"   ❌ Transaction failed")
            return False

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Main function"""
    print("🛡️ VALIDATOR 2 REGISTRATION")
    print("=" * 40)

    success = register_validator_2()

    if success:
        print(f"\n🎉 SUCCESS! VALIDATOR 2 REGISTERED!")
        print(f"🎯 Contract: 0x60d7b1A881b01D49371eaFfBE2833AE2bcd86441")
        print(f"🔍 Verify: python test_metagraph_integration.py")
        print(f"🚀 Start: python scripts/run_validator_core_v2.py")
    else:
        print(f"\n❌ FAILED TO REGISTER VALIDATOR 2")

    return success


if __name__ == "__main__":
    main()
