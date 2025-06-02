#!/usr/bin/env python3
"""
Aptos Miner Runner Script for Subnet1
Replaces the Cardano-based run_miner2.py with Aptos functionality
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
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# --- Import required classes --- 
try:
    from subnet1.miner import Subnet1Miner
    from mt_aptos.agent.miner_agent import MinerAgent
    from mt_aptos.config.settings import settings as sdk_settings
    from mt_aptos.keymanager.decryption_utils import decode_hotkey_account
    from mt_aptos.account import Account
except ImportError as e:
    print(f"❌ FATAL: Import Error: {e}")
    sys.exit(1)

# --- Load environment variables (.env) ---
env_path = project_root / '.env'

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
    logger.warning(f"📄 Environment file (.env) not found at {env_path}.")


async def run_miner_processes():
    """Async function to configure and run both Miner Server and Miner Agent for Aptos."""
    logger.info("⛏️ --- Starting Aptos Miner Configuration & Processes --- ⛏️")

    # === Common configuration for Miner ===
    miner_readable_id = os.getenv("SUBNET1_MINER_ID")
    if not miner_readable_id:
        logger.critical("❌ FATAL: SUBNET1_MINER_ID is not set in .env.")
        return
    logger.info(f"🆔 Read Miner ID from .env: '{miner_readable_id}'")

    # --- Calculate UID hex ---
    try:
        expected_uid_bytes = miner_readable_id.encode('utf-8')
        expected_uid_hex = expected_uid_bytes.hex()
        logger.info(f"🔑 Derived On-Chain UID (Hex): {expected_uid_hex}")
    except Exception as e:
        logger.critical(f"❌ FATAL: Could not encode SUBNET1_MINER_ID ('{miner_readable_id}') to derive UID: {e}")
        return

    # === Configuration for Subnet1Miner ===
    validator_result_submit_url = os.getenv("SUBNET1_VALIDATOR_URL")
    if not validator_result_submit_url:
        logger.critical("❌ FATAL: SUBNET1_VALIDATOR_URL (for AI results submission) is not set.")
        return
    miner_host = os.getenv("SUBNET1_MINER_HOST") or getattr(sdk_settings, 'DEFAULT_MINER_HOST', "0.0.0.0")
    miner_port = int(os.getenv("SUBNET1_MINER_PORT") or getattr(sdk_settings, 'DEFAULT_MINER_PORT', 9001))

    logger.info("🖥️ --- Subnet 1 Miner AI Task Server Configuration --- 🖥️")
    logger.info(f"🆔 Miner Readable ID     : [cyan]'{miner_readable_id}'[/]")
    logger.info(f"👂 Listening on          : [bold blue]{miner_host}:{miner_port}[/]")
    logger.info(f"➡️ Validator Submit URL  : [link={validator_result_submit_url}]{validator_result_submit_url}[/link]")
    logger.info("-------------------------------------------------------------")

    # === Configuration for MinerAgent ===
    aptos_private_key = os.getenv("APTOS_PRIVATE_KEY")
    aptos_node_url = os.getenv("APTOS_NODE_URL")
    aptos_contract_address = os.getenv("APTOS_CONTRACT_ADDRESS")
    validator_consensus_api_url = os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT")
    miner_check_interval = int(os.getenv("MINER_AGENT_CHECK_INTERVAL") or getattr(sdk_settings, 'MINER_AGENT_CHECK_INTERVAL', 300))

    agent_required_keys = {
        "APTOS_PRIVATE_KEY": aptos_private_key,
        "APTOS_NODE_URL": aptos_node_url,
        "APTOS_CONTRACT_ADDRESS": aptos_contract_address,
        "SUBNET1_VALIDATOR_API_ENDPOINT": validator_consensus_api_url
    }
    missing_agent_configs = [k for k, v in agent_required_keys.items() if not v]
    if missing_agent_configs:
        logger.critical(f"❌ FATAL: Missing Miner Agent configurations in .env: {missing_agent_configs}")
        return

    logger.info("🔗 --- Miner Agent (Aptos Blockchain Interaction) Configuration --- 🔗")
    logger.info(f"🔑 Agent On-Chain UID    : [yellow]{expected_uid_hex}[/]")
    logger.info(f"🏗️ Aptos Node URL        : [cyan]{aptos_node_url}[/]")
    logger.info(f"📝 Contract Address      : [cyan]{aptos_contract_address}[/]")
    logger.info(f"🔎 Validator API (Fetch) : [link={validator_consensus_api_url}]{validator_consensus_api_url}[/link]")
    logger.info(f"⏱️ Check Interval (s)    : {miner_check_interval}")
    logger.info("----------------------------------------------------------------------")

    # Load Aptos account for Miner Agent
    miner_account: Optional[Account] = None
    try:
        logger.info(f"🔑 Loading Aptos account for Miner Agent...")
        if not aptos_private_key:
            raise ValueError("APTOS_PRIVATE_KEY is required")
            
        # Create Aptos account from private key
        miner_account = Account.load_key(aptos_private_key)
        logger.info(f"✅ Miner Agent Aptos account loaded successfully. Address: {miner_account.address()}")
        
    except Exception as key_err:
        logger.exception(f"💥 FATAL: Failed to load Aptos account for Miner Agent: {key_err}")
        return

    # --- Initialize processes --- 
    miner_agent_instance: Optional[MinerAgent] = None
    try:
        logger.info("🛠️ Initializing Miner Agent instance...")
        miner_agent_instance = MinerAgent(
            miner_uid_hex=expected_uid_hex,
            config=dict(sdk_settings),
            miner_account=miner_account,
            aptos_node_url=aptos_node_url,
            contract_address=aptos_contract_address
        )
        logger.info("✅ Miner Agent instance initialized.")

        logger.info(f"🛠️ Initializing Subnet1Miner Server ('{miner_readable_id}')...")
        miner_server_instance = Subnet1Miner(
            validator_url=validator_result_submit_url,
            on_chain_uid_hex=expected_uid_hex,
            host=miner_host,
            port=miner_port,
            miner_id=miner_readable_id
        )
        logger.info("✅ Subnet1Miner Server instance initialized.")

        # Run Miner Server
        miner_server_thread = threading.Thread(target=miner_server_instance.run, daemon=True)
        miner_server_thread.start()
        logger.info(f"🧵 Started Subnet1Miner server in background thread for '{miner_readable_id}' (UID: {expected_uid_hex})...")

        await asyncio.sleep(5)

        # Run Miner Agent
        logger.info(f"▶️ Starting Miner Agent main loop for UID {expected_uid_hex}...")
        await miner_agent_instance.run(
            validator_api_url=validator_consensus_api_url,
            check_interval_seconds=miner_check_interval
        )
        logger.info("⏹️ Miner Agent main loop finished.")

    except Exception as e:
        logger.exception(f"💥 An unexpected error occurred during miner process startup or execution: {e}")
    finally:
        if miner_agent_instance:
            await miner_agent_instance.close()
        logger.info("🛑 Miner processes cleanup finished.")


# --- Main execution point --- 
if __name__ == "__main__":
    try:
        logger.info("🚦 Starting main asynchronous execution...")
        asyncio.run(run_miner_processes())
    except KeyboardInterrupt:
        logger.info("👋 Miner processes interrupted by user (Ctrl+C).")
    except Exception as main_err:
        logger.exception(f"💥 Critical error in main execution block: {main_err}")
    finally:
        logger.info("🏁 Miner script finished.") 