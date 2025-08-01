#!/usr/bin/env python3
"""
Test script for Core blockchain ModernTensor style slot-based consensus
This script runs validators with the same timing patterns as the successful Cardano project
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Setup detailed logging with file output
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"logs/validator1_consensus_{timestamp}.log"

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging with both file and console output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, mode="w"),  # Write mode for fresh logs
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Also create a separate consensus-only log file
consensus_log_filename = f"logs/validator1_consensus_only_{timestamp}.log"
consensus_logger = logging.getLogger("consensus_events")
consensus_handler = logging.FileHandler(consensus_log_filename, mode="w")
consensus_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
consensus_logger.addHandler(consensus_handler)
consensus_logger.setLevel(logging.INFO)
consensus_logger.propagate = False  # Don't propagate to root logger


# Log important events with special markers
def log_consensus_event(message):
    full_msg = f"📊 CONSENSUS: {message}"
    logger.info(full_msg)
    consensus_logger.info(full_msg)  # Also log to consensus-only file


def log_txid_event(message):
    full_msg = f"🔗 TXID: {message}"
    logger.info(full_msg)
    consensus_logger.info(full_msg)


def log_score_event(message):
    full_msg = f"📈 SCORE: {message}"
    logger.info(full_msg)
    consensus_logger.info(full_msg)


def log_p2p_event(message):
    full_msg = f"🌐 P2P: {message}"
    logger.info(full_msg)
    consensus_logger.info(full_msg)


def log_task_event(message):
    full_msg = f"📋 TASK: {message}"
    logger.info(full_msg)
    consensus_logger.info(full_msg)


logger.info("=" * 80)
logger.info("🚀 STARTING CORE BLOCKCHAIN VALIDATOR 1 WITH DETAILED LOGGING")
logger.info(f"📝 Log file: {log_filename}")
logger.info("=" * 80)

# Add project root to path
project_root = Path(__file__).parent.parent.parent  # Go up to the actual project root
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "moderntensor_aptos"))

# Load environment variables
env_path = project_root / "config.env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

# Set environment to use Core blockchain test config (fast cycles)
os.environ["ENV_FILE"] = str(project_root / "core_test_config.env")

# Import after setting environment
from mt_core.config.settings import settings
from mt_core.account import Account
from mt_core.async_client import ModernTensorCoreClient
from subnet1.validator import Subnet1Validator


async def test_core_style_validator():
    """Test validator with Core blockchain ModernTensor slot timing"""

    logger.info("🚀 Starting Core blockchain ModernTensor style validator test")
    logger.info(
        f"📋 Using Core config with CONSENSUS_CYCLE_LENGTH: {settings.CONSENSUS_CYCLE_LENGTH} seconds"
    )

    try:
        # Load validator 1 account from private key
        validator_private_key = os.getenv("VALIDATOR_1_PRIVATE_KEY")
        if not validator_private_key:
            raise ValueError("VALIDATOR_1_PRIVATE_KEY not found in environment")

        validator_account = Account.from_key(validator_private_key)
        validator_address = str(validator_account.address)

        logger.info(f"🔑 Validator 1 Address: {validator_address}")

        # Initialize Core blockchain client
        core_client = ModernTensorCoreClient(settings.CORE_NODE_URL)

        # Get contract address
        core_contract_address = settings.CORE_CONTRACT_ADDRESS

        # Create validator info
        from mt_core.core.datatypes import ValidatorInfo

        validator_info = ValidatorInfo(
            uid="validator_1",
            address=validator_address,
            api_endpoint="http://localhost:8001",
            status="active",
        )

        # Initialize Subnet1Validator with Core blockchain consensus mode
        validator_instance = Subnet1Validator(
            validator_info=validator_info,
            core_client=core_client,
            account=validator_account,
            contract_address=core_contract_address,
            consensus_mode="flexible",  # Use flexible mode for independent task assignment with synchronized consensus
            batch_wait_time=30.0,
            api_port=8001,  # Use port 8001 to match the api_endpoint
        )

        logger.info("✅ Validator 1 initialized with Core blockchain timing")
        logger.info(
            f"🎯 Will perform SYNCHRONIZED consensus every {settings.CONSENSUS_CYCLE_LENGTH} seconds"
        )
        logger.info(
            "📋 Synchronized Mode: Send tasks → Wait for completion → Score → P2P broadcast → Consensus"
        )

        # Run validator with enhanced logging
        log_consensus_event("Starting validator run loop...")
        await validator_instance.run()

    except Exception as e:
        logger.error(f"❌ Validator error: {e}")
        raise
    finally:
        log_consensus_event("Validator 1 finished")
        logger.info("✅ Core blockchain Validator 1 completed!")


async def check_current_scores():
    """Check and display current scores from the validator"""
    try:
        import httpx

        # Call validator API to get current status
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/status")

            if response.status_code == 200:
                status_data = response.json()
                print(f"\n📊 **CURRENT VALIDATOR STATUS:**")
                print(f"Task Status: {status_data.get('task_status', {})}")
                print(f"Consensus Status: {status_data.get('consensus_status', {})}")

                # Try to get scores endpoint if exists
                try:
                    scores_response = await client.get("http://localhost:8001/scores")
                    if scores_response.status_code == 200:
                        scores_data = scores_response.json()
                        print(f"\n🎯 **CURRENT SCORES:**")
                        for slot, scores in scores_data.items():
                            print(f"Slot {slot}: {len(scores)} scores")
                            for score in scores:
                                print(
                                    f"  - Miner {score['miner_uid']}: {score['score']:.3f}"
                                )
                except:
                    print("No scores endpoint available")

            else:
                print(f"Failed to get status: HTTP {response.status_code}")

    except Exception as e:
        print(f"Error checking scores: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "check":
        asyncio.run(check_current_scores())
    else:
        asyncio.run(test_core_style_validator())

    logger.info("🏁 Validator 1 script finished.")
