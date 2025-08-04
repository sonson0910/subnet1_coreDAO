#!/usr/bin/env python3
"""
Debug registration issues
"""

import json
from pathlib import Path
from web3 import Web3
from eth_account import Account


def debug_registration():
    print("🔍 DEBUGGING REGISTRATION ISSUES")
    print("=" * 50)

    # Contract configuration
    contract_address = "0x594fc12B3e3AB824537b947765dd9409DAAAa143"
    core_token_address = "0x7B74e4868c8C500D6143CEa53a5d2F94e94c7637"
    rpc_url = "https://rpc.test.btcs.network"

    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    print(f"✅ Connected to Core: {w3.is_connected()}")

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

    # Check subnet status
    print("\n📊 SUBNET STATUS:")
    try:
        # Check if subnet 0 exists and registration is open
        subnet_static = contract.functions.getSubnetStaticData(0).call()
        subnet_dynamic = contract.functions.getSubnetDynamicData(0).call()

        print(f"  📍 Subnet 0 Static:")
        print(f"    net_uid: {subnet_static[0]}")
        print(f"    name: {subnet_static[1]}")
        print(f"    owner: {subnet_static[2]}")
        print(f"    created_at: {subnet_static[3]}")
        print(f"    min_stake_miner: {Web3.from_wei(subnet_static[4], 'ether')} CORE")
        print(
            f"    min_stake_validator: {Web3.from_wei(subnet_static[5], 'ether')} CORE"
        )

        print(f"\n  📈 Subnet 0 Dynamic:")
        print(f"    total_miners: {subnet_dynamic[0]}")
        print(f"    total_validators: {subnet_dynamic[1]}")
        print(f"    total_stake: {Web3.from_wei(subnet_dynamic[2], 'ether')} CORE")
        print(f"    registration_open: {subnet_dynamic[3]}")
        print(f"    last_update: {subnet_dynamic[4]}")

        if subnet_dynamic[3] == 0:
            print("  ❌ Registration is CLOSED for subnet 0")
        else:
            print("  ✅ Registration is OPEN for subnet 0")

    except Exception as e:
        print(f"  ❌ Error checking subnet: {e}")

    # Check a specific entity (miner_1)
    print("\n🔍 CHECKING SPECIFIC ENTITY:")
    entities_dir = Path("entities")
    miner_file = entities_dir / "miner_1.json"

    if miner_file.exists():
        with open(miner_file, "r") as f:
            miner = json.load(f)

        address = miner["address"]
        stake_amount = int(float(miner["stake_amount"]) * 10**18)

        print(f"  🔨 Miner Address: {address}")
        print(f"  💰 Stake Amount: {Web3.from_wei(stake_amount, 'ether')} CORE")

        # Check if already registered
        try:
            miner_data = contract.functions.getMinerData(address).call()
            print(f"  📋 Miner Data: {miner_data}")
        except Exception as e:
            print(f"  ℹ️ Miner not found (expected): {e}")

        # Check balance
        balance = w3.eth.get_balance(address)
        print(f"  💳 ETH Balance: {Web3.from_wei(balance, 'ether')} CORE")

        # Check CORE token balance
        erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function",
            }
        ]

        try:
            core_token = w3.eth.contract(address=core_token_address, abi=erc20_abi)
            token_balance = core_token.functions.balanceOf(address).call()
            print(
                f"  🪙 CORE Token Balance: {Web3.from_wei(token_balance, 'ether')} CORE"
            )
        except Exception as e:
            print(f"  ❌ Error checking token balance: {e}")

        # Check allowance
        try:
            allowance_abi = [
                {
                    "constant": True,
                    "inputs": [
                        {"name": "_owner", "type": "address"},
                        {"name": "_spender", "type": "address"},
                    ],
                    "name": "allowance",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "type": "function",
                }
            ]
            core_token_full = w3.eth.contract(
                address=core_token_address, abi=allowance_abi
            )
            allowance = core_token_full.functions.allowance(
                address, contract_address
            ).call()
            print(
                f"  📝 CORE Token Allowance: {Web3.from_wei(allowance, 'ether')} CORE"
            )
        except Exception as e:
            print(f"  ❌ Error checking allowance: {e}")

    print("\n🎯 RECOMMENDATIONS:")
    print("1. Ensure subnet 0 registration is open")
    print("2. Check minimum stake requirements")
    print("3. Verify entities have sufficient CORE tokens")
    print("4. Check gas fees and network connectivity")


if __name__ == "__main__":
    debug_registration()
