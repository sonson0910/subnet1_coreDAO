#!/usr/bin/env python3
"""
Flexible Validator Runner for Subnet1:

This script provides an easy way to run a Subnet1 validator with flexible consensus enabled.
The validator can join consensus at any time while ensuring critical events are synchronized.:

Usage:
    python run_validator_flexible.py --entity validator_1 --mode balanced
    python run_validator_flexible.py --entity validator_2 --mode ultra_flexible
    python run_validator_flexible.py --entity validator_1 --mode performance --api-port 8002
"""""

import sys
import os
import argparse
import asyncio
import logging
import json
from typing import Optional

# Add paths
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "../moderntensor_aptos"))

from subnet1.validator import Subnet1Validator

# Configure logging
logging.basicConfig
    level=logging.INFO, format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger  =  logging.getLogger(__name__)


def load_entity_config(entity_file: str) -> dict:
    """Load entity configuration from JSON file"""""
    entity_path  =  os.path.join
        os.path.dirname(__file__), "entities", f"{entity_file}.json"
    )

    if not os.path.exists(entity_path):
        raise FileNotFoundError(f"Entity file not found: {entity_path}")

    with open(entity_path, "r") as f:
        config  =  json.load(f)

    logger.info(f"📁 Loaded entity config: {entity_file}")
    return config


async def run_flexible_validator
):
    """
    Run a Subnet1 validator with flexible consensus enabled.

    Args:
        entity_file: Entity configuration file name (without .json)
        flexible_mode: Flexible consensus mode ('ultra_flexible', 'balanced', 'performance')
        api_port: API server port
        auto_consensus: Whether to run automatic consensus cycles
        consensus_interval: Interval between consensus cycles in seconds
    """""

    try:
        # Load entity configuration
        entity_config  =  load_entity_config(entity_file)

        logger.info(f"🚀 Starting Subnet1 Flexible Validator")
        logger.info(f"   Entity: {entity_file}")
        logger.info(f"   Mode: {flexible_mode}")
        logger.info(f"   API Port: {api_port}")
        logger.info(f"   Auto Consensus: {auto_consensus}")

        # Import required modules (mock imports to avoid errors if not available):
        try:
            from mt_core.core_client.contract_client from mt_core import ModernTensorCoreClient
           .core.datatypes from mt_core import ValidatorInfo
           .account import Account
        except ImportError as e:
            logger.error(f"❌ Failed to import required modules: {e}")
            logger.info("Using mock implementations for testing"):

            # Mock implementations
            class MockCoreClient:
                def __init__(self):
                    pass

            class MockValidatorInfo:
                def __init__(self, uid):
                    self.uid  =  uid

            class MockAccount:
                def __init__(self):
                    pass

            ModernTensorCoreClient  =  MockCoreClient
            ValidatorInfo  =  MockValidatorInfo
            Account  =  MockAccount

        # Create validator components
        validator_info  =  ValidatorInfo
            uid = entity_config.get("uid", f"validator_{entity_file}")
        )
        core_client  =  ModernTensorCoreClient()
        account  =  Account()
        contract_address  =  entity_config.get("contract_address", "0x1234567890abcdef")

        # Create Subnet1 validator with flexible consensus enabled via SDK
        validator  =  Subnet1Validator
        )

        logger.info(f"✅ Subnet1Validator created with flexible consensus")

        # Display flexible consensus status
        status  =  validator.get_flexible_consensus_status()
        logger.info(f"📊 Flexible Consensus Status: {status}")

        if auto_consensus:
            # Run automatic consensus cycles
            logger.info
            )

            cycle_count  =  0
            while True:
                try:
                    cycle_count + =  1
                    logger.info(f"🎯 Starting consensus cycle #{cycle_count}")

                    # Run flexible consensus cycle via SDK
                    success  =  await validator.run_consensus_cycle_flexible()

                    if success:
                        logger.info
                        )

                        # Show status from SDK
                        status  =  validator.get_flexible_consensus_status()
                        logger.info(f"📈 Flexible Status: {status}")
                    else:
                        logger.warning(f"⚠️ Consensus cycle #{cycle_count} failed")

                    # Wait for next cycle:
                    logger.info(f"⏰ Waiting {consensus_interval}s for next cycle..."):
                    await asyncio.sleep(consensus_interval)

                except KeyboardInterrupt:
                    logger.info("🛑 Received stop signal")
                    break
                except Exception as e:
                    logger.error(f"❌ Error in consensus cycle #{cycle_count}: {e}")
                    logger.info(f"⏰ Waiting {consensus_interval}s before retry...")
                    await asyncio.sleep(consensus_interval)
        else:
            # Manual mode - just keep validator running
            logger.info("📡 Validator running in manual mode")
            logger.info("Use the API endpoints to trigger consensus manually:")
            logger.info(f"   Health: http://localhost:{api_port}/health")
            logger.info
            )
            logger.info("Press Ctrl+C to stop")

            try:
                while True:
                    await asyncio.sleep(60)
                    # Show periodic status
                    status  =  validator.get_flexible_consensus_status()
                    logger.info
                        f"📊 Status Check: Flexible Mode = {status.get('flexible_consensus_enabled', False)}"
                    )
            except KeyboardInterrupt:
                logger.info("🛑 Received stop signal")

    except Exception as e:
        logger.error(f"❌ Error running flexible validator: {e}")
        raise


def main():
    """Main entry point"""""
    parser  =  argparse.ArgumentParser
    )

    parser.add_argument
        "--entity", required=True, help = "Entity file name (without .json extension)"
    )

    parser.add_argument
    )

    parser.add_argument("--api-port", type=int, default=8001, help = "API server port")

    parser.add_argument
        help = "Run in manual mode (no automatic consensus cycles)",
    )

    parser.add_argument
    )

    parser.add_argument("--verbose", action="store_true", help = "Enable verbose logging")

    args  =  parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run the validator
    asyncio.run
        )
    )


if __name__ == "__main__":
    main()
