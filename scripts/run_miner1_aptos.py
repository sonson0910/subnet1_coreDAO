#!/usr/bin/env python3
"""
Aptos Miner 1 Runner Script for Subnet1
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
    from mt_aptos.agent.miner_agent import MinerAgent
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


async def run_miner1_processes():
    """Async function to configure and run Miner 1 processes for Aptos."""
    logger.info("⛏️ --- Starting Aptos Miner 1 Configuration & Processes --- ⛏️")

    # === Miner 1 Configuration ===
    miner_private_key = os.getenv("MINER_1_PRIVATE_KEY")
    miner_address = os.getenv("MINER_1_ADDRESS")
    miner_api_endpoint = os.getenv("MINER_1_API_ENDPOINT")
    miner_port = int(os.getenv("MINER_1_PORT", "8100"))
    miner_readable_id = "subnet1_miner_1"
    # Use short UID to match blockchain registration
    miner_uid_short = "miner_1"

    if not miner_private_key:
        logger.critical("❌ FATAL: MINER_1_PRIVATE_KEY is not set in config.env.")
        return
    
    logger.info(f"🆔 Using Miner 1: '{miner_readable_id}' (UID: {miner_uid_short})")

    # --- Calculate UID hex (use short UID for blockchain compatibility) ---
    try:
        expected_uid_bytes = miner_uid_short.encode('utf-8')
        expected_uid_hex = expected_uid_bytes.hex()
        logger.info(f"🔑 Derived On-Chain UID (Hex): {expected_uid_hex}")
    except Exception as e:
        logger.critical(f"❌ FATAL: Could not encode miner UID ('{miner_uid_short}') to derive UID: {e}")
        return

    # === Configuration for Subnet1Miner ===
    validator_result_submit_url = os.getenv("VALIDATOR_1_API_ENDPOINT")  # Use validator 1 by default
    if not validator_result_submit_url:
        logger.critical("❌ FATAL: VALIDATOR_1_API_ENDPOINT (for AI results submission) is not set.")
        return
    
    miner_host = os.getenv("SUBNET1_MINER_HOST", "0.0.0.0")

    logger.info("🖥️ --- Subnet 1 Miner 1 AI Task Server Configuration --- 🖥️")
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
        "MINER_1_PRIVATE_KEY": miner_private_key,
        "APTOS_NODE_URL": aptos_node_url,
        "APTOS_CONTRACT_ADDRESS": aptos_contract_address,
        "VALIDATOR_1_API_ENDPOINT": validator_result_submit_url
    }
    missing_agent_configs = [k for k, v in agent_required_keys.items() if not v]
    if missing_agent_configs:
        logger.critical(f"❌ FATAL: Missing Miner 1 Agent configurations in config.env: {missing_agent_configs}")
        return

    logger.info("🔗 --- Miner 1 Agent (Aptos Blockchain Interaction) Configuration --- 🔗")
    logger.info(f"🔑 Agent On-Chain UID    : [yellow]{expected_uid_hex}[/]")
    logger.info(f"🏗️ Aptos Node URL        : [cyan]{aptos_node_url}[/]")
    logger.info(f"📝 Contract Address      : [cyan]{aptos_contract_address}[/]")
    logger.info(f"🔎 Validator API (Fetch) : [link={validator_result_submit_url}]{validator_result_submit_url}[/link]")
    logger.info(f"⏱️ Check Interval (s)    : {miner_check_interval}")
    logger.info("----------------------------------------------------------------------")

    # Load Aptos account for Miner Agent
    miner_account: Optional[Account] = None
    try:
        logger.info(f"🔑 Loading Aptos account for Miner 1 Agent...")
        if not miner_private_key:
            raise ValueError("MINER_1_PRIVATE_KEY is required")
            
        # Create Aptos account from private key
        miner_account = Account.load_key(miner_private_key)
        logger.info(f"✅ Miner 1 Agent Aptos account loaded successfully. Address: {miner_account.address()}")
        
    except Exception as key_err:
        logger.exception(f"💥 FATAL: Failed to load Aptos account for Miner 1 Agent: {key_err}")
        return

    # --- Initialize processes --- 
    miner_agent_instance: Optional[MinerAgent] = None
    try:
        logger.info("🛠️ Initializing Miner 1 Agent instance...")
        
        # Note: MinerAgent expects ExtendedSigningKey from PyCardano, not Aptos Account
        # For now, we'll skip MinerAgent initialization since it's designed for Cardano
        # TODO: Create AptosAgent for Aptos blockchain interaction
        logger.warning("⚠️ MinerAgent is designed for Cardano. Skipping agent initialization for Aptos deployment.")
        logger.warning("⚠️ Consider implementing AptosAgent for Aptos blockchain interaction.")

        logger.info(f"🛠️ Initializing Subnet1Miner 1 Server ('{miner_readable_id}')...")
        miner_server_instance = Subnet1Miner(
            validator_url=validator_result_submit_url,
            on_chain_uid_hex=expected_uid_hex,
            host=miner_host,
            port=miner_port,
            miner_id=miner_readable_id
        )
        logger.info("✅ Subnet1Miner 1 Server instance initialized.")

        # Run Miner Server
        miner_server_thread = threading.Thread(target=miner_server_instance.run, daemon=True)
        miner_server_thread.start()
        logger.info(f"🧵 Started Subnet1Miner 1 server in background thread for '{miner_readable_id}' (UID: {expected_uid_hex})...")

        # Keep the miner server running
        logger.info(f"🔄 Miner 1 Server is running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(60)  # Keep alive
            logger.debug(f"🔄 Miner 1 Server heartbeat - UID: {expected_uid_hex}")

    except Exception as e:
        logger.exception(f"💥 An unexpected error occurred during miner 1 process startup or execution: {e}")
    finally:
        if miner_agent_instance:
            await miner_agent_instance.close()
        logger.info("🛑 Miner 1 processes cleanup finished.")


# --- Main execution point --- 
if __name__ == "__main__":
    try:
        logger.info("🚦 Starting Miner 1 main asynchronous execution...")
        asyncio.run(run_miner1_processes())
    except KeyboardInterrupt:
        logger.info("👋 Miner 1 processes interrupted by user (Ctrl+C).")
    except Exception as main_err:
        logger.exception(f"💥 Critical error in miner 1 main execution block: {main_err}")
    finally:
        logger.info("🏁 Miner 1 script finished.") 