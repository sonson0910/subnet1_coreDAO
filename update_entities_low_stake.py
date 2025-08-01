#!/usr/bin/env python3
"""
Update entity configurations with ultra-low stake amounts
Suitable for 1 CORE faucet tokens
"""

import json
from pathlib import Path


def main():
    print("🔄 Updating Entity Configurations for Ultra-Low Stakes")
    print("=" * 55)

    entities_dir = Path(__file__).parent / "entities"

    if not entities_dir.exists():
        print("❌ No entities directory found")
        return

    # Update miners
    for i in range(1, 3):
        miner_file = entities_dir / f"miner_{i}.json"
        if miner_file.exists():
            with open(miner_file, "r") as f:
                entity = json.load(f)

            # Update stake amount
            entity["stake_amount"] = "0.05"  # Ultra-low: 0.05 CORE
            entity["gas_reserve"] = "0.95"  # Keep rest for gas
            entity["updated_for"] = "ultra_low_stake_contract"

            with open(miner_file, "w") as f:
                json.dump(entity, f, indent=2)

            print(f"✅ Updated {entity['name']}: {entity['stake_amount']} CORE stake")

    # Update validators
    for i in range(1, 4):
        validator_file = entities_dir / f"validator_{i}.json"
        if validator_file.exists():
            with open(validator_file, "r") as f:
                entity = json.load(f)

            # Update stake amount
            entity["stake_amount"] = "0.08"  # Ultra-low: 0.08 CORE
            entity["gas_reserve"] = "0.92"  # Keep rest for gas
            entity["updated_for"] = "ultra_low_stake_contract"

            with open(validator_file, "w") as f:
                json.dump(entity, f, indent=2)

            print(f"✅ Updated {entity['name']}: {entity['stake_amount']} CORE stake")

    print(f"\n📊 New Requirements:")
    print(f"🔨 Miners: 0.05 CORE each (have 1.0 CORE = 20x requirement)")
    print(f"✅ Validators: 0.08 CORE each (have 1.0 CORE = 12.5x requirement)")
    print(f"⛽ Gas Reserve: ~0.9 CORE per entity for transactions")
    print(f"\n🎉 All entities can now participate with faucet tokens!")


if __name__ == "__main__":
    main()
