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
from rich.console import Console

# --- Add project root to sys.path ---
# Current file: /Users/sonson/Documents/code/moderntensor_core/subnet1_aptos/scripts/run_validator_core.py
# We need: /Users/sonson/Documents/code/moderntensor_core/subnet1_aptos (project_root)
# And: /Users/sonson/Documents/code/moderntensor_core (for moderntensor_aptos)

script_path = Path(__file__).resolve()  # Full absolute path
project_root = script_path.parent.parent  # subnet1_aptos directory
core_root = project_root.parent  # moderntensor_core directory

# Add paths in correct order
sys.path.insert(0, str(core_root))  # For moderntensor_aptos import
sys.path.insert(0, str(project_root))  # For subnet1.validator import

# Debug: Verify paths are correct
logger = logging.getLogger(__name__)
logger.debug(
    f"Project paths - Script: {script_path}, Core: {core_root}, Project: {project_root}"
)

# --- Import required classes ---
try:
    from subnet1.validator import Subnet1Validator
    from moderntensor_aptos.mt_core.config.settings import settings as sdk_settings
    from moderntensor_aptos.mt_core.account import Account
except ImportError as e:
    print(f"❌ FATAL: Import Error: {e}")
    print("Make sure moderntensor_aptos is properly installed and in path")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# --- Load environment variables (.env) ---
env_path = project_root / ".env"

# Force color output in terminals
os.environ["FORCE_COLOR"] = "1"
os.environ["CLICOLOR"] = "1"
os.environ["CLICOLOR_FORCE"] = "1"

# --- Configure Logging with RichHandler ---
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)

# 🔥 CYBERPUNK CONSOLE CONFIGURATION 🔥
console = Console(
    force_terminal=True,
    force_interactive=True,
    color_system="truecolor",  # Full color support for cyberpunk
    width=120,
    legacy_windows=False,
    style="bold bright_green on black",  # Cyberpunk terminal style
)

# 🤖 CYBERPUNK RICH HANDLER 🤖
rich_handler = RichHandler(
    console=console,
    show_time=True,
    show_level=True,
    show_path=False,
    markup=True,  # Enable full markup for cyberpunk effects
    rich_tracebacks=True,
    log_time_format="[bold cyan][%Y-%m-%d %H:%M:%S][/]",
)

logging.basicConfig(
    level=log_level, format="%(message)s", datefmt="[%X]", handlers=[rich_handler]
)

# Suppress noisy debug logs from web3 and other libraries
logging.getLogger("web3.providers.HTTPProvider").setLevel(logging.INFO)
logging.getLogger("web3.RequestManager").setLevel(logging.INFO)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# --- Load environment variables (after logger is configured) ---
if env_path.exists():
    logger.info(f"📄 Loading environment variables from: {env_path}")
    load_dotenv(dotenv_path=env_path, override=True)
else:
    logger.warning(f"📄 Environment file (.env) not found at {env_path}.")


async def run_validator_process():
    """Async function to configure and run Subnet1 Validator for Core blockchain."""

    # 🔥 CYBERPUNK UI: Enhanced Validator Startup Header
    try:
        from moderntensor_aptos.mt_core.cli.cyberpunk_ui_extended import (
            create_cyberpunk_console,
        )

        cyberpunk_console = create_cyberpunk_console()

        # Epic validator startup header with enhanced design
        cyberpunk_console.print()
        cyberpunk_console.print("[bold bright_blue]" + "▀" * 80 + "[/bold bright_blue]")
        cyberpunk_console.print("[bold bright_cyan]" + "█" * 80 + "[/bold bright_cyan]")
        cyberpunk_console.print(
            "[bold bright_yellow on bright_blue]🛡️🤖 QUANTUM VALIDATOR NEURAL CORE ONLINE 🤖🛡️[/bold bright_yellow on bright_blue]".center(
                80
            )
        )
        cyberpunk_console.print(
            "[bold bright_magenta]" + "░▒▓█" * 20 + "[/bold bright_magenta]"
        )
        cyberpunk_console.print()
        cyberpunk_console.print(
            "[bold bright_cyan]║[/bold bright_cyan] [bright_yellow]🚀 INITIALIZING VALIDATION MATRIX...[/bright_yellow] [bold bright_cyan]║[/bold bright_cyan]"
        )
        cyberpunk_console.print(
            "[bold bright_cyan]║[/bold bright_cyan] [bright_green]● CONSENSUS ENGINE:[/bright_green] [bright_white]ONLINE[/bright_white] [bright_cyan]● NEURAL NET:[/bright_cyan] [bright_white]READY[/bright_white] [bold bright_cyan]║[/bold bright_cyan]"
        )
        cyberpunk_console.print(
            "[bold bright_cyan]║[/bold bright_cyan] [bright_magenta]● SCORING AI:[/bright_magenta] [bright_white]SYNCHRONIZED[/bright_white] [bright_yellow]● QUANTUM CORE:[/bright_yellow] [bright_white]ACTIVE[/bright_white] [bold bright_cyan]║[/bold bright_cyan]"
        )
        cyberpunk_console.print()
        cyberpunk_console.print("[bold bright_blue]" + "▄" * 80 + "[/bold bright_blue]")
        cyberpunk_console.print()
    except ImportError:
        # Fallback to existing cyberpunk banner
        console.print("\n" + "▓" * 100, style="bold bright_magenta")
        console.print("█" * 100, style="bold bright_cyan on black")
        console.print(
            "██  ⚡ MODERNTENSOR CYBERPUNK VALIDATOR CORE ⚡  ██",
            style="bold bright_yellow on bright_magenta",
            justify="center",
        )
        console.print(
            "██    🤖 NEURAL NETWORK CONSENSUS ENGINE 🤖    ██",
            style="bold bright_green on black",
            justify="center",
        )
        console.print("█" * 100, style="bold bright_cyan on black")
        console.print("▓" * 100, style="bold bright_magenta")
        console.print(
            "  🔥 INITIALIZING QUANTUM BLOCKCHAIN MATRIX 🔥  ",
            style="bold bright_red blink",
            justify="center",
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

    # 🔥 CYBERPUNK UI: Enhanced Validator Configuration Display
    try:
        cyberpunk_console.print()
        cyberpunk_console.print(
            "[bold bright_cyan]╔════════════════════ VALIDATOR CONFIGURATION MATRIX ════════════════════╗[/bold bright_cyan]"
        )
        cyberpunk_console.print(
            "[bold bright_cyan]║[/bold bright_cyan]                                                                        [bold bright_cyan]║[/bold bright_cyan]"
        )
        cyberpunk_console.print(
            f"[bold bright_cyan]║[/bold bright_cyan] [bright_yellow]🆔 VALIDATOR UNIT ID:[/bright_yellow] [bright_white]{validator_readable_id}[/bright_white] [bold bright_cyan]║[/bold bright_cyan]"
        )
        cyberpunk_console.print(
            f"[bold bright_cyan]║[/bold bright_cyan] [bright_green]🔑 BLOCKCHAIN ADDRESS:[/bright_green] [bright_yellow]{validator_address[:30]}...[/bright_yellow] [bold bright_cyan]║[/bold bright_cyan]"
        )
        cyberpunk_console.print(
            f"[bold bright_cyan]║[/bold bright_cyan] [bright_magenta]🔑 ON-CHAIN UID:[/bright_magenta] [bright_white]{expected_uid_hex[:30]}...[/bright_white] [bold bright_cyan]║[/bold bright_cyan]"
        )
        cyberpunk_console.print(
            f"[bold bright_cyan]║[/bold bright_cyan] [bright_cyan]🏗️ CORE NODE URL:[/bright_cyan] [bright_white]{core_node_url[:35]}...[/bright_white] [bold bright_cyan]║[/bold bright_cyan]"
        )
        cyberpunk_console.print(
            f"[bold bright_cyan]║[/bold bright_cyan] [bright_red]📝 CONTRACT ADDRESS:[/bright_red] [bright_white]{core_contract_address[:30]}...[/bright_white] [bold bright_cyan]║[/bold bright_cyan]"
        )
        cyberpunk_console.print(
            f"[bold bright_cyan]║[/bold bright_cyan] [bright_yellow]👂 NEURAL INTERFACE:[/bright_yellow] [bright_white]{validator_host}:{validator_port}[/bright_white] [bold bright_cyan]║[/bold bright_cyan]"
        )
        cyberpunk_console.print(
            f"[bold bright_cyan]║[/bold bright_cyan] [bright_blue]🌐 API ENDPOINT:[/bright_blue] [bright_white]{validator_api_endpoint[:40]}...[/bright_white] [bold bright_cyan]║[/bold bright_cyan]"
        )
        cyberpunk_console.print(
            "[bold bright_cyan]║[/bold bright_cyan]                                                                        [bold bright_cyan]║[/bold bright_cyan]"
        )
        cyberpunk_console.print(
            "[bold bright_cyan]╚════════════════════════════════════════════════════════════════════════╝[/bold bright_cyan]"
        )
        cyberpunk_console.print()
    except:
        # Fallback to existing cyberpunk configuration matrix
        console.print(f"\n┌{'─' * 80}┐", style="bold bright_cyan")
        console.print(
            f"│ ⚡ [bold bright_magenta]CYBER VALIDATOR NODE {validator_id} NEURAL CONFIG[/] ⚡ │",
            style="bold bright_cyan",
            justify="center",
        )
    console.print(f"├{'─' * 80}┤", style="bold bright_cyan")
    console.print(
        f"│ 🤖 [bold bright_green]Node Identity    :[/] [bright_yellow]{validator_readable_id:<40}[/] │",
        style="bold bright_cyan",
    )
    console.print(
        f"│ 🔑 [bold bright_green]Wallet Address   :[/] [bright_cyan]{validator_address:<40}[/] │",
        style="bold bright_cyan",
    )
    console.print(
        f"│ ⚡ [bold bright_green]Neural UID       :[/] [bright_magenta]{expected_uid_hex:<40}[/] │",
        style="bold bright_cyan",
    )
    console.print(
        f"│ 🌐 [bold bright_green]Blockchain RPC   :[/] [bright_blue]{core_node_url:<40}[/] │",
        style="bold bright_cyan",
    )
    console.print(
        f"│ 📜 [bold bright_green]Smart Contract   :[/] [bright_yellow]{core_contract_address:<40}[/] │",
        style="bold bright_cyan",
    )
    console.print(
        f"│ 🔗 [bold bright_green]API Neural Link  :[/] [bright_green]{validator_api_endpoint:<40}[/] │",
        style="bold bright_cyan",
    )
    console.print(
        f"│ 🚀 [bold bright_green]Network Interface:[/] [bold bright_red]{validator_host}:{validator_port:<37}[/] │",
        style="bold bright_cyan",
    )
    console.print(f"└{'─' * 80}┘", style="bold bright_cyan")
    console.print(
        "🔥 [bold bright_red blink]CYBERPUNK NEURAL MATRIX ONLINE[/] 🔥",
        justify="center",
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
        from moderntensor_aptos.mt_core.core.datatypes import ValidatorInfo
        from moderntensor_aptos.mt_core.core_client.contract_client import (
            ModernTensorCoreClient,
        )

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

        # 🔥 CYBERPUNK UI: Enhanced Validator Launch Status
        try:
            cyberpunk_console.print()
            cyberpunk_console.print(
                "[bold bright_blue]"
                + "◄" * 40
                + " VALIDATOR LAUNCH SEQUENCE "
                + "►" * 40
                + "[/bold bright_blue]"
            )
            cyberpunk_console.print()
            cyberpunk_console.print(
                f"[bright_cyan]🚀 STARTING VALIDATOR:[/bright_cyan] [bright_white]{validator_id}[/bright_white] [bright_yellow]({expected_uid_hex[:20]}...)[/bright_yellow]"
            )
            cyberpunk_console.print(
                f"[bright_green]🛡️ CONSENSUS MODE:[/bright_green] [bright_yellow]FLEXIBLE VALIDATION[/bright_yellow]"
            )
            cyberpunk_console.print(
                f"[bright_magenta]🌐 NEURAL INTERFACE:[/bright_magenta] [bright_white]{validator_host}:{validator_port}[/bright_white]"
            )
            cyberpunk_console.print(
                f"[bright_red]⚡ STATUS:[/bright_red] [blink bright_green]ONLINE & VALIDATING[/blink bright_green] 🔥"
            )
            cyberpunk_console.print()
            cyberpunk_console.print(
                "[bold bright_blue]" + "◄" * 97 + "[/bold bright_blue]"
            )
            cyberpunk_console.print()
        except:
            pass

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
