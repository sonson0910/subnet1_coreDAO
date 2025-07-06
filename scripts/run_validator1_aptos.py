#!/usr/bin/env python3
"""
Aptos Validator 1 Runner Script for Subnet1
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


async def run_validator1_process():
    """Async function to configure and run Subnet1 Validator 1 for Aptos."""
    logger.info("🛡️ --- Starting Aptos Validator 1 Configuration & Process --- 🛡️")

    # === Validator 1 Configuration ===
    validator_private_key = os.getenv("VALIDATOR_1_PRIVATE_KEY")
    validator_address = os.getenv("VALIDATOR_1_ADDRESS")
    validator_api_endpoint = os.getenv("VALIDATOR_1_API_ENDPOINT")
    validator_port = int(os.getenv("VALIDATOR_1_PORT", "8001"))
    validator_readable_id = "subnet1_validator_1"

    if not validator_private_key:
        logger.critical("❌ FATAL: VALIDATOR_1_PRIVATE_KEY is not set in config.env.")
        return
    
    logger.info(f"🆔 Using Validator 1: '{validator_readable_id}'")

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
        "VALIDATOR_1_PRIVATE_KEY": validator_private_key,
        "APTOS_NODE_URL": aptos_node_url,
        "APTOS_CONTRACT_ADDRESS": aptos_contract_address,
        "VALIDATOR_1_API_ENDPOINT": validator_api_endpoint
    }
    missing_configs = [k for k, v in required_configs.items() if not v]
    if missing_configs:
        logger.critical(f"❌ FATAL: Missing Validator 1 configurations in config.env: {missing_configs}")
        return

    logger.info("🏗️ --- Subnet 1 Validator 1 (Aptos Blockchain) Configuration --- 🏗️")
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
        logger.info(f"🔑 Loading Aptos account for Validator 1...")
        if not validator_private_key:
            raise ValueError("VALIDATOR_1_PRIVATE_KEY is required")
            
        # Create Aptos account from private key
        validator_account = Account.load_key(validator_private_key)
        logger.info(f"✅ Validator 1 Aptos account loaded successfully. Address: {validator_account.address()}")
        
    except Exception as key_err:
        logger.exception(f"💥 FATAL: Failed to load Aptos account for Validator 1: {key_err}")
        return

    # --- Initialize and run validator --- 
    try:
        logger.info("🛠️ Initializing Subnet1Validator 1 instance...")
        
        # Import required classes for proper initialization
        from mt_aptos.core.datatypes import ValidatorInfo
        from mt_aptos.async_client import RestClient
        
        # Create ValidatorInfo object
        validator_info = ValidatorInfo(
            uid=expected_uid_hex,
            address=str(validator_account.address()),
            api_endpoint=validator_api_endpoint,
            trust_score=1.0,
            weight=1.0,
            stake=0.0,
            last_performance=1.0,
            performance_history=[],
            subnet_uid=1,
            status=1,  # Active status
            registration_time=0,
            wallet_addr_hash=None,
            performance_history_hash=None
        )
        
        # Create Aptos REST client
        aptos_client = RestClient(aptos_node_url)
        
        # Initialize Subnet1Validator with correct parameters and sequential consensus mode
        validator_instance = Subnet1Validator(
            validator_info=validator_info,
            aptos_client=aptos_client,
            account=validator_account,
            contract_address=aptos_contract_address,
            consensus_mode="synchronized",  # Enable synchronized consensus for true coordination between validators
            batch_wait_time=30.0,  # Wait 30 seconds for each batch
            api_port=validator_port  # Use the configured port instead of default 8000
        )
        logger.info("✅ Subnet1Validator 1 instance initialized.")

        # Run Validator
        logger.info(f"▶️ Starting Subnet1Validator 1 main loop for UID {expected_uid_hex}...")
        await validator_instance.run()
        logger.info("⏹️ Subnet1Validator 1 main loop finished.")

    except Exception as e:
        logger.exception(f"💥 An unexpected error occurred during validator 1 process startup or execution: {e}")
    finally:
        logger.info("🛑 Validator 1 process cleanup finished.")


# --- Main execution point --- 
if __name__ == "__main__":
    try:
        logger.info("🚦 Starting Validator 1 main asynchronous execution...")
        asyncio.run(run_validator1_process())
    except KeyboardInterrupt:
        logger.info("👋 Validator 1 process interrupted by user (Ctrl+C).")
    except Exception as main_err:
        logger.exception(f"💥 Critical error in validator 1 main execution block: {main_err}")
    finally:
        logger.info("🏁 Validator 1 script finished.") 