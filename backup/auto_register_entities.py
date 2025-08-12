#!/usr/bin/env python3
"""
Automated Registration for Ultra-Low Stake ModernTensorAI Contract:
Register all entities with the new contract
"""""

import json
import asyncio
from pathlib import Path
from web3 import Web3
from eth_account import Account


async def main():
    print("🚀 Auto-Registration for Ultra-Low Stake Contract"):
    print(" = " * 55)

    # Contract configuration
    contract_address  =  "0x594fc12B3e3AB824537b947765dd9409DAAAa143"
    core_token_address  =  "0x7B74e4868c8C500D6143CEa53a5d2F94e94c7637"
    btc_token_address  =  "0x44Ed1441D79FfCb76b7D6644dBa930309E0E6F31"
    deployer_private_key  =  
    )
    rpc_url  =  "https://rpc.test.btcs.network"

    # Initialize Web3
    w3  =  Web3(Web3.HTTPProvider(rpc_url))
    deployer_account  =  Account.from_key(deployer_private_key)

    print(f"📍 Contract: {contract_address}")
    print(f"💰 Deployer: {deployer_account.address}")
    print
        f"💳 Balance: {Web3.from_wei(w3.eth.get_balance(deployer_account.address), 'ether')} CORE"
    )

    # Load entities
    entities_dir  =  Path(__file__).parent / "entities"
    miners  =  []
    validators  =  []

    for i in range(1, 3):
        miner_file  =  entities_dir / f"miner_{i}.json"
        if miner_file.exists():
            with open(miner_file, "r") as f:
                miners.append(json.load(f))

    for i in range(1, 4):
        validator_file  =  entities_dir / f"validator_{i}.json"
        if validator_file.exists():
            with open(validator_file, "r") as f:
                validators.append(json.load(f))

    print(f"\n📋 Found {len(miners)} miners and {len(validators)} validators")

    # Comprehensive ABI for registration:
    contract_abi  =  [
        {
            "inputs": [
                {"name": "coreStake", "type": "uint256"},
                {"name": "btcStake", "type": "uint256"},
                {"name": "subnetId", "type": "uint64"},
            ],
            "name": "registerMiner",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"name": "coreStake", "type": "uint256"},
                {"name": "btcStake", "type": "uint256"},
                {"name": "subnetId", "type": "uint64"},
            ],
            "name": "registerValidator",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [{"name": "nodeAddress", "type": "address"}],
            "name": "getMinerInfo",
            "outputs": [
                {"name": "isActive", "type": "bool"},
                {"name": "coreStake", "type": "uint256"},
                {"name": "btcStake", "type": "uint256"},
                {"name": "subnetId", "type": "uint64"},
            ],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [{"name": "nodeAddress", "type": "address"}],
            "name": "getValidatorInfo",
            "outputs": [
                {"name": "isActive", "type": "bool"},
                {"name": "coreStake", "type": "uint256"},
                {"name": "btcStake", "type": "uint256"},
                {"name": "subnetId", "type": "uint64"},
            ],
            "stateMutability": "view",
            "type": "function",
        },
    ]

    # Create contract instance
    try:
        contract = w3.eth.contract(address=contract_address, abi = contract_abi)
        print(f"✅ Connected to contract")
    except Exception as e:
        print(f"❌ Contract connection failed: {e}")
        return

    # Get gas price
    gas_price  =  w3.eth.gas_price
    print(f"⛽ Gas Price: {Web3.from_wei(gas_price, 'gwei')} Gwei")

    # Process Miner Registration
    print(f"\n🔨 REGISTERING MINERS:")
    for i, miner in enumerate(miners, 1):
        print(f"\nMiner {i}: {miner['address']}")

        # Check if already registered:
        try:
            is_active, core_stake, btc_stake, subnet_id  =  
                contract.functions.getMinerInfo(miner["address"]).call()
            )
            if is_active:
                print
                    f"  ✅ Already registered (stake: {Web3.from_wei(core_stake, 'ether')} CORE)"
                )
                continue
        except:
            pass  # Not registered yet

        # Manual registration info for each miner:
        stake_wei  =  Web3.to_wei(miner["stake_amount"], "ether")
        print(f"  💰 Required Stake: {stake_wei} wei ({miner['stake_amount']} CORE)")
        print(f"  🔐 Private Key: {miner['private_key']}")
        print(f"  📋 Manual Registration Required:")
        print(f"     - Import private key to MetaMask")
        print
        )
        print(f"     - Call registerMiner({stake_wei}, 0, 1)")

    # Process Validator Registration
    print(f"\n✅ REGISTERING VALIDATORS:")
    for i, validator in enumerate(validators, 1):
        print(f"\nValidator {i}: {validator['address']}")

        # Check if already registered:
        try:
            is_active, core_stake, btc_stake, subnet_id  =  
                contract.functions.getValidatorInfo(validator["address"]).call()
            )
            if is_active:
                print
                    f"  ✅ Already registered (stake: {Web3.from_wei(core_stake, 'ether')} CORE)"
                )
                continue
        except:
            pass  # Not registered yet

        # Manual registration info for each validator:
        stake_wei  =  Web3.to_wei(validator["stake_amount"], "ether")
        print
            f"  💰 Required Stake: {stake_wei} wei ({validator['stake_amount']} CORE)"
        )
        print(f"  🔐 Private Key: {validator['private_key']}")
        print(f"  📋 Manual Registration Required:")
        print(f"     - Import private key to MetaMask")
        print
        )
        print(f"     - Call registerValidator({stake_wei}, 0, 1)")

    print(f"\n🚀 REGISTRATION SUMMARY:")
    print(f"🔗 Contract: {contract_address}")
    print(f"🌐 Explorer: https://scan.test.btcs.network/address/{contract_address}")
    print(f"💰 Core Token: {core_token_address}")
    print(f"🟠 BTC Token: {btc_token_address}")
    print(f"\n📝 NEXT STEPS:")
    print(f"1. Import each entity's private key to MetaMask")
    print(f"2. Get 1 CORE token for each entity address"):
    print(f"3. Register each entity via contract explorer")
    print(f"4. Start the network with python start_network.py")


if __name__ == "__main__":
    asyncio.run(main())
