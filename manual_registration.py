#!/usr/bin/env python3
"""
Manual Registration with ModernTensorAI Smart Contract
Register generated entities with the deployed contract
"""

import json
import sys
from pathlib import Path
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import os


def load_entities():
    """Load generated entities from files"""
    entities_dir = Path(__file__).parent / "entities"

    miners = []
    validators = []

    # Load miners
    for i in range(1, 3):
        miner_file = entities_dir / f"miner_{i}.json"
        if miner_file.exists():
            with open(miner_file, "r") as f:
                miners.append(json.load(f))

    # Load validators
    for i in range(1, 4):
        validator_file = entities_dir / f"validator_{i}.json"
        if validator_file.exists():
            with open(validator_file, "r") as f:
                validators.append(json.load(f))

    return miners, validators


def main():
    print("🔄 Manual Registration with ModernTensorAI")
    print("=" * 50)

    # Load environment
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # Contract configuration
    contract_address = "0x594fc12B3e3AB824537b947765dd9409DAAAa143"
    rpc_url = "https://rpc.test.btcs.network"
    deployer_private_key = (
        "a07b6e0db803f9a21ffd1001c76b0aa0b313aaba8faab8c771af47301c4452b4"
    )

    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    if not w3.is_connected():
        print("❌ Failed to connect to Core testnet")
        return

    print(f"✅ Connected to Core testnet")

    # Setup deployer account
    deployer_account = Account.from_key(deployer_private_key)
    balance = w3.eth.get_balance(deployer_account.address)

    print(f"📍 Deployer: {deployer_account.address}")
    print(f"💰 Balance: {Web3.from_wei(balance, 'ether')} CORE")

    if balance == 0:
        print("❌ Insufficient balance for registration")
        return

    # Load entities
    miners, validators = load_entities()

    if not miners and not validators:
        print("❌ No entities found. Run quick_setup_entities.py first")
        return

    print(f"\n📋 Found {len(miners)} miners and {len(validators)} validators")

    # Display entities
    if miners:
        print("\n🔨 Miners:")
        for i, miner in enumerate(miners, 1):
            print(f"  {i}. {miner['name']}: {miner['address'][:10]}...")

    if validators:
        print("\n✅ Validators:")
        for i, validator in enumerate(validators, 1):
            print(f"  {i}. {validator['name']}: {validator['address'][:10]}...")

    # Manual registration steps
    print(f"\n🔧 Manual Registration Steps:")
    print(f"1. Contract Address: {contract_address}")
    print(f"2. Use Core testnet scanner: https://scan.test.btcs.network")
    print(f"3. Connect deployer wallet: {deployer_account.address}")
    print(f"4. Call contract functions manually or use Web3 console")

    # Generate sample Web3 calls
    print(f"\n💻 Sample Web3 Registration Calls:")

    if miners:
        print("# Register Miners:")
        for miner in miners:
            stake_wei = Web3.to_wei(miner["stake_amount"], "ether")
            print(f"# Miner: {miner['name']}")
            print(
                f"registerMiner('{miner['address']}', 1, {stake_wei}, '{miner['api_endpoint']}')"
            )
            print()

    if validators:
        print("# Register Validators:")
        for validator in validators:
            stake_wei = Web3.to_wei(validator["stake_amount"], "ether")
            print(f"# Validator: {validator['name']}")
            print(
                f"registerValidator('{validator['address']}', 1, {stake_wei}, '{validator['api_endpoint']}')"
            )
            print()

    # Create registration script
    reg_script = Path(__file__).parent / "auto_register.py"

    script_content = f'''#!/usr/bin/env python3
"""Auto-generated registration script"""

from web3 import Web3
from eth_account import Account

# Configuration
RPC_URL = "{rpc_url}"
CONTRACT_ADDRESS = "{contract_address}"
DEPLOYER_KEY = "{deployer_private_key}"

# Initialize
w3 = Web3(Web3.HTTPProvider(RPC_URL))
deployer = Account.from_key(DEPLOYER_KEY)

print("🔄 Auto Registration Starting...")
print(f"Contract: {{CONTRACT_ADDRESS}}")
print(f"Deployer: {{deployer.address}}")

# Check balance
balance = w3.eth.get_balance(deployer.address)
print(f"Balance: {{Web3.from_wei(balance, 'ether')}} CORE")

if balance < Web3.to_wei('0.1', 'ether'):
    print("❌ Insufficient balance")
    exit(1)

# TODO: Add actual contract calls here
print("✅ Ready for registration")
print("⚠️  Implement contract ABI and function calls")
'''

    with open(reg_script, "w") as f:
        f.write(script_content)

    print(f"📝 Created registration template: {reg_script}")

    # Save registration summary
    summary = {
        "contract_address": contract_address,
        "deployer_address": deployer_account.address,
        "miners": len(miners),
        "validators": len(validators),
        "total_entities": len(miners) + len(validators),
        "registration_ready": True,
    }

    summary_file = Path(__file__).parent / "registration_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n🎯 Next Steps:")
    print(f"1. Visit: https://scan.test.btcs.network/address/{contract_address}")
    print(f"2. Connect wallet: {deployer_account.address}")
    print(f"3. Call registration functions manually")
    print(f"4. Or implement auto_register.py with contract ABI")
    print(f"5. Start validators/miners once registered")


if __name__ == "__main__":
    main()
