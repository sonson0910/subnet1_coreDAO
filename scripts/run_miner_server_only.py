#!/usr/bin/env python3
"""
Core blockchain Miner Server Only - No Agent
Chỉ chạy miner server để nhận task từ validator, không chạy agent
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
sys.path.insert(
    0, str(project_root.parent / "moderntensor_aptos")
)  # Add moderntensor_aptos path for mt_core imports

# --- Import required classes ---
try:
    from subnet1.miner import Subnet1Miner
    from moderntensor_aptos.mt_core.config.settings import settings as sdk_settings
    from moderntensor_aptos.mt_core.account import Account
except ImportError as e:
    print(f"❌ FATAL: Import Error: {e}")
    sys.exit(1)

# --- Load environment variables from config.env ---
env_path = project_root.parent / "config.env"  # Look for config.env in root

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
    logger.warning(f"📄 Environment file (config.env) not found at {env_path}.")


def run_miner_server_only():
    """Function to configure and run only Miner Server (no Agent)."""
    logger.info("⛏️ --- Starting Core blockchain Miner Server Only (No Agent) --- ⛏️")

    # === Get miner configuration from environment ===
    # Check for MINER_ID env var, default to miner1 if not specified
    miner_id = os.getenv("MINER_ID", "1")  # Can be "1" or "2"

    # Use specific miner configuration based on MINER_ID
    if miner_id == "2":
        miner_private_key = os.getenv("MINER_2_PRIVATE_KEY")
        miner_address = os.getenv("MINER_2_ADDRESS")
        miner_api_endpoint = os.getenv("MINER_2_API_ENDPOINT")
        miner_port = int(os.getenv("MINER_2_PORT", "8101"))
        miner_readable_id = (
            f"miner_{miner_id}"  # Use simple format to match validator expectation
        )
    else:  # Default to miner 1
        miner_private_key = os.getenv("MINER_1_PRIVATE_KEY")
        miner_address = os.getenv("MINER_1_ADDRESS")
        miner_api_endpoint = os.getenv("MINER_1_API_ENDPOINT")
        miner_port = int(os.getenv("MINER_1_PORT", "8100"))
        miner_readable_id = (
            f"miner_{miner_id}"  # Use simple format to match validator expectation
        )

    if not miner_private_key:
        logger.critical(
            f"❌ FATAL: MINER_{miner_id}_PRIVATE_KEY is not set in config.env."
        )
        return

    logger.info(f"🆔 Using Miner {miner_id}: '{miner_readable_id}'")

    # --- Calculate UID hex ---
    try:
        expected_uid_bytes = miner_readable_id.encode("utf-8")
        expected_uid_hex = expected_uid_bytes.hex()
        logger.info(f"🔑 Derived On-Chain UID (Hex): {expected_uid_hex}")
    except Exception as e:
        logger.critical(
            f"❌ FATAL: Could not encode miner ID ('{miner_readable_id}') to derive UID: {e}"
        )
        return

    # === Configuration for Subnet1Miner ===
    validator_result_submit_url = os.getenv(
        "VALIDATOR_1_API_ENDPOINT"
    )  # Use validator 1 by default
    if not validator_result_submit_url:
        logger.critical(
            "❌ FATAL: VALIDATOR_1_API_ENDPOINT (for AI results submission) is not set."
        )
        return

    miner_host = os.getenv("SUBNET1_MINER_HOST", "0.0.0.0")

    logger.info("🖥️ --- Subnet 1 Miner AI Task Server Configuration --- 🖥️")
    logger.info(f"🆔 Miner Readable ID     : [cyan]'{miner_readable_id}'[/]")
    logger.info(f"🔑 Miner Address         : [yellow]{miner_address}[/]")
    logger.info(f"👂 Listening on          : [bold blue]{miner_host}:{miner_port}[/]")
    logger.info(
        f"➡️ Validator Submit URL  : [link={validator_result_submit_url}]{validator_result_submit_url}[/link]"
    )
    logger.info("-------------------------------------------------------------")
    logger.info("🚫 Miner Agent is DISABLED - Running server only")
    logger.info("-------------------------------------------------------------")

    # --- Initialize miner server only ---
    try:
        logger.info(f"🛠️ Initializing Subnet1Miner Server ('{miner_readable_id}')...")
        miner_server_instance = Subnet1Miner(
            validator_url=validator_result_submit_url,
            on_chain_uid_hex=expected_uid_hex,
            host=miner_host,
            port=miner_port,
            miner_id=miner_readable_id,
        )
        logger.info("✅ Subnet1Miner Server instance initialized.")

        # Run Miner Server in main thread (blocking)
        logger.info(
            f"▶️ Starting Subnet1Miner server for '{miner_readable_id}' (UID: {expected_uid_hex})..."
        )
        logger.info("🎯 Server will listen for tasks from validators")
        logger.info("📋 Press Ctrl+C to stop the server")

        # Run server (this will block)
        miner_server_instance.run()

    except KeyboardInterrupt:
        logger.info("👋 Miner server stopped by user (Ctrl+C)")
    except Exception as e:
        logger.exception(
            f"💥 An unexpected error occurred during miner server startup: {e}"
        )
    finally:
        logger.info("🛑 Miner server cleanup finished.")


# --- Main execution point ---
if __name__ == "__main__":
    try:
        logger.info("🚦 Starting Core blockchain miner server only...")
        run_miner_server_only()
    except KeyboardInterrupt:
        logger.info("👋 Miner server interrupted by user (Ctrl+C).")
    except Exception as main_err:
        logger.exception(f"💥 Critical error in main execution block: {main_err}")
    finally:
        logger.info("🏁 Miner server script finished.")
