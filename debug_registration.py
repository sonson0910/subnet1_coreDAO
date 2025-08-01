#!/usr/bin/env python3
"""
Debug registration issues
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


def debug_registration():
    """Debug registration issues"""
    print(f"\n🔍 DEBUGGING REGISTRATION ISSUES")
    print("=" * 60)

    # Use the deployed contract address
    contract_address = "0x60d7b1A881b01D49371eaFfBE2833AE2bcd86441"
    print(f"🎯 Target contract: {contract_address}")

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

    # Check miner 2 status (the one that was registered)
    miner_2_address = "0x16102CA8BEF74fb6214AF352989b664BF0e50498"
    print(f"\n🔍 Checking Miner 2 status: {miner_2_address}")

    try:
        miner_info = contract.functions.getMinerInfo(miner_2_address).call()
        print(f"   UID: {miner_info[0].hex()}")
        print(f"   Status: {miner_info[9]} (0=Inactive, 1=Active, 2=Jailed)")
        print(f"   Already registered: {miner_info[0] != b'\\x00' * 32}")
    except Exception as e:
        print(f"   Error getting miner info: {e}")

    # Try to check if validator 1 can register
    validator_1_address = "0x25F3D6316017FDF7A4f4e54003b29212a198768f"
    validator_1_private_key = (
        "0x3ac6e82cf34e51d376395af0338d0b1162c1d39b9d34614ed40186fd2367b33d"
    )

    print(f"\n🔍 Checking Validator 1 registration status: {validator_1_address}")

    try:
        validator_info = contract.functions.getValidatorInfo(validator_1_address).call()
        print(f"   UID: {validator_info[0].hex()}")
        print(f"   Status: {validator_info[9]} (0=Inactive, 1=Active, 2=Jailed)")
        print(f"   Already registered: {validator_info[0] != b'\\x00' * 32}")
    except Exception as e:
        print(f"   Error getting validator info: {e}")

    # Check balances and allowances
    core_token_address = "0xA8cb1a72c3F946bAcACa4c9eA2648aB3A0a97b74"
    core_token_abi = [
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

    print(f"\n💰 Checking token balances and allowances for Validator 1:")
    try:
        balance = core_token.functions.balanceOf(validator_1_address).call()
        allowance = core_token.functions.allowance(
            validator_1_address, contract_address
        ).call()
        print(f"   CORE Balance: {web3.from_wei(balance, 'ether')} CORE")
        print(f"   Contract Allowance: {web3.from_wei(allowance, 'ether')} CORE")
    except Exception as e:
        print(f"   Error checking token info: {e}")

    # Try to simulate a registration call
    print(f"\n🧪 Simulating Validator 1 registration...")

    try:
        account = web3.eth.account.from_key(validator_1_private_key)
        stake_wei = web3.to_wei(0.08, "ether")

        # Try to call the function without sending transaction
        result = contract.functions.registerValidator(
            0,  # subnetId
            stake_wei,  # coreStake
            0,  # btcStake
            "http://localhost:8001",
        ).call({"from": account.address})

        print(f"   ✅ Simulation successful: {result}")

    except Exception as e:
        print(f"   ❌ Simulation failed: {e}")

    # Check gas estimation
    print(f"\n⛽ Checking gas estimation...")
    try:
        gas_estimate = contract.functions.registerValidator(
            0,  # subnetId
            stake_wei,  # coreStake
            0,  # btcStake
            "http://localhost:8001",
        ).estimate_gas({"from": account.address})

        print(f"   Estimated gas: {gas_estimate}")

    except Exception as e:
        print(f"   ❌ Gas estimation failed: {e}")


def main():
    debug_registration()


if __name__ == "__main__":
    main()
