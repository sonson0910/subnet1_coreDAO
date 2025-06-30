#!/usr/bin/env python3
"""
Aptos Miner 2 Runner Script for Subnet1
"""

import os
import sys
import logging
import asyncio
import threading
import binascii
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from rich.logging import RichHandler

# --- Add project root to sys.path ---
project_root = Path(__file__).parent.parent  # Go to subnet1 root
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent / "moderntensor"))  # Add moderntensor path for mt_aptos imports

# --- Import required classes --- 
try:
    from subnet1.miner import Subnet1Miner
    from mt_aptos.config.settings import settings as sdk_settings
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


async def run_miner2_processes():
    """Async function to configure and run Miner 2 processes for Aptos."""
    logger.info("⛏️ --- Starting Aptos Miner 2 Configuration & Processes --- ⛏️")

    # === Miner 2 Configuration ===
    miner_private_key = os.getenv("MINER_2_PRIVATE_KEY")
    miner_address = os.getenv("MINER_2_ADDRESS")
    miner_api_endpoint = os.getenv("MINER_2_API_ENDPOINT")
    miner_port = int(os.getenv("MINER_2_PORT", "8101"))
    miner_readable_id = "subnet1_miner_2"

    if not miner_private_key:
        logger.critical("❌ FATAL: MINER_2_PRIVATE_KEY is not set in config.env.")
        return
    
    logger.info(f"🆔 Using Miner 2: '{miner_readable_id}'")

    # --- Calculate UID hex ---
    try:
        expected_uid_bytes = miner_readable_id.encode('utf-8')
        expected_uid_hex = expected_uid_bytes.hex()
        logger.info(f"🔑 Derived On-Chain UID (Hex): {expected_uid_hex}")
    except Exception as e:
        logger.critical(f"❌ FATAL: Could not encode miner ID ('{miner_readable_id}') to derive UID: {e}")
        return

    # === Configuration for Subnet1Miner ===
    validator_result_submit_url = os.getenv("VALIDATOR_1_API_ENDPOINT")  # Use validator 1 by default
    if not validator_result_submit_url:
        logger.critical("❌ FATAL: VALIDATOR_1_API_ENDPOINT (for AI results submission) is not set.")
        return
    
    miner_host = os.getenv("SUBNET1_MINER_HOST", "0.0.0.0")

    logger.info("🖥️ --- Subnet 1 Miner 2 AI Task Server Configuration --- 🖥️")
    logger.info(f"🆔 Miner Readable ID     : [cyan]'{miner_readable_id}'[/]")
    logger.info(f"🔑 Miner Address         : [yellow]{miner_address}[/]")
    logger.info(f"👂 Listening on          : [bold blue]{miner_host}:{miner_port}[/]")
    logger.info(f"➡️ Validator Submit URL  : [link={validator_result_submit_url}]{validator_result_submit_url}[/link]")
    logger.info("-------------------------------------------------------------")

    # === Configuration for MinerAgent ===
    aptos_node_url = os.getenv("APTOS_NODE_URL")
    aptos_contract_address = os.getenv("APTOS_CONTRACT_ADDRESS")
    miner_check_interval = int(os.getenv("MINER_AGENT_CHECK_INTERVAL", "300"))

    agent_required_keys = {
        "MINER_2_PRIVATE_KEY": miner_private_key,
        "APTOS_NODE_URL": aptos_node_url,
        "APTOS_CONTRACT_ADDRESS": aptos_contract_address,
        "VALIDATOR_1_API_ENDPOINT": validator_result_submit_url
    }
    missing_agent_configs = [k for k, v in agent_required_keys.items() if not v]
    if missing_agent_configs:
        logger.critical(f"❌ FATAL: Missing Miner 2 Agent configurations in config.env: {missing_agent_configs}")
        return

    logger.info("🔗 --- Miner 2 Agent (Aptos Blockchain Interaction) Configuration --- 🔗")
    logger.info(f"🔑 Agent On-Chain UID    : [yellow]{expected_uid_hex}[/]")
    logger.info(f"🏗️ Aptos Node URL        : [cyan]{aptos_node_url}[/]")
    logger.info(f"📝 Contract Address      : [cyan]{aptos_contract_address}[/]")
    logger.info(f"🔎 Validator API (Fetch) : [link={validator_result_submit_url}]{validator_result_submit_url}[/link]")
    logger.info(f"⏱️ Check Interval (s)    : {miner_check_interval}")
    logger.info("----------------------------------------------------------------------")

    # Note: Miner Agent temporarily disabled (Cardano-specific code)
    logger.info("ℹ️ Miner Agent temporarily disabled (requires Aptos-specific implementation)")

    # --- Initialize processes --- 
    try:
        logger.info(f"🛠️ Initializing Subnet1Miner 2 Server ('{miner_readable_id}')...")
        miner_server_instance = Subnet1Miner(
            validator_url=validator_result_submit_url,
            on_chain_uid_hex=expected_uid_hex,
            host=miner_host,
            port=miner_port,
            miner_id=miner_readable_id
        )
        logger.info("✅ Subnet1Miner 2 Server instance initialized.")

        # Run Miner Server and keep it running
        logger.info(f"🚀 Starting Subnet1Miner 2 server for '{miner_readable_id}' (UID: {expected_uid_hex})...")
        miner_server_instance.run()  # This will block and keep running
        
    except Exception as e:
        logger.exception(f"💥 An unexpected error occurred during miner 2 process startup or execution: {e}")
    finally:
        logger.info("🛑 Miner 2 processes cleanup finished.")


# --- Main execution point --- 
if __name__ == "__main__":
    try:
        logger.info("🚦 Starting Miner 2 main asynchronous execution...")
        asyncio.run(run_miner2_processes())
    except KeyboardInterrupt:
        logger.info("👋 Miner 2 processes interrupted by user (Ctrl+C).")
    except Exception as main_err:
        logger.exception(f"💥 Critical error in miner 2 main execution block: {main_err}")
    finally:
        logger.info("🏁 Miner 2 script finished.") 