#!/usr/bin/env python3
"""
Aptos Validator 3 Runner Script for Subnet1
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
sys.path.insert(0, str(project_root.parent / "moderntensor"))  # Add moderntensor path for mt_aptos imports

# --- Import required classes --- 
try:
    from subnet1.validator import Subnet1Validator
    from mt_aptos.config.settings import settings as sdk_settings
    from mt_aptos.account import Account
except ImportError as e:
    print(f"❌ FATAL: Import Error: {e}")
    sys.exit(1)

# --- Load environment variables from config.env ---
env_path = project_root.parent / 'config.env'  # Look for config.env in root

# --- Configure Logging with RichHandler ---
log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)

rich_handler = RichHandler(
    show_time=True,
    show_level=True,
    show_path=False,
    markup=True,
    rich_tracebacks=True,
    log_time_format="[%Y-%m-%d %H:%M:%S]"
)

logging.basicConfig(
    level=log_level,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[rich_handler]
)

logger = logging.getLogger(__name__)

# --- Load environment variables (after logger is configured) ---
if env_path.exists():
    logger.info(f"📄 Loading environment variables from: {env_path}")
    load_dotenv(dotenv_path=env_path, override=True)
else:
    logger.warning(f"📄 Environment file (config.env) not found at {env_path}.")


async def run_validator3_process():
    """Async function to configure and run Subnet1 Validator 3 for Aptos."""
    logger.info("🛡️ --- Starting Aptos Validator 3 Configuration & Process --- 🛡️")

    # === Validator 3 Configuration ===
    validator_private_key = os.getenv("VALIDATOR_3_PRIVATE_KEY")
    validator_address = os.getenv("VALIDATOR_3_ADDRESS")
    validator_api_endpoint = os.getenv("VALIDATOR_3_API_ENDPOINT")
    validator_port = int(os.getenv("VALIDATOR_3_PORT", "8003"))
    validator_readable_id = "subnet1_validator_3"

    if not validator_private_key:
        logger.critical("❌ FATAL: VALIDATOR_3_PRIVATE_KEY is not set in config.env.")
        return
    
    logger.info(f"🆔 Using Validator 3: '{validator_readable_id}'")

    # --- Calculate UID hex ---
    try:
        expected_uid_bytes = validator_readable_id.encode('utf-8')
        expected_uid_hex = expected_uid_bytes.hex()
        logger.info(f"🔑 Derived On-Chain UID (Hex): {expected_uid_hex}")
    except Exception as e:
        logger.critical(f"❌ FATAL: Could not encode validator ID ('{validator_readable_id}') to derive UID: {e}")
        return

    # === Aptos Configuration ===
    aptos_node_url = os.getenv("APTOS_NODE_URL")
    aptos_contract_address = os.getenv("APTOS_CONTRACT_ADDRESS")
    validator_host = os.getenv("SUBNET1_VALIDATOR_HOST", "0.0.0.0")

    required_configs = {
        "VALIDATOR_3_PRIVATE_KEY": validator_private_key,
        "APTOS_NODE_URL": aptos_node_url,
        "APTOS_CONTRACT_ADDRESS": aptos_contract_address,
        "VALIDATOR_3_API_ENDPOINT": validator_api_endpoint
    }
    missing_configs = [k for k, v in required_configs.items() if not v]
    if missing_configs:
        logger.critical(f"❌ FATAL: Missing Validator 3 configurations in config.env: {missing_configs}")
        return

    logger.info("🏗️ --- Subnet 1 Validator 3 (Aptos Blockchain) Configuration --- 🏗️")
    logger.info(f"🆔 Validator Readable ID : [cyan]'{validator_readable_id}'[/]")
    logger.info(f"🔑 Validator Address     : [yellow]{validator_address}[/]")
    logger.info(f"🔑 On-Chain UID (Hex)    : [yellow]{expected_uid_hex}[/]")
    logger.info(f"🏗️ Aptos Node URL        : [cyan]{aptos_node_url}[/]")
    logger.info(f"📝 Contract Address      : [cyan]{aptos_contract_address}[/]")
    logger.info(f"👂 API Endpoint          : [link={validator_api_endpoint}]{validator_api_endpoint}[/link]")
    logger.info(f"👂 Listening on          : [bold blue]{validator_host}:{validator_port}[/]")
    logger.info("-------------------------------------------------------------------------------")

    # Load Aptos account for Validator
    validator_account: Optional[Account] = None
    try:
        logger.info(f"🔑 Loading Aptos account for Validator 3...")
        if not validator_private_key:
            raise ValueError("VALIDATOR_3_PRIVATE_KEY is required")
            
        # Create Aptos account from private key
        validator_account = Account.load_key(validator_private_key)
        logger.info(f"✅ Validator 3 Aptos account loaded successfully. Address: {validator_account.address()}")
        
    except Exception as key_err:
        logger.exception(f"💥 FATAL: Failed to load Aptos account for Validator 3: {key_err}")
        return

    # --- Initialize and run validator --- 
    try:
        logger.info("🛠️ Initializing Subnet1Validator 3 instance...")
        validator_info = {
            "validator_id": validator_readable_id,
            "on_chain_uid_hex": expected_uid_hex,
            "host": validator_host,
            "port": validator_port,
            "aptos_node_url": aptos_node_url,
            "contract_address": aptos_contract_address,
            "api_endpoint": validator_api_endpoint
        }
        aptos_client = None  # Assuming aptos_client is not provided in the original code
        validator_instance = Subnet1Validator(
            validator_info=validator_info,
            aptos_client=aptos_client,
            account=validator_account,
            contract_address=aptos_contract_address,
            consensus_mode="synchronized",  # Enable synchronized consensus for coordination between validators  
            batch_wait_time=30.0,  # Wait 30 seconds for each batch
            api_port=validator_port  # Use the configured port instead of default 8000
        )
        logger.info("✅ Subnet1Validator 3 instance initialized.")

        # Run Validator
        logger.info(f"▶️ Starting Subnet1Validator 3 main loop for UID {expected_uid_hex}...")
        await validator_instance.run()
        logger.info("⏹️ Subnet1Validator 3 main loop finished.")

    except Exception as e:
        logger.exception(f"💥 An unexpected error occurred during validator 3 process startup or execution: {e}")
    finally:
        logger.info("🛑 Validator 3 process cleanup finished.")


# --- Main execution point --- 
if __name__ == "__main__":
    try:
        logger.info("🚦 Starting Validator 3 main asynchronous execution...")
        asyncio.run(run_validator3_process())
    except KeyboardInterrupt:
        logger.info("👋 Validator 3 process interrupted by user (Ctrl+C).")
    except Exception as main_err:
        logger.exception(f"💥 Critical error in validator 3 main execution block: {main_err}")
    finally:
        logger.info("🏁 Validator 3 script finished.") 