#!/usr/bin/env python3
"""
Core Blockchain Miner Runner Script for Subnet1
Migrated from Aptos to Core blockchain functionality
"""

import os
import sys
import logging
import asyncio
import time
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from rich.logging import RichHandler

# --- Add project root to sys.path ---
project_root = Path(__file__).parent.parent  # Go to subnet1_aptos root
sys.path.insert(0, str(project_root))

# Add moderntensor_aptos path (parent directory)
moderntensor_path = project_root.parent / "moderntensor_aptos"
sys.path.insert(0, str(moderntensor_path))

# Also add the parent directory to ensure mt_core is found
parent_path = project_root.parent
sys.path.insert(0, str(parent_path))

print(f"🔍 Project root: {project_root}")
print(f"🔍 ModernTensor path: {moderntensor_path}")
print(f"🔍 ModernTensor exists: {moderntensor_path.exists()}")
print(f"🔍 Parent path: {parent_path}")
print(f"🔍 Python path: {sys.path[:3]}")

# --- Import required classes ---
try:
    from subnet1.miner import Subnet1Miner
    from mt_core.account import Account
except ImportError as e:
    print(f"❌ FATAL: Import Error: {e}")
    print(f"🔍 Python path: {sys.path[:3]}")
    sys.exit(1)

# --- Load environment variables from .env ---
env_path = project_root / ".env"  # Look for .env in subnet1_aptos root

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


def run_miner_process():
    """Function to configure and run Subnet1Miner for Core blockchain."""

    # 🔥 CYBERPUNK UI: Miner Startup Header
    try:
        from moderntensor_aptos.mt_core.cli.cyberpunk_ui_extended import (
            create_cyberpunk_console,
        )

        console = create_cyberpunk_console()

        # Epic miner startup header
        console.print()
        console.print("[bold bright_green]" + "▀" * 80 + "[/bold bright_green]")
        console.print("[bold bright_cyan]" + "█" * 80 + "[/bold bright_cyan]")
        console.print(
            "[bold bright_yellow on bright_green]⛏️🤖 QUANTUM MINER NEURAL CORE ACTIVATION 🤖⛏️[/bold bright_yellow on bright_green]".center(
                80
            )
        )
        console.print("[bold bright_magenta]" + "░▒▓█" * 20 + "[/bold bright_magenta]")
        console.print()
        console.print(
            "[bold bright_cyan]║[/bold bright_cyan] [bright_yellow]🚀 INITIALIZING MINING MATRIX...[/bright_yellow] [bold bright_cyan]║[/bold bright_cyan]"
        )
        console.print(
            "[bold bright_cyan]║[/bold bright_cyan] [bright_green]● AI CORES:[/bright_green] [bright_white]ONLINE[/bright_white] [bright_cyan]● QUANTUM ENGINE:[/bright_cyan] [bright_white]READY[/bright_white] [bold bright_cyan]║[/bold bright_cyan]"
        )
        console.print(
            "[bold bright_cyan]║[/bold bright_cyan] [bright_magenta]● NEURAL NET:[/bright_magenta] [bright_white]SYNCHRONIZED[/bright_white] [bright_yellow]● MINING AI:[/bright_yellow] [bright_white]ACTIVE[/bright_white] [bold bright_cyan]║[/bold bright_cyan]"
        )
        console.print()
        console.print("[bold bright_green]" + "▄" * 80 + "[/bold bright_green]")
        console.print()
    except ImportError:
        pass

    logger.info("⛏️ --- Starting Core Blockchain Miner Configuration & Processes --- ⛏️")

    # === Get miner configuration from environment ===
    # Check for MINER_ID env var, default to miner1 if not specified
    miner_id = os.getenv("MINER_ID", "1")  # Can be "1" or "2"

    # Use specific miner configuration based on MINER_ID
    if miner_id == "2":
        miner_private_key = os.getenv("MINER_2_PRIVATE_KEY")
        miner_address = os.getenv("MINER_2_ADDRESS")
        miner_api_endpoint = os.getenv("MINER_2_API_ENDPOINT")
        miner_port = int(
            os.getenv("MINER_2_PORT", "8102")
        )  # Fixed: Miner 2 should be 8102
        miner_readable_id = f"subnet1_miner_{miner_id}"
    else:  # Default to miner 1
        miner_private_key = os.getenv("MINER_1_PRIVATE_KEY")
        miner_address = os.getenv("MINER_1_ADDRESS")
        miner_api_endpoint = os.getenv("MINER_1_API_ENDPOINT")
        miner_port = int(
            os.getenv("MINER_1_PORT", "8101")
        )  # Fixed: Miner 1 should be 8101
        miner_readable_id = f"subnet1_miner_{miner_id}"

    if not miner_private_key:
        logger.critical(f"❌ FATAL: MINER_{miner_id}_PRIVATE_KEY is not set in .env.")
        return

    logger.info(f"🆔 Using Miner {miner_id}: '{miner_readable_id}'")

    # --- Calculate UID hex ---
    try:
        expected_uid_bytes = miner_readable_id.encode("utf-8")
        expected_uid_hex = expected_uid_bytes.hex()
        logger.info(f"🔑 Derived On-Chain UID (Hex): {expected_uid_hex}")
        logger.info(f"🔑 Smart Contract uses Address as ID: {miner_address}")
    except Exception as e:
        logger.critical(
            f"❌ FATAL: Could not encode miner ID ('{miner_readable_id}') to derive UID: {e}"
        )
        return

    # === Configuration for Subnet1Miner ===
    # Choose which validator to submit results to based on environment or default to validator 1
    target_validator_id = os.getenv(
        "TARGET_VALIDATOR_ID", "1"
    )  # Can target validator 1 or 2

    if target_validator_id == "2":
        validator_result_submit_url = os.getenv("VALIDATOR_2_API_ENDPOINT")
        validator_name = "Validator 2"
    else:
        validator_result_submit_url = os.getenv("VALIDATOR_1_API_ENDPOINT")
        validator_name = "Validator 1"

    if not validator_result_submit_url:
        logger.critical(
            f"❌ FATAL: {validator_name.upper().replace(' ', '_')}_API_ENDPOINT (for AI results submission) is not set."
        )
        return

    miner_host = os.getenv("SUBNET1_MINER_HOST", "0.0.0.0")

    # 🔥 CYBERPUNK UI: Miner Configuration Display
    try:
        console = create_cyberpunk_console()

        console.print()
        console.print(
            "[bold bright_cyan]╔══════════════════════ MINER CONFIGURATION MATRIX ══════════════════════╗[/bold bright_cyan]"
        )
        console.print(
            "[bold bright_cyan]║[/bold bright_cyan]                                                                        [bold bright_cyan]║[/bold bright_cyan]"
        )
        console.print(
            f"[bold bright_cyan]║[/bold bright_cyan] [bright_yellow]🆔 MINER UNIT ID:[/bright_yellow] [bright_white]{miner_readable_id}[/bright_white] [bold bright_cyan]║[/bold bright_cyan]"
        )
        console.print(
            f"[bold bright_cyan]║[/bold bright_cyan] [bright_green]🔑 BLOCKCHAIN ADDRESS:[/bright_green] [bright_yellow]{miner_address[:30]}...[/bright_yellow] [bold bright_cyan]║[/bold bright_cyan]"
        )
        console.print(
            f"[bold bright_cyan]║[/bold bright_cyan] [bright_magenta]👂 NEURAL INTERFACE:[/bright_magenta] [bright_white]{miner_host}:{miner_port}[/bright_white] [bold bright_cyan]║[/bold bright_cyan]"
        )
        console.print(
            f"[bold bright_cyan]║[/bold bright_cyan] [bright_cyan]🎯 TARGET VALIDATOR:[/bright_cyan] [bright_white]{validator_name}[/bright_white] [bold bright_cyan]║[/bold bright_cyan]"
        )
        console.print(
            f"[bold bright_cyan]║[/bold bright_cyan] [bright_red]➡️ QUANTUM UPLINK:[/bright_red] [bright_white]{validator_result_submit_url[:40]}...[/bright_white] [bold bright_cyan]║[/bold bright_cyan]"
        )
        console.print(
            "[bold bright_cyan]║[/bold bright_cyan]                                                                        [bold bright_cyan]║[/bold bright_cyan]"
        )
        console.print(
            "[bold bright_cyan]╚════════════════════════════════════════════════════════════════════════╝[/bold bright_cyan]"
        )
        console.print()
    except:
        pass

    logger.info("🖥️ --- Subnet 1 Miner AI Task Server Configuration --- 🖥️")
    logger.info(f"🆔 Miner Readable ID     : [cyan]'{miner_readable_id}'[/]")
    logger.info(f"🔑 Miner Address         : [yellow]{miner_address}[/]")
    logger.info(f"👂 Listening on          : [bold blue]{miner_host}:{miner_port}[/]")
    logger.info(f"🎯 Target Validator      : [cyan]{validator_name}[/]")
    logger.info(
        f"➡️ Validator Submit URL  : [link={validator_result_submit_url}]{validator_result_submit_url}[/link]"
    )
    logger.info("-------------------------------------------------------------")

    # === Configuration for MinerAgent ===
    core_node_url = os.getenv("CORE_NODE_URL")
    core_contract_address = os.getenv("CORE_CONTRACT_ADDRESS")
    miner_check_interval = int(os.getenv("MINER_AGENT_CHECK_INTERVAL", "300"))

    # Basic validation for miner requirements
    required_configs = {
        f"MINER_{miner_id}_PRIVATE_KEY": miner_private_key,
        f"VALIDATOR_{target_validator_id}_API_ENDPOINT": validator_result_submit_url,
    }
    missing_configs = [k for k, v in required_configs.items() if not v]
    if missing_configs:
        logger.critical(
            f"❌ FATAL: Missing Miner configurations in .env: {missing_configs}"
        )
        return

    logger.info("🔗 --- Final Miner Configuration --- 🔗")
    logger.info(f"🔑 Miner On-Chain UID    : [yellow]{expected_uid_hex}[/]")
    logger.info(f"🎯 Target Validator      : [cyan]{validator_name}[/]")
    logger.info(
        f"➡️ Submit Results To     : [link={validator_result_submit_url}]{validator_result_submit_url}[/link]"
    )
    logger.info(
        "----------------------------------------------------------------------"
    )

    # Load Core blockchain account for Miner
    miner_account: Optional[Account] = None
    try:
        logger.info(f"🔑 Loading Core blockchain account for Miner...")
        if not miner_private_key:
            raise ValueError(f"MINER_{miner_id}_PRIVATE_KEY is required")

        # Create Core blockchain account from private key
        miner_account = Account.from_key(miner_private_key)
        logger.info(
            f"✅ Miner Core blockchain account loaded successfully. Address: {miner_account.address}"
        )

    except Exception as key_err:
        logger.exception(
            f"💥 FATAL: Failed to load Core blockchain account for Miner: {key_err}"
        )
        return

    # --- Initialize and run miner ---
    try:
        logger.info(f"🛠️ Initializing Subnet1Miner ('{miner_readable_id}')...")

        # Create Subnet1Miner instance - this handles both AI tasks and basic blockchain interaction
        miner_instance = Subnet1Miner(
            validator_url=validator_result_submit_url,
            on_chain_uid_hex=expected_uid_hex,
            host=miner_host,
            port=miner_port,
            miner_id=miner_readable_id,
        )
        logger.info("✅ Subnet1Miner instance initialized.")

        # 🔥 CYBERPUNK UI: Miner Launch Status
        try:
            console = create_cyberpunk_console()
            console.print()
            console.print(
                "[bold bright_yellow]"
                + "◄" * 40
                + " MINER LAUNCH SEQUENCE "
                + "►" * 40
                + "[/bold bright_yellow]"
            )
            console.print()
            console.print(
                f"[bright_cyan]🚀 STARTING MINER:[/bright_cyan] [bright_white]{expected_uid_hex[:20]}...[/bright_white]"
            )
            console.print(
                f"[bright_green]👂 NEURAL INTERFACE:[/bright_green] [bright_yellow]{miner_host}:{miner_port}[/bright_yellow]"
            )
            console.print(
                f"[bright_magenta]🎯 QUANTUM UPLINK:[/bright_magenta] [bright_white]{validator_result_submit_url[:50]}...[/bright_white]"
            )
            console.print(
                f"[bright_red]⚡ STATUS:[/bright_red] [blink bright_green]ONLINE & MINING[/blink bright_green] 🔥"
            )
            console.print()
            console.print("[bold bright_yellow]" + "◄" * 97 + "[/bold bright_yellow]")
            console.print()
        except:
            pass

        logger.info(f"▶️ Starting Subnet1Miner main loop for UID {expected_uid_hex}...")
        logger.info(f"👂 Listening on: {miner_host}:{miner_port}")
        logger.info(f"🎯 Submitting results to: {validator_result_submit_url}")

        # Run the miner - this will start the FastAPI server and handle incoming tasks
        # Note: This is a blocking call that runs the server
        miner_instance.run()

        logger.info("⏹️ Subnet1Miner main loop finished.")

    except Exception as e:
        logger.exception(
            f"💥 An unexpected error occurred during miner startup or execution: {e}"
        )
    finally:
        logger.info("🛑 Miner process cleanup finished.")


# --- Main execution point ---
if __name__ == "__main__":
    try:
        logger.info("🚦 Starting main execution...")
        run_miner_process()
    except KeyboardInterrupt:
        logger.info("👋 Miner process interrupted by user (Ctrl+C).")
    except Exception as main_err:
        logger.exception(f"💥 Critical error in main execution block: {main_err}")
    finally:
        logger.info("🏁 Miner script finished.")
