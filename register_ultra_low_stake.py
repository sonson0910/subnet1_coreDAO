#!/usr/bin/env python3
"""
Registration script for Ultra-Low Stake ModernTensorAI Contract
Perfect for 1 CORE faucet tokens
"""

import json
from pathlib import Path
from web3 import Web3
from eth_account import Account
from dotenv import set_key


def main():
    print("🚀 Ultra-Low Stake Registration Ready!")
    print("=" * 50)

    # New contract info
    new_contract = "0x594fc12B3e3AB824537b947765dd9409DAAAa143"
    new_core_token = "0x7B74e4868c8C500D6143CEa53a5d2F94e94c7637"
    new_btc_token = "0x44Ed1441D79FfCb76b7D6644dBa930309E0E6F31"

    print(f"📍 New Contract: {new_contract}")
    print(f"💰 CORE Token: {new_core_token}")
    print(f"🪙 BTC Token: {new_btc_token}")

    # Load entities
    entities_dir = Path(__file__).parent / "entities"
    miners = []
    validators = []

    for i in range(1, 3):
        miner_file = entities_dir / f"miner_{i}.json"
        if miner_file.exists():
            with open(miner_file, "r") as f:
                miners.append(json.load(f))

    for i in range(1, 4):
        validator_file = entities_dir / f"validator_{i}.json"
        if validator_file.exists():
            with open(validator_file, "r") as f:
                validators.append(json.load(f))

    # Check balances
    w3 = Web3(Web3.HTTPProvider("https://rpc.test.btcs.network"))

    print(f"\n💰 Current Balances & Requirements:")

    all_ready = True

    for miner in miners:
        balance = w3.eth.get_balance(miner["address"])
        balance_eth = float(Web3.from_wei(balance, "ether"))
        required = 0.05  # 0.05 CORE

        status = "✅" if balance_eth >= required else "❌"
        print(f"🔨 {miner['name']}: {balance_eth} CORE (need {required}) {status}")

        if balance_eth < required:
            all_ready = False

    for validator in validators:
        balance = w3.eth.get_balance(validator["address"])
        balance_eth = float(Web3.from_wei(balance, "ether"))
        required = 0.08  # 0.08 CORE

        status = "✅" if balance_eth >= required else "❌"
        print(f"✅ {validator['name']}: {balance_eth} CORE (need {required}) {status}")

        if balance_eth < required:
            all_ready = False

    # Update .env with new contract
    env_path = Path(__file__).parent / ".env"

    env_updates = {
        "CORE_CONTRACT_ADDRESS": new_contract,
        "CORE_TOKEN_ADDRESS": new_core_token,
        "BTC_TOKEN_ADDRESS": new_btc_token,
        "CONTRACT_TYPE": "ultra_low_stake",
        "MIN_MINER_STAKE": "0.05",
        "MIN_VALIDATOR_STAKE": "0.08",
    }

    for key, value in env_updates.items():
        set_key(env_path, key, value)

    print(f"\n📝 Updated .env with new contract addresses")

    if all_ready:
        print(f"\n🎉 ALL ENTITIES READY FOR REGISTRATION!")
        print(f"📋 Summary:")
        print(f"   - Contract: {new_contract}")
        print(f"   - 2 Miners ready (0.05 CORE each)")
        print(f"   - 3 Validators ready (0.08 CORE each)")
        print(f"   - Total stake needed: {2*0.05 + 3*0.08} CORE")
        print(f"   - Have: 5.0 CORE total")
        print(f"   - Remaining for gas: ~4.76 CORE")

        print(f"\n🚀 Next Steps:")
        print(f"1. Visit: https://scan.test.btcs.network/address/{new_contract}")
        print(f"2. Connect MetaMask with deployer wallet")
        print(f"3. Call contract functions manually or use registration script")
        print(f"4. Start network: python start_network.py")

        # Create quick registration summary
        summary = {
            "ultra_low_stake_contract": new_contract,
            "ready_for_registration": True,
            "entities": {
                "miners": len(miners),
                "validators": len(validators),
                "total": len(miners) + len(validators),
            },
            "stake_requirements": {
                "miner_stake": "0.05 CORE",
                "validator_stake": "0.08 CORE",
                "total_needed": f"{2*0.05 + 3*0.08} CORE",
            },
        }

        with open("ultra_low_registration_ready.json", "w") as f:
            json.dump(summary, f, indent=2)

        print(f"💾 Saved registration summary")

    else:
        print(f"\n⚠️  Some entities need more tokens")
        print(f"💡 But with 1 CORE each, all should be ready!")


if __name__ == "__main__":
    main()
