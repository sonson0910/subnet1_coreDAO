#!/usr/bin/env python3
"""
Flexible Validator Runner for Subnet1 - Core Blockchain
Integrates flexible consensus with existing Subnet1 validator logic

This script provides:
- Flexible start times (can join mid-slot)
- Event-driven consensus coordination
- Backward compatibility with existing Subnet1 code
- Dynamic phase detection and adaptation
"""

import os
import sys
import logging
import asyncio
import argparse
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
    from mt_core.core.datatypes import ValidatorInfo
    from mt_core.consensus.flexible_validator_node import (
        FlexibleValidatorNode,
        FlexibleSlotConfig,
    )
    from mt_core.consensus.validator_node_core import ValidatorNodeCore
    from web3 import Web3
except ImportError as e:
    print(f"❌ FATAL: Import Error: {e}")
    sys.exit(1)

# --- Load environment variables (.env) ---
env_path = project_root / ".env"

# --- Configure Logging with RichHandler ---
rich_handler = RichHandler(
    show_time=True,
    show_level=True,
    show_path=False,
    markup=True,
    rich_tracebacks=True,
    log_time_format="[%Y-%m-%d %H:%M:%S]",
)

logging.basicConfig(
    level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[rich_handler]
)

logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments for flexible validator."""
    parser = argparse.ArgumentParser(
        description="Flexible Subnet1 Validator - Start anytime with adaptive consensus",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Flexibility Modes:
  ultra_flexible : Maximum flexibility, can join anytime, long buffers
  balanced       : Balanced flexibility and performance (default)
  performance    : Performance focused with flexible start
  rigid          : Traditional fixed timing (backward compatibility)

Examples:
  python run_flexible_validator_subnet1.py --validator 1 --mode balanced
  python run_flexible_validator_subnet1.py --validator 2 --mode ultra_flexible
  python run_flexible_validator_subnet1.py --validator 1 --mode rigid
        """,
    )

    parser.add_argument(
        "--validator",
        "-v",
        type=int,
        choices=[1, 2],
        default=1,
        help="Validator ID to run (1 or 2). Default: 1",
    )

    parser.add_argument(
        "--mode",
        choices=["ultra_flexible", "balanced", "performance", "rigid"],
        default="balanced",
        help="Consensus mode (default: balanced)",
    )

    parser.add_argument(
        "--auto-adapt",
        action="store_true",
        default=True,
        help="Auto-adapt timing based on network (default: True)",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level. Default: INFO",
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Show demo of flexibility features",
    )

    return parser.parse_args()


def setup_flexible_config(mode: str) -> Optional[FlexibleSlotConfig]:
    """Setup flexible slot configuration based on mode."""

    if mode == "rigid":
        # Traditional mode - no flexible features
        return None

    elif mode == "ultra_flexible":
        # Maximum flexibility for research/testing
        return FlexibleSlotConfig(
            slot_duration_minutes=6.0,  # Longer slots for maximum flexibility
            min_task_assignment_seconds=20,
            min_task_execution_seconds=45,
            min_consensus_seconds=30,
            min_metagraph_update_seconds=15,
            task_deadline_buffer=60,
            consensus_deadline_buffer=90,
            metagraph_deadline_buffer=30,
            allow_mid_slot_join=True,
            auto_extend_on_consensus=True,
            max_auto_extension_seconds=180,
        )

    elif mode == "performance":
        # Performance focused but still flexible
        return FlexibleSlotConfig(
            slot_duration_minutes=3.0,  # Shorter slots for faster cycles
            min_task_assignment_seconds=25,
            min_task_execution_seconds=50,
            min_consensus_seconds=35,
            min_metagraph_update_seconds=10,
            task_deadline_buffer=15,
            consensus_deadline_buffer=25,
            metagraph_deadline_buffer=10,
            allow_mid_slot_join=True,
            auto_extend_on_consensus=False,  # No auto-extension for performance
            max_auto_extension_seconds=30,
        )

    else:  # balanced (default)
        # Balanced flexibility and performance for production
        return FlexibleSlotConfig(
            slot_duration_minutes=4.0,
            min_task_assignment_seconds=30,
            min_task_execution_seconds=60,
            min_consensus_seconds=45,
            min_metagraph_update_seconds=15,
            task_deadline_buffer=30,
            consensus_deadline_buffer=45,
            metagraph_deadline_buffer=15,
            allow_mid_slot_join=True,
            auto_extend_on_consensus=True,
            max_auto_extension_seconds=90,
        )


class FlexibleSubnet1Validator:
    """
    Flexible wrapper for Subnet1Validator that integrates flexible consensus.
    
    This class bridges existing Subnet1Validator functionality with the new
    flexible consensus system, maintaining backward compatibility while
    adding flexible timing features.
    """

    def __init__(
        self,
        validator_info: ValidatorInfo,
        core_client: Web3,
        account: Account,
        contract_address: str,
        api_port: int = 8001,
        host: str = "0.0.0.0",
        mode: str = "balanced",
        auto_adapt: bool = True,
    ):
        """
        Initialize flexible Subnet1 validator.

        Args:
            validator_info: Validator information
            core_client: Web3 client for Core blockchain
            account: Validator account
            contract_address: Smart contract address
            api_port: API port for validator
            host: Host address
            mode: Consensus mode (flexible/rigid)
            auto_adapt: Whether to auto-adapt timing
        """
        self.validator_info = validator_info
        self.core_client = core_client
        self.account = account
        self.contract_address = contract_address
        self.api_port = api_port
        self.host = host
        self.mode = mode
        self.auto_adapt = auto_adapt

        # Setup configuration
        self.flexible_config = setup_flexible_config(mode)

        # Initialize components
        self.subnet1_validator = None
        self.flexible_validator = None
        self.validator_core = None

        logger.info(f"🔄 FlexibleSubnet1Validator initialized")
        logger.info(f"📊 Mode: {mode}, Auto-adapt: {auto_adapt}")
        logger.info(f"🆔 Validator: {validator_info.uid}")
        logger.info(f"📍 Address: {validator_info.address}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self):
        """Start the flexible validator."""
        logger.info(f"🚀 Starting FlexibleSubnet1Validator in {self.mode} mode")

        try:
            if self.mode == "rigid":
                # Use traditional Subnet1Validator
                await self._start_rigid_mode()
            else:
                # Use flexible consensus
                await self._start_flexible_mode()

            logger.info("✅ FlexibleSubnet1Validator started successfully")

        except Exception as e:
            logger.error(f"❌ Error starting FlexibleSubnet1Validator: {e}")
            raise

    async def stop(self):
        """Stop the validator."""
        logger.info("🛑 Stopping FlexibleSubnet1Validator")

        try:
            if self.subnet1_validator:
                await self.subnet1_validator.__aexit__(None, None, None)

        except Exception as e:
            logger.error(f"❌ Error stopping validator: {e}")

    async def _start_rigid_mode(self):
        """Start validator in traditional rigid mode."""
        logger.info("⏰ Starting in RIGID mode (traditional timing)")

        # Create traditional Subnet1Validator
        self.subnet1_validator = Subnet1Validator(
            validator_info=self.validator_info,
            core_client=self.core_client,
            account=self.account,
            contract_address=self.contract_address,
            api_port=self.api_port,
            host=self.host,
        )

        # Start using traditional method
        await self.subnet1_validator.__aenter__()

    async def _start_flexible_mode(self):
        """Start validator in flexible consensus mode."""
        logger.info(f"🔄 Starting in FLEXIBLE mode ({self.mode})")

        # Create Subnet1Validator
        self.subnet1_validator = Subnet1Validator(
            validator_info=self.validator_info,
            core_client=self.core_client,
            account=self.account,
            contract_address=self.contract_address,
            api_port=self.api_port,
            host=self.host,
        )

        # Start the base validator
        await self.subnet1_validator.__aenter__()

        # Get the underlying ValidatorNodeCore
        if hasattr(self.subnet1_validator, "validator_node"):
            self.validator_core = self.subnet1_validator.validator_node
        else:
            # Create ValidatorNodeCore if not available
            self.validator_core = ValidatorNodeCore(
                validator_info=self.validator_info,
                core_client=self.core_client,
                account=self.account,
                contract_address=self.contract_address,
                api_port=self.api_port,
                consensus_mode="flexible",
            )

        # Create FlexibleValidatorNode wrapper
        self.flexible_validator = FlexibleValidatorNode(
            validator_core=self.validator_core,
            flexible_config=self.flexible_config,
            auto_adapt_timing=self.auto_adapt,
        )

        # Start flexible consensus
        logger.info("🔄 Starting flexible consensus process...")
        await self.flexible_validator.start_flexible_consensus()

    async def run_forever(self):
        """Run the validator forever until interrupted."""
        try:
            if self.mode == "rigid":
                # In rigid mode, just wait
                while True:
                    await asyncio.sleep(1)
            else:
                # In flexible mode, the consensus loop is already running
                # Just wait for interruption
                while True:
                    await asyncio.sleep(10)
                    # Optional: Log periodic status
                    if self.flexible_validator:
                        metrics = self.flexible_validator.get_performance_metrics()
                        logger.debug(f"📊 Validator metrics: {metrics}")

        except KeyboardInterrupt:
            logger.info("👋 Validator interrupted by user")
        except Exception as e:
            logger.error(f"❌ Error in validator main loop: {e}")
            raise


async def run_flexible_validator_process(args):
    """Main process to run the flexible validator."""
    logger.info("🛡️ --- Starting Flexible Subnet1 Validator --- 🛡️")

    # --- Load environment variables ---
    if env_path.exists():
        logger.info(f"📄 Loading environment variables from: {env_path}")
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        logger.warning(f"📄 Environment file (.env) not found at {env_path}")

    # === Get validator configuration ===
    validator_id = args.validator

    # Use specific validator configuration based on validator_id
    if validator_id == 2:
        validator_readable_id = os.getenv("VALIDATOR_2_ID")
        validator_private_key = os.getenv("VALIDATOR_2_PRIVATE_KEY")
        validator_address = os.getenv("VALIDATOR_2_ADDRESS")
        validator_api_endpoint = os.getenv("VALIDATOR_2_API_ENDPOINT")
        validator_host = os.getenv("VALIDATOR_2_HOST", "0.0.0.0")
        validator_port = int(os.getenv("VALIDATOR_2_PORT", "8002"))
    else:  # Default to validator 1
        validator_readable_id = (
            os.getenv("VALIDATOR_1_ID") or os.getenv("SUBNET1_VALIDATOR_ID")
        )
        validator_private_key = (
            os.getenv("VALIDATOR_1_PRIVATE_KEY") or os.getenv("CORE_PRIVATE_KEY")
        )
        validator_address = os.getenv("VALIDATOR_1_ADDRESS")
        validator_api_endpoint = (
            os.getenv("VALIDATOR_1_API_ENDPOINT")
            or os.getenv("VALIDATOR_API_ENDPOINT")
        )
        validator_host = (
            os.getenv("VALIDATOR_1_HOST")
            or os.getenv("SUBNET1_VALIDATOR_HOST", "0.0.0.0")
        )
        validator_port = int(
            os.getenv("VALIDATOR_1_PORT")
            or os.getenv("SUBNET1_VALIDATOR_PORT", "8001")
        )

    # Validate required configurations
    required_configs = {
        f"VALIDATOR_{validator_id}_ID": validator_readable_id,
        f"VALIDATOR_{validator_id}_PRIVATE_KEY": validator_private_key,
        "CORE_NODE_URL": os.getenv("CORE_NODE_URL"),
        "CORE_CONTRACT_ADDRESS": os.getenv("CORE_CONTRACT_ADDRESS"),
    }

    missing_configs = [k for k, v in required_configs.items() if not v]
    if missing_configs:
        logger.critical(
            f"❌ FATAL: Missing configurations in .env: {missing_configs}"
        )
        return

    # === Display configuration ===
    logger.info(f"🏗️ --- Flexible Validator {validator_id} Configuration --- 🏗️")
    logger.info(f"🆔 Validator ID          : [cyan]'{validator_readable_id}'[/]")
    logger.info(f"🔑 Validator Address     : [yellow]{validator_address}[/]")
    logger.info(f"🏗️ Core Node URL         : [cyan]{os.getenv('CORE_NODE_URL')}[/]")
    logger.info(f"📝 Contract Address      : [cyan]{os.getenv('CORE_CONTRACT_ADDRESS')}[/]")
    logger.info(f"👂 API Endpoint          : [link={validator_api_endpoint}]{validator_api_endpoint}[/link]")
    logger.info(f"👂 Listening on          : [bold blue]{validator_host}:{validator_port}[/]")
    logger.info(f"🔄 Consensus Mode        : [bold green]{args.mode}[/]")
    logger.info(f"⚡ Auto-adapt           : [bold blue]{args.auto_adapt}[/]")
    logger.info("=" * 70)

    # === Load validator account ===
    try:
        logger.info(f"🔑 Loading validator {validator_id} account...")
        validator_account = Account.from_key(validator_private_key)
        logger.info(f"✅ Account loaded: {validator_account.address}")

        # Calculate UID
        expected_uid_bytes = validator_readable_id.encode("utf-8")
        expected_uid_hex = expected_uid_bytes.hex()

        # Create ValidatorInfo
        validator_info = ValidatorInfo(
            uid=expected_uid_hex,
            address=validator_account.address,
            stake=0,  # Will be populated from chain
            api_endpoint=validator_api_endpoint,
        )

        # Create Web3 client
        web3_client = Web3(Web3.HTTPProvider(os.getenv("CORE_NODE_URL")))
        logger.info(f"🌐 Web3 connected: {web3_client.is_connected()}")

    except Exception as e:
        logger.critical(f"❌ FATAL: Failed to setup validator account: {e}")
        return

    # === Initialize and run flexible validator ===
    try:
        flexible_validator = FlexibleSubnet1Validator(
            validator_info=validator_info,
            core_client=web3_client,
            account=validator_account,
            contract_address=os.getenv("CORE_CONTRACT_ADDRESS"),
            api_port=validator_port,
            host=validator_host,
            mode=args.mode,
            auto_adapt=args.auto_adapt,
        )

        # Run validator using async context manager
        async with flexible_validator:
            logger.info(f"✅ Flexible Validator {validator_id} started in {args.mode} mode")
            logger.info("🔄 Validator is now running and can join consensus at any time...")

            # Show mode-specific features
            if args.mode != "rigid":
                config = setup_flexible_config(args.mode)
                logger.info(f"⏰ Slot duration: {config.slot_duration_minutes} minutes")
                logger.info(f"🔄 Mid-slot join: {config.allow_mid_slot_join}")
                logger.info(f"⚡ Auto-extend: {config.auto_extend_on_consensus}")

            # Run forever
            await flexible_validator.run_forever()

    except Exception as e:
        logger.exception(f"💥 Error running flexible validator: {e}")
    finally:
        logger.info(f"🛑 Flexible Validator {validator_id} cleanup finished")


async def demo_flexibility():
    """Demonstrate flexibility features."""
    logger.info("🎭 FLEXIBLE CONSENSUS DEMONSTRATION")
    logger.info("=" * 60)

    modes = ["ultra_flexible", "balanced", "performance", "rigid"]

    for mode in modes:
        logger.info(f"\n📊 {mode.upper()} MODE:")

        if mode == "rigid":
            logger.info("   ⏰ Traditional fixed timing")
            logger.info("   🚫 No mid-slot joining")
            logger.info("   📐 Strict phase boundaries")
        else:
            config = setup_flexible_config(mode)
            logger.info(f"   ⏰ Slot duration: {config.slot_duration_minutes} min")
            logger.info(f"   🔄 Mid-slot join: {config.allow_mid_slot_join}")
            logger.info(f"   ⚡ Auto-extend: {config.auto_extend_on_consensus}")
            logger.info(f"   🛡️ Consensus buffer: {config.consensus_deadline_buffer}s")

        # Show when validators can start
        logger.info("   🕐 Can start at:")
        if mode == "rigid":
            logger.info("      - Only at slot boundaries")
        else:
            logger.info("      - Any time during consensus")
            logger.info("      - Mid-slot joining supported")
            logger.info("      - Automatic phase detection")

    logger.info("\n💡 KEY BENEFITS:")
    logger.info("   ✅ Validators can start anytime")
    logger.info("   ✅ Automatic network synchronization")
    logger.info("   ✅ Graceful handling of offline validators")
    logger.info("   ✅ Backward compatibility with rigid mode")


def main():
    """Main entry point."""
    args = parse_arguments()

    # Update log level
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    rich_handler.setLevel(log_level)
    logger.setLevel(log_level)

    if args.demo:
        asyncio.run(demo_flexibility())
    else:
        try:
            asyncio.run(run_flexible_validator_process(args))
        except KeyboardInterrupt:
            logger.info("👋 Flexible validator interrupted by user (Ctrl+C)")
        except Exception as e:
            logger.exception(f"💥 Critical error in main execution: {e}")
        finally:
            logger.info("🏁 Flexible validator script finished")


if __name__ == "__main__":
    main()