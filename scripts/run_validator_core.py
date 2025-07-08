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
project_root = Path(__file__).parent.parent  # Go to subnet1 root
sys.path.insert(0, str(project_root))
sys.path.insert(
    0, str(project_root.parent / "moderntensor_aptos")
)  # Add moderntensor path for mt_core imports

# --- Import required classes ---
try:
    from subnet1.validator import Subnet1Validator
    from moderntensor_aptos.mt_core.config.settings import settings as sdk_settings
    from moderntensor_aptos.mt_core.account import Account
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
        "🛡️ --- Starting Core Blockchain Validator Configuration & Process --- 🛡️"
    )

    # === Configuration for Validator ===
    validator_readable_id = os.getenv("SUBNET1_VALIDATOR_ID")
    if not validator_readable_id:
        logger.critical("❌ FATAL: SUBNET1_VALIDATOR_ID is not set in .env.")
        return
    logger.info(f"🆔 Read Validator ID from .env: '{validator_readable_id}'")

    # --- Calculate UID hex ---
    try:
        expected_uid_bytes = validator_readable_id.encode("utf-8")
        expected_uid_hex = expected_uid_bytes.hex()
        logger.info(f"🔑 Derived On-Chain UID (Hex): {expected_uid_hex}")
    except Exception as e:
        logger.critical(
            f"❌ FATAL: Could not encode SUBNET1_VALIDATOR_ID ('{validator_readable_id}') to derive UID: {e}"
        )
        return

    # === Core Blockchain Configuration ===
    core_private_key = os.getenv("CORE_PRIVATE_KEY")
    core_node_url = os.getenv("CORE_NODE_URL")
    core_contract_address = os.getenv("CORE_CONTRACT_ADDRESS")
    validator_api_endpoint = os.getenv("VALIDATOR_API_ENDPOINT")
    validator_host = os.getenv("SUBNET1_VALIDATOR_HOST") or "0.0.0.0"
    validator_port = int(os.getenv("SUBNET1_VALIDATOR_PORT") or 8001)

    required_configs = {
        "CORE_PRIVATE_KEY": core_private_key,
        "CORE_NODE_URL": core_node_url,
        "CORE_CONTRACT_ADDRESS": core_contract_address,
        "VALIDATOR_API_ENDPOINT": validator_api_endpoint,
    }
    missing_configs = [k for k, v in required_configs.items() if not v]
    if missing_configs:
        logger.critical(
            f"❌ FATAL: Missing Validator configurations in .env: {missing_configs}"
        )
        return

    logger.info("🏗️ --- Subnet 1 Validator (Core Blockchain) Configuration --- 🏗️")
    logger.info(f"🆔 Validator Readable ID : [cyan]'{validator_readable_id}'[/]")
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
        logger.info(f"🔑 Loading Core blockchain account for Validator...")
        if not core_private_key:
            raise ValueError("CORE_PRIVATE_KEY is required")

        # Create Core blockchain account from private key
        validator_account = Account.from_key(core_private_key)
        logger.info(
            f"✅ Validator Core blockchain account loaded successfully. Address: {validator_account.address}"
        )

    except Exception as key_err:
        logger.exception(
            f"💥 FATAL: Failed to load Core blockchain account for Validator: {key_err}"
        )
        return

    # --- Initialize and run validator ---
    try:
        logger.info("🛠️ Initializing Subnet1Validator instance...")
        validator_instance = Subnet1Validator(
            validator_id=validator_readable_id,
            on_chain_uid_hex=expected_uid_hex,
            host=validator_host,
            port=validator_port,
            core_node_url=core_node_url,
            core_account=validator_account,
            contract_address=core_contract_address,
            api_endpoint=validator_api_endpoint,
            api_port=validator_port,
        )
        logger.info("✅ Subnet1Validator instance initialized.")

        # Run Validator
        logger.info(
            f"▶️ Starting Subnet1Validator main loop for UID {expected_uid_hex}..."
        )
        await validator_instance.run()
        logger.info("⏹️ Subnet1Validator main loop finished.")

    except Exception as e:
        logger.exception(
            f"💥 An unexpected error occurred during validator process startup or execution: {e}"
        )
    finally:
        logger.info("🛑 Validator process cleanup finished.")


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
