#!/usr/bin/env python3
"""
Flexible Validator Runner - Start validator anytime with adaptive consensus

This script demonstrates how to run a validator in flexible mode:
- Can start at any time during consensus
- Automatically detects current network state
- Adapts to ongoing consensus phases
- Maintains synchronization for critical events

Usage:
    python run_flexible_validator.py [--mode flexible|rigid] [--auto-adapt]
"""

import asyncio
import logging
import argparse
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from moderntensor_aptos.mt_core.consensus.flexible_validator_node import (
    FlexibleValidatorNode,
    FlexibleSlotConfig,
)
from moderntensor_aptos.mt_core.consensus.validator_node_core import ValidatorNodeCore
from moderntensor_aptos.mt_core.config.config_loader import ModernTensorConfig
from moderntensor_aptos.mt_core.core_client.account_service import AccountService
from moderntensor_aptos.mt_core.core.datatypes import ValidatorInfo
from web3 import Web3

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s[%(process)d] %(levelname)-8s %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def setup_flexible_config(mode: str) -> FlexibleSlotConfig:
    """Setup flexible slot configuration based on mode."""

    if mode == "ultra_flexible":
        # Maximum flexibility - can start anytime, long buffers
        return FlexibleSlotConfig(
            slot_duration_minutes=5.0,
            min_task_assignment_seconds=20,
            min_task_execution_seconds=45,
            min_consensus_seconds=30,
            min_metagraph_update_seconds=15,
            task_deadline_buffer=45,
            consensus_deadline_buffer=60,
            metagraph_deadline_buffer=20,
            allow_mid_slot_join=True,
            auto_extend_on_consensus=True,
            max_auto_extension_seconds=120,
        )

    elif mode == "balanced":
        # Balanced flexibility and timing
        return FlexibleSlotConfig(
            slot_duration_minutes=4.0,
            min_task_assignment_seconds=30,
            min_task_execution_seconds=60,
            min_consensus_seconds=45,
            min_metagraph_update_seconds=15,
            task_deadline_buffer=30,
            consensus_deadline_buffer=45,
            metagraph_deadline_buffer=15,
            allow_mid_slot_join=True,
            auto_extend_on_consensus=True,
            max_auto_extension_seconds=90,
        )

    elif mode == "performance":
        # Performance focused - shorter times but flexible start
        return FlexibleSlotConfig(
            slot_duration_minutes=3.0,
            min_task_assignment_seconds=25,
            min_task_execution_seconds=50,
            min_consensus_seconds=35,
            min_metagraph_update_seconds=10,
            task_deadline_buffer=20,
            consensus_deadline_buffer=30,
            metagraph_deadline_buffer=10,
            allow_mid_slot_join=True,
            auto_extend_on_consensus=False,  # No auto-extension for performance
            max_auto_extension_seconds=30,
        )

    else:  # default
        return FlexibleSlotConfig()


async def load_validator_account(entity_file: str = None) -> tuple:
    """Load validator account from entity file or create a new one."""

    account_service = AccountService()

    # Try to load from specified file or find existing
    entity_paths = []
    if entity_file:
        entity_paths.append(entity_file)

    # Add common entity file patterns
    entity_paths.extend(
        [
            "entities/subnet1_validator_001.json",
            "entities/subnet1_validator_002.json",
            "entities/validator_1.json",
            "entities/validator_2.json",
        ]
    )

    for entity_path in entity_paths:
        if os.path.exists(entity_path):
            logger.info(f"📁 Loading validator account from {entity_path}")

            try:
                account_data = account_service.load_account_from_file(entity_path)

                if account_data:
                    validator_info = ValidatorInfo(
                        uid=account_data.get(
                            "entity_id", f"flexible_validator_{int(time.time())}"
                        ),
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

                    logger.info(f"✅ Loaded validator: {validator_info.uid}")
                    logger.info(f"📍 Address: {validator_info.address}")

                    return validator_info, account_data

            except Exception as e:
                logger.warning(f"⚠️ Could not load {entity_path}: {e}")
                continue

    # Create a new validator account if none found
    logger.info("🆕 Creating new validator account")

    from eth_account import Account as EthAccount
    import time

    new_account = EthAccount.create()
    validator_uid = f"flexible_validator_{int(time.time())}"

    validator_info = ValidatorInfo(
        uid=validator_uid,
        address=new_account.address,
        api_endpoint="http://localhost:8001",
        last_performance=0.0,
        trust_score=0.5,
        stake=1000.0,
        status=1,
        performance_history=[],
        subnet_uid=1,
        registration_time=int(time.time()),
    )

    # Save the new account
    account_data = {
        "entity_id": validator_uid,
        "address": new_account.address,
        "private_key": new_account.key.hex(),
        "created_at": time.time(),
    }

    # Create entities directory if it doesn't exist
    os.makedirs("entities", exist_ok=True)

    # Save to file
    import json

    entity_file = f"entities/{validator_uid}.json"
    with open(entity_file, "w") as f:
        json.dump(account_data, f, indent=2)

    logger.info(f"💾 Saved new validator account to {entity_file}")

    return validator_info, account_data


async def run_flexible_validator(
    mode: str = "balanced", auto_adapt: bool = True, entity_file: str = None
):
    """
    Run a flexible validator that can start anytime.

    Args:
        mode: Flexibility mode (ultra_flexible, balanced, performance)
        auto_adapt: Whether to auto-adapt timing based on network
        entity_file: Specific entity file to load
    """

    logger.info("🚀 Starting Flexible Validator")
    logger.info(f"📊 Mode: {mode}, Auto-adapt: {auto_adapt}")
    logger.info("=" * 60)

    try:
        # Load configuration
        config = ModernTensorConfig()
        logger.info(f"✅ Config loaded")
        logger.info(f"   - Contract: {config.blockchain.contract_address}")
        logger.info(f"   - Node URL: {config.blockchain.core_node_url}")

        # Setup flexible configuration
        flexible_config = setup_flexible_config(mode)
        logger.info(f"🔧 Flexible config:")
        logger.info(f"   - Slot duration: {flexible_config.slot_duration_minutes} min")
        logger.info(f"   - Mid-slot join: {flexible_config.allow_mid_slot_join}")
        logger.info(f"   - Auto-extend: {flexible_config.auto_extend_on_consensus}")

        # Load validator account
        validator_info, account_data = await load_validator_account(entity_file)

        # Setup Web3 client
        core_client = Web3(Web3.HTTPProvider(config.blockchain.core_node_url))
        logger.info(f"🌐 Web3 connected: {core_client.is_connected()}")

        # Create account object
        from eth_account import Account as EthAccount

        account = EthAccount.from_key(account_data["private_key"])

        # Create core validator node
        validator_core = ValidatorNodeCore(
            validator_info=validator_info,
            core_client=core_client,
            account=account,
            contract_address=config.blockchain.contract_address,
            api_port=8001,
            consensus_mode="flexible",  # Set to flexible mode
        )

        # Create flexible validator wrapper
        flexible_validator = FlexibleValidatorNode(
            validator_core=validator_core,
            flexible_config=flexible_config,
            auto_adapt_timing=auto_adapt,
        )

        logger.info("✅ Flexible validator initialized")

        # Start the flexible consensus process
        logger.info("🔄 Starting flexible consensus process...")
        logger.info("   (Validator can join at any time during consensus)")

        await flexible_validator.start_flexible_consensus()

    except KeyboardInterrupt:
        logger.info("🛑 Flexible validator stopped by user")
    except Exception as e:
        logger.error(f"❌ Error running flexible validator: {e}")
        import traceback

        traceback.print_exc()


async def demo_flexibility():
    """Demonstrate flexibility by showing different start scenarios."""

    logger.info("🎭 DEMONSTRATING FLEXIBILITY")
    logger.info("=" * 60)

    scenarios = [
        ("ultra_flexible", "Maximum flexibility - can join anytime"),
        ("balanced", "Balanced flexibility and performance"),
        ("performance", "Performance focused with flexible start"),
    ]

    for mode, description in scenarios:
        logger.info(f"\n📊 Testing {mode.upper()} mode:")
        logger.info(f"   {description}")

        # Show configuration
        config = setup_flexible_config(mode)
        logger.info(f"   - Slot duration: {config.slot_duration_minutes} min")
        logger.info(f"   - Task buffer: {config.task_deadline_buffer}s")
        logger.info(f"   - Consensus buffer: {config.consensus_deadline_buffer}s")
        logger.info(f"   - Auto-extend: {config.auto_extend_on_consensus}")

        # Simulate starting at different times
        logger.info("   🕐 Can start at any of these times:")
        logger.info("      - Beginning of slot (normal)")
        logger.info("      - During task assignment")
        logger.info("      - During task execution")
        logger.info("      - During consensus scoring")
        logger.info("      - During metagraph update")


def main():
    """Main entry point with command line argument support."""

    parser = argparse.ArgumentParser(
        description="Flexible Validator - Start anytime with adaptive consensus",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Start with balanced flexibility (default)
    python run_flexible_validator.py
    
    # Maximum flexibility mode
    python run_flexible_validator.py --mode ultra_flexible
    
    # Performance mode with auto-adaptation
    python run_flexible_validator.py --mode performance --auto-adapt
    
    # Use specific entity file
    python run_flexible_validator.py --entity-file entities/my_validator.json
    
    # Demo different flexibility modes
    python run_flexible_validator.py --demo
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["ultra_flexible", "balanced", "performance"],
        default="balanced",
        help="Flexibility mode (default: balanced)",
    )

    parser.add_argument(
        "--auto-adapt",
        action="store_true",
        default=True,
        help="Auto-adapt timing based on network (default: True)",
    )

    parser.add_argument("--entity-file", help="Specific entity file to load")

    parser.add_argument(
        "--demo", action="store_true", help="Demonstrate different flexibility modes"
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("🐛 Debug logging enabled")

    # Run demo or actual validator
    if args.demo:
        asyncio.run(demo_flexibility())
    else:
        asyncio.run(
            run_flexible_validator(
                mode=args.mode, auto_adapt=args.auto_adapt, entity_file=args.entity_file
            )
        )


if __name__ == "__main__":
    main()
