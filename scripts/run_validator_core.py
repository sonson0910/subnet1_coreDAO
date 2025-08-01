#!/usr/bin/env python3
"""
Core Blockchain Validator Runner Script for Subnet1
Migrated from Aptos to Core blockchain functionality
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
from rich.logging import RichHandler

# --- Add project root to sys.path ---
project_root = Path(__file__).parent.parent  # Go to subnet1_aptos root
sys.path.insert(0, str(project_root))
# Add moderntensor_aptos path (parent directory)
moderntensor_path = project_root.parent / "moderntensor_aptos"
sys.path.insert(0, str(moderntensor_path))

# --- Import required classes ---
try:
    from subnet1.validator import Subnet1Validator
    from mt_core.config.settings import settings as sdk_settings
    from mt_core.account import Account
except ImportError as e:
    print(f"❌ FATAL: Import Error: {e}")
    sys.exit(1)

# --- Load environment variables (.env) ---
env_path = project_root / ".env"

# --- Configure Logging with RichHandler ---
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)

rich_handler = RichHandler(
    show_time=True,
    show_level=True,
    show_path=False,
    markup=True,
    rich_tracebacks=True,
    log_time_format="[%Y-%m-%d %H:%M:%S]",
)

logging.basicConfig(
    level=log_level, format="%(message)s", datefmt="[%X]", handlers=[rich_handler]
)

logger = logging.getLogger(__name__)

# --- Load environment variables (after logger is configured) ---
if env_path.exists():
    logger.info(f"📄 Loading environment variables from: {env_path}")
    load_dotenv(dotenv_path=env_path, override=True)
else:
    logger.warning(f"📄 Environment file (.env) not found at {env_path}.")


async def run_validator_process():
    """Async function to configure and run Subnet1 Validator for Core blockchain."""
    logger.info(
        "🛡️ --- Starting Enhanced Core Blockchain Validator Configuration & Process --- 🛡️"
    )

    # === Get validator configuration from environment ===
    # Check for VALIDATOR_ID env var, default to validator1 if not specified
    validator_id = os.getenv("VALIDATOR_ID", "1")  # Can be "1" or "2"

    # Use specific validator configuration based on VALIDATOR_ID
    if validator_id == "2":
        validator_readable_id = os.getenv("VALIDATOR_2_ID")
        validator_private_key = os.getenv("VALIDATOR_2_PRIVATE_KEY")
        validator_address = os.getenv("VALIDATOR_2_ADDRESS")
        validator_api_endpoint = os.getenv("VALIDATOR_2_API_ENDPOINT")
        validator_host = os.getenv("VALIDATOR_2_HOST", "0.0.0.0")
        validator_port = int(os.getenv("VALIDATOR_2_PORT", "8002"))
    else:  # Default to validator 1
        validator_readable_id = os.getenv("VALIDATOR_1_ID") or os.getenv(
            "SUBNET1_VALIDATOR_ID"
        )
        validator_private_key = os.getenv("VALIDATOR_1_PRIVATE_KEY") or os.getenv(
            "CORE_PRIVATE_KEY"
        )
        validator_address = os.getenv("VALIDATOR_1_ADDRESS")
        validator_api_endpoint = os.getenv("VALIDATOR_1_API_ENDPOINT") or os.getenv(
            "VALIDATOR_API_ENDPOINT"
        )
        validator_host = os.getenv("VALIDATOR_1_HOST") or os.getenv(
            "SUBNET1_VALIDATOR_HOST", "0.0.0.0"
        )
        validator_port = int(
            os.getenv("VALIDATOR_1_PORT") or os.getenv("SUBNET1_VALIDATOR_PORT", "8001")
        )

    if not validator_readable_id:
        logger.critical(f"❌ FATAL: VALIDATOR_{validator_id}_ID is not set in .env.")
        return

    if not validator_private_key:
        logger.critical(
            f"❌ FATAL: VALIDATOR_{validator_id}_PRIVATE_KEY is not set in .env."
        )
        return

    logger.info(f"🆔 Using Validator {validator_id}: '{validator_readable_id}'")

    # --- Calculate UID hex ---
    try:
        expected_uid_bytes = validator_readable_id.encode("utf-8")
        expected_uid_hex = expected_uid_bytes.hex()
        logger.info(f"🔑 Derived On-Chain UID (Hex): {expected_uid_hex}")
        logger.info(f"🔑 Smart Contract uses Address as ID: {validator_address}")
    except Exception as e:
        logger.critical(
            f"❌ FATAL: Could not encode validator ID ('{validator_readable_id}') to derive UID: {e}"
        )
        return

    # === Core Blockchain Configuration ===
    core_node_url = os.getenv("CORE_NODE_URL")
    core_contract_address = os.getenv("CORE_CONTRACT_ADDRESS")

    required_configs = {
        f"VALIDATOR_{validator_id}_PRIVATE_KEY": validator_private_key,
        "CORE_NODE_URL": core_node_url,
        "CORE_CONTRACT_ADDRESS": core_contract_address,
        f"VALIDATOR_{validator_id}_API_ENDPOINT": validator_api_endpoint,
    }
    missing_configs = [k for k, v in required_configs.items() if not v]
    if missing_configs:
        logger.critical(
            f"❌ FATAL: Missing Validator {validator_id} configurations in .env: {missing_configs}"
        )
        return

    logger.info(
        f"🏗️ --- Subnet 1 Validator {validator_id} (Core Blockchain) Configuration --- 🏗️"
    )
    logger.info(f"🆔 Validator Readable ID : [cyan]'{validator_readable_id}'[/]")
    logger.info(f"🔑 Validator Address     : [yellow]{validator_address}[/]")
    logger.info(f"🔑 On-Chain UID (Hex)    : [yellow]{expected_uid_hex}[/]")
    logger.info(f"🏗️ Core Node URL         : [cyan]{core_node_url}[/]")
    logger.info(f"📝 Contract Address      : [cyan]{core_contract_address}[/]")
    logger.info(
        f"👂 API Endpoint          : [link={validator_api_endpoint}]{validator_api_endpoint}[/link]"
    )
    logger.info(
        f"👂 Listening on          : [bold blue]{validator_host}:{validator_port}[/]"
    )
    logger.info(
        "-------------------------------------------------------------------------------"
    )

    # Load Core blockchain account for Validator
    validator_account: Optional[Account] = None
    try:
        logger.info(
            f"🔑 Loading Core blockchain account for Validator {validator_id}..."
        )
        if not validator_private_key:
            raise ValueError(f"VALIDATOR_{validator_id}_PRIVATE_KEY is required")

        # Create Core blockchain account from private key
        validator_account = Account.from_key(validator_private_key)
        logger.info(
            f"✅ Validator {validator_id} Core blockchain account loaded successfully. Address: {validator_account.address}"
        )

    except Exception as key_err:
        logger.exception(
            f"💥 FATAL: Failed to load Core blockchain account for Validator {validator_id}: {key_err}"
        )
        return

    # --- Initialize and run validator ---
    try:
        logger.info(f"🛠️ Initializing Subnet1Validator {validator_id} instance...")

        # Import proper classes
        from mt_core.core.datatypes import ValidatorInfo
        from mt_core.core_client.contract_client import ModernTensorCoreClient

        # Create ValidatorInfo object for the SDK
        validator_info = ValidatorInfo(
            uid=expected_uid_hex,
            address=validator_account.address,
            stake=0,  # Will be populated from chain
            api_endpoint=validator_api_endpoint,
        )

        # Create Web3 instance first
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider(core_node_url))

        # Create ModernTensorCoreClient with Web3 instance
        core_client = ModernTensorCoreClient(
            w3=w3,
            contract_address=core_contract_address,
            account=validator_account,
        )

        # Initialize Subnet1Validator with flexible consensus enabled
        validator_instance = Subnet1Validator(
            validator_info=validator_info,
            core_client=core_client,
            account=validator_account,
            contract_address=core_contract_address,
            api_port=validator_port,
            host=validator_host,
            enable_flexible_consensus=True,  # Enable flexible consensus from SDK
            flexible_mode="balanced",  # Use balanced mode
        )
        logger.info(f"✅ Subnet1Validator {validator_id} instance initialized.")

        # Run Validator using proper async context manager
        logger.info(
            f"▶️ Starting Subnet1Validator {validator_id} main loop for UID {expected_uid_hex}..."
        )

        # Start the validator using proper async startup
        await validator_instance.start()
        logger.info(f"✅ Subnet1Validator {validator_id} started successfully")
        logger.info(
            f"🔄 Flexible Consensus: {'✅ Enabled' if validator_instance.flexible_consensus_enabled else '❌ Disabled'}"
        )

        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info(f"👋 Validator {validator_id} interrupted by user")
        finally:
            # Properly stop the validator
            await validator_instance.stop()

        logger.info(f"⏹️ Subnet1Validator {validator_id} main loop finished.")

    except Exception as e:
        logger.exception(
            f"💥 An unexpected error occurred during validator {validator_id} process startup or execution: {e}"
        )
    finally:
        logger.info(f"🛑 Validator {validator_id} process cleanup finished.")


# --- Main execution point ---
if __name__ == "__main__":
    try:
        logger.info("🚦 Starting main asynchronous execution...")
        asyncio.run(run_validator_process())
    except KeyboardInterrupt:
        logger.info("👋 Validator process interrupted by user (Ctrl+C).")
    except Exception as main_err:
        logger.exception(f"💥 Critical error in main execution block: {main_err}")
    finally:
        logger.info("🏁 Validator script finished.")
