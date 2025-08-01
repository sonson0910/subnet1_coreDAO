#!/usr/bin/env python3
"""
Debug script to test validator detection logic
Run this to see what validators are loaded and why P2P communication fails
"""

import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from moderntensor_aptos.mt_core.consensus.validator_node_core import ValidatorNodeCore
from moderntensor_aptos.mt_core.config.config_loader import ModernTensorConfig

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)s[%(process)d] %(levelname)-8s %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


async def debug_validator_detection():
    """Debug validator detection to see why P2P fails"""

    try:
        print("🔍 DEBUGGING VALIDATOR DETECTION")
        print("=" * 60)

        # Load config
        config = ModernTensorConfig()
        print(f"✅ Config loaded successfully")
        print(f"   - Contract address: {config.blockchain.contract_address}")
        print(f"   - Validators in config: {len(getattr(config, 'validators', {}))}")

        # Create validator node core
        print("\n🏗️ Creating ValidatorNodeCore...")

        # Try to use existing validator account setup
        from moderntensor_aptos.mt_core.core_client.account_service import (
            AccountService,
        )
        from moderntensor_aptos.mt_core.core.datatypes import ValidatorInfo
        from web3 import Web3

        # Load existing validator account if available
        try:
            # Try to find validator 1 or 2
            entity_paths = [
                "entities/subnet1_validator_001.json",
                "entities/subnet1_validator_002.json",
            ]

            account_service = None
            validator_info = None

            for entity_path in entity_paths:
                if os.path.exists(entity_path):
                    print(f"   📁 Found entity file: {entity_path}")

                    # Load account from entity file
                    account_service = AccountService()
                    account_data = account_service.load_account_from_file(entity_path)

                    if account_data:
                        validator_info = ValidatorInfo(
                            uid=account_data.get("entity_id", "debug_validator"),
                            address=account_data.get("address", ""),
                            api_endpoint="http://localhost:8001",
                            last_performance=0.0,
                            trust_score=0.5,
                            stake=1000.0,
                            status=1,
                            performance_history=[],
                            subnet_uid=1,
                            registration_time=0,
                        )
                        print(f"   ✅ Loaded validator: {validator_info.uid}")
                        break

            if not account_service or not validator_info:
                # Create mock if no real account found
                print("   ⚠️ No validator accounts found, creating mock...")
                validator_info = ValidatorInfo(
                    uid="debug_validator_mock",
                    address="0x1234567890123456789012345678901234567890",
                    api_endpoint="http://localhost:8001",
                    last_performance=0.0,
                    trust_score=0.5,
                    stake=1000.0,
                    status=1,
                    performance_history=[],
                    subnet_uid=1,
                    registration_time=0,
                )

                # Create mock account
                from eth_account import Account as EthAccount

                mock_account = EthAccount.create()
                account_service = mock_account

            # Create Web3 client
            core_client = Web3(Web3.HTTPProvider(config.blockchain.core_node_url))

            print(f"   ✅ Web3 client connected: {core_client.is_connected()}")

            validator_core = ValidatorNodeCore(
                validator_info=validator_info,
                core_client=core_client,
                account=account_service,
                contract_address=config.blockchain.contract_address,
                api_port=8001,
            )

        except Exception as e:
            print(f"   ❌ Error creating ValidatorNodeCore: {e}")
            print("   📋 Trying simplified debug approach...")

            # Skip full ValidatorNodeCore creation and just test contract client
            from moderntensor_aptos.mt_core.metagraph.core_metagraph_adapter import (
                CoreMetagraphClient,
            )

            print("\n📊 Testing direct blockchain access...")
            core_client = CoreMetagraphClient()

            validators_addresses = core_client.get_all_validators()
            miners_addresses = core_client.get_all_miners()

            print(f"✅ Validators on blockchain: {len(validators_addresses)}")
            for addr in validators_addresses:
                print(f"   - {addr}")
                try:
                    validator_info = core_client.get_validator_info(addr)
                    print(f"     Status: {validator_info.get('status', 'N/A')}")
                    print(f"     Endpoint: {validator_info.get('api_endpoint', 'N/A')}")
                except Exception as ve:
                    print(f"     Error getting info: {ve}")

            print(f"✅ Miners on blockchain: {len(miners_addresses)}")
            for addr in miners_addresses:
                print(f"   - {addr}")

            print("\n🎯 SIMPLIFIED SUMMARY:")
            print(f"   - Validators on chain: {len(validators_addresses)}")
            print(f"   - Miners on chain: {len(miners_addresses)}")
            print(
                f"   - P2P possible: {'✅ YES' if len(validators_addresses) > 1 else '❌ NO - Only 1 validator'}"
            )
            return

        print("✅ ValidatorNodeCore created")

        # Load metagraph data
        print("\n📊 Loading metagraph data...")
        await validator_core.load_metagraph_data()

        print(f"✅ Metagraph loaded:")
        print(f"   - Miners: {len(validator_core.miners_info)}")
        print(f"   - Validators: {len(validator_core.validators_info)}")

        # Test validator detection
        print("\n🔍 Testing validator detection...")

        if hasattr(validator_core, "consensus"):
            active_validators = await validator_core.consensus._get_active_validators()
            print(f"✅ Active validators detected: {len(active_validators)}")

            for i, validator in enumerate(active_validators):
                print(f"   [{i+1}] UID: {getattr(validator, 'uid', 'N/A')}")
                print(f"       Address: {getattr(validator, 'address', 'N/A')}")
                print(f"       Endpoint: {getattr(validator, 'api_endpoint', 'N/A')}")
                print(f"       Status: {getattr(validator, 'status', 'N/A')}")
        else:
            print("❌ No consensus module found")

        # Manual check of validators_info
        print("\n📋 Manual validators_info check:")
        for uid, validator_info in validator_core.validators_info.items():
            print(f"   UID: {uid}")
            print(f"   Type: {type(validator_info)}")
            print(f"   Address: {getattr(validator_info, 'address', 'N/A')}")
            print(f"   Endpoint: {getattr(validator_info, 'api_endpoint', 'N/A')}")
            print(
                f"   Status: {getattr(validator_info, 'status', 'N/A')} ({type(getattr(validator_info, 'status', None))})"
            )
            print(f"   ---")

        # Check blockchain data
        print("\n🔗 Checking blockchain data...")
        if hasattr(validator_core, "core_contract_client"):
            try:
                validators_addresses = (
                    validator_core.core_contract_client.get_all_validators()
                )
                print(f"✅ Validators on blockchain: {len(validators_addresses)}")
                for addr in validators_addresses:
                    print(f"   - {addr}")

                miners_addresses = validator_core.core_contract_client.get_all_miners()
                print(f"✅ Miners on blockchain: {len(miners_addresses)}")
                for addr in miners_addresses:
                    print(f"   - {addr}")

            except Exception as e:
                print(f"❌ Error checking blockchain: {e}")
        else:
            print("❌ No core_contract_client found")

        print("\n🎯 SUMMARY:")
        total_validators = len(validator_core.validators_info)
        self_uid = validator_core.info.uid if validator_core.info else "Unknown"
        other_validators = [
            v
            for v in validator_core.validators_info.values()
            if getattr(v, "uid", None) != self_uid
        ]

        print(f"   - Total validators loaded: {total_validators}")
        print(f"   - Self UID: {self_uid}")
        print(f"   - Other validators: {len(other_validators)}")
        print(f"   - Can do P2P: {'✅ YES' if len(other_validators) > 0 else '❌ NO'}")

        if len(other_validators) == 0:
            print("\n💡 SOLUTION:")
            print("   - Register more validators to the smart contract")
            print("   - Ensure validators have proper api_endpoint set")
            print("   - Check validator status is active (status >= 1)")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_validator_detection())
