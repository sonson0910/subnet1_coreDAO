#!/usr/bin/env python3
"""
Flexible Miner Runner for Subnet1 - Core Blockchain
Provides flexible timing support for miners in subnet1

This script provides:
- Flexible task execution timing
- Adaptive result submission
- Dynamic validator detection
- Graceful handling of network changes
"""

import os
import sys
import logging
import asyncio
import argparse
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

# --- Import required classes ---
try:
    from subnet1.miner import Subnet1Miner
    from mt_core.config.settings import settings as sdk_settings
    from mt_core.account import Account
    from mt_core.core.datatypes import MinerInfo
    from mt_core.consensus.flexible_slot_coordinator import (
        FlexibleSlotCoordinator,
        FlexibleSlotPhase,
        FlexibleSlotConfig,
    )
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
    """Parse command line arguments for flexible miner."""
    parser = argparse.ArgumentParser(
        description="Flexible Subnet1 Miner - Adaptive task execution with flexible timing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Flexibility Modes:
  adaptive       : Automatically adapt to validator timing (default)
  responsive     : Fast response mode with quick task execution
  patient        : Patient mode with longer task execution windows
  traditional    : Traditional fixed timing (backward compatibility)

Examples:
  python run_flexible_miner_subnet1.py --miner 1 --mode adaptive
  python run_flexible_miner_subnet1.py --miner 2 --mode responsive
  python run_flexible_miner_subnet1.py --miner 1 --mode patient
        """,
    )

    parser.add_argument(
        "--miner",
        "-m",
        type=int,
        choices=[1, 2, 3, 4, 5],
        default=1,
        help="Miner ID to run (1-5). Default: 1",
    )

    parser.add_argument(
        "--mode",
        choices=["adaptive", "responsive", "patient", "traditional"],
        default="adaptive",
        help="Miner mode (default: adaptive)",
    )

    parser.add_argument(
        "--auto-detect-validators",
        action="store_true",
        default=True,
        help="Auto-detect active validators (default: True)",
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
        help="Show demo of miner flexibility features",
    )

    return parser.parse_args()


class FlexibleMinerConfig:
    """Configuration for flexible miner behavior."""

    def __init__(
        self,
        mode: str = "adaptive",
        response_timeout_multiplier: float = 1.0,
        task_execution_buffer: int = 30,
        validator_detection_interval: int = 10,
        auto_adjust_timing: bool = True,
    ):
        self.mode = mode
        self.response_timeout_multiplier = response_timeout_multiplier
        self.task_execution_buffer = task_execution_buffer
        self.validator_detection_interval = validator_detection_interval
        self.auto_adjust_timing = auto_adjust_timing


def setup_miner_config(mode: str) -> FlexibleMinerConfig:
    """Setup miner configuration based on mode."""

    if mode == "responsive":
        # Fast response mode
        return FlexibleMinerConfig(
            mode=mode,
            response_timeout_multiplier=0.8,  # 20% faster response
            task_execution_buffer=15,  # Shorter buffer
            validator_detection_interval=5,  # Check validators more frequently
            auto_adjust_timing=True,
        )

    elif mode == "patient":
        # Patient mode with longer execution windows
        return FlexibleMinerConfig(
            mode=mode,
            response_timeout_multiplier=1.5,  # 50% longer response window
            task_execution_buffer=60,  # Longer buffer
            validator_detection_interval=15,  # Check validators less frequently
            auto_adjust_timing=True,
        )

    elif mode == "traditional":
        # Traditional fixed timing
        return FlexibleMinerConfig(
            mode=mode,
            response_timeout_multiplier=1.0,
            task_execution_buffer=30,
            validator_detection_interval=30,
            auto_adjust_timing=False,
        )

    else:  # adaptive (default)
        # Adaptive mode that adjusts based on network conditions
        return FlexibleMinerConfig(
            mode=mode,
            response_timeout_multiplier=1.2,  # Slightly more time
            task_execution_buffer=30,
            validator_detection_interval=10,
            auto_adjust_timing=True,
        )


class FlexibleSubnet1Miner:
    """
    Flexible wrapper for Subnet1Miner that adapts to validator timing.
    
    This class provides:
    - Automatic validator detection
    - Adaptive task execution timing
    - Flexible result submission
    - Network condition awareness
    """

    def __init__(
        self,
        miner_info: MinerInfo,
        core_client: Web3,
        account: Account,
        contract_address: str,
        api_port: int = 9001,
        host: str = "0.0.0.0",
        mode: str = "adaptive",
        auto_detect_validators: bool = True,
    ):
        """
        Initialize flexible Subnet1 miner.

        Args:
            miner_info: Miner information
            core_client: Web3 client for Core blockchain
            account: Miner account
            contract_address: Smart contract address
            api_port: API port for miner
            host: Host address
            mode: Miner mode (adaptive/responsive/patient/traditional)
            auto_detect_validators: Whether to auto-detect validators
        """
        self.miner_info = miner_info
        self.core_client = core_client
        self.account = account
        self.contract_address = contract_address
        self.api_port = api_port
        self.host = host
        self.mode = mode
        self.auto_detect_validators = auto_detect_validators

        # Setup configuration
        self.config = setup_miner_config(mode)

        # Initialize components
        self.subnet1_miner = None
        self.slot_coordinator = None
        self.validator_endpoints = []
        self.last_validator_check = 0

        # Performance tracking
        self.tasks_received = 0
        self.tasks_completed = 0
        self.avg_response_time = 0.0
        self.network_conditions = "unknown"  # unknown, good, poor, unstable

        logger.info(f"🔄 FlexibleSubnet1Miner initialized")
        logger.info(f"📊 Mode: {mode}, Auto-detect: {auto_detect_validators}")
        logger.info(f"🆔 Miner: {miner_info.uid}")
        logger.info(f"📍 Address: {miner_info.address}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self):
        """Start the flexible miner."""
        logger.info(f"🚀 Starting FlexibleSubnet1Miner in {self.mode} mode")

        try:
            # Create Subnet1Miner
            self.subnet1_miner = Subnet1Miner(
                miner_info=self.miner_info,
                core_client=self.core_client,
                account=self.account,
                contract_address=self.contract_address,
                api_port=self.api_port,
                host=self.host,
            )

            # Start the base miner
            await self.subnet1_miner.__aenter__()

            # Initialize slot coordinator for timing awareness
            if self.mode != "traditional":
                self.slot_coordinator = FlexibleSlotCoordinator(
                    validator_uid=f"miner_{self.miner_info.uid}",
                    coordination_dir="slot_coordination",
                )

            # Start background tasks
            if self.auto_detect_validators:
                asyncio.create_task(self._validator_detection_loop())

            if self.config.auto_adjust_timing:
                asyncio.create_task(self._timing_adjustment_loop())

            logger.info("✅ FlexibleSubnet1Miner started successfully")

        except Exception as e:
            logger.error(f"❌ Error starting FlexibleSubnet1Miner: {e}")
            raise

    async def stop(self):
        """Stop the miner."""
        logger.info("🛑 Stopping FlexibleSubnet1Miner")

        try:
            if self.subnet1_miner:
                await self.subnet1_miner.__aexit__(None, None, None)

        except Exception as e:
            logger.error(f"❌ Error stopping miner: {e}")

    async def _validator_detection_loop(self):
        """Background loop to detect active validators."""
        logger.info("🔍 Starting validator detection loop")

        while True:
            try:
                current_time = time.time()

                # Check if it's time to update validator list
                if (
                    current_time - self.last_validator_check
                    > self.config.validator_detection_interval
                ):
                    await self._detect_active_validators()
                    self.last_validator_check = current_time

                await asyncio.sleep(self.config.validator_detection_interval)

            except Exception as e:
                logger.error(f"❌ Error in validator detection loop: {e}")
                await asyncio.sleep(30)  # Error recovery delay

    async def _detect_active_validators(self):
        """Detect currently active validators."""
        try:
            logger.debug("🔍 Detecting active validators...")

            # Method 1: Check coordination files
            active_validators = []
            if self.slot_coordinator:
                # Get current slot and check for active coordination files
                current_slot, current_phase, _ = (
                    self.slot_coordinator.get_current_slot_and_phase()
                )
                active_validators = self.slot_coordinator._get_active_validators_in_slot(
                    current_slot
                )

            # Method 2: Check blockchain for registered validators
            # (This would be implemented based on your contract interface)

            # Method 3: Network discovery
            await self._discover_validators_via_network()

            # Update validator endpoints
            self.validator_endpoints = active_validators

            logger.debug(
                f"🔍 Found {len(active_validators)} active validators: {active_validators}"
            )

            # Assess network conditions based on validator count
            self._assess_network_conditions(len(active_validators))

        except Exception as e:
            logger.error(f"❌ Error detecting validators: {e}")

    async def _discover_validators_via_network(self):
        """Discover validators via network pings."""
        # This would implement network-based validator discovery
        # For now, just a placeholder
        pass

    def _assess_network_conditions(self, validator_count: int):
        """Assess network conditions based on validator activity."""
        if validator_count >= 3:
            self.network_conditions = "good"
        elif validator_count >= 2:
            self.network_conditions = "fair"
        elif validator_count >= 1:
            self.network_conditions = "poor"
        else:
            self.network_conditions = "unstable"

        logger.debug(f"📊 Network conditions: {self.network_conditions}")

    async def _timing_adjustment_loop(self):
        """Background loop to adjust timing based on network conditions."""
        logger.info("⏰ Starting timing adjustment loop")

        while True:
            try:
                await self._adjust_timing_based_on_conditions()
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"❌ Error in timing adjustment loop: {e}")
                await asyncio.sleep(60)

    async def _adjust_timing_based_on_conditions(self):
        """Adjust timing parameters based on current network conditions."""
        if not self.config.auto_adjust_timing:
            return

        # Adjust response timeout multiplier based on network conditions
        if self.network_conditions == "good":
            self.config.response_timeout_multiplier = 1.0
        elif self.network_conditions == "fair":
            self.config.response_timeout_multiplier = 1.2
        elif self.network_conditions == "poor":
            self.config.response_timeout_multiplier = 1.5
        else:  # unstable
            self.config.response_timeout_multiplier = 2.0

        logger.debug(
            f"⏰ Adjusted timeout multiplier to {self.config.response_timeout_multiplier:.1f} "
            f"based on {self.network_conditions} conditions"
        )

    def get_adaptive_timeout(self, base_timeout: float) -> float:
        """Calculate adaptive timeout based on current conditions."""
        return base_timeout * self.config.response_timeout_multiplier

    def should_respond_to_task(self, task_deadline: float) -> bool:
        """Determine if miner should respond to a task given its deadline."""
        current_time = time.time()
        time_remaining = task_deadline - current_time

        # Consider execution buffer
        min_time_needed = 10  # Minimum time to execute task
        buffer_time = self.config.task_execution_buffer

        return time_remaining > (min_time_needed + buffer_time)

    async def run_forever(self):
        """Run the miner forever until interrupted."""
        try:
            logger.info(f"🔄 FlexibleSubnet1Miner running in {self.mode} mode")
            logger.info("📡 Listening for tasks from validators...")

            # Show current configuration
            logger.info(f"⏰ Response timeout multiplier: {self.config.response_timeout_multiplier}")
            logger.info(f"🛡️ Task execution buffer: {self.config.task_execution_buffer}s")
            logger.info(f"🔍 Validator check interval: {self.config.validator_detection_interval}s")

            while True:
                # Periodic status logging
                await asyncio.sleep(30)

                logger.debug(f"📊 Miner status:")
                logger.debug(f"   - Tasks received: {self.tasks_received}")
                logger.debug(f"   - Tasks completed: {self.tasks_completed}")
                logger.debug(f"   - Network conditions: {self.network_conditions}")
                logger.debug(f"   - Active validators: {len(self.validator_endpoints)}")

        except KeyboardInterrupt:
            logger.info("👋 Miner interrupted by user")
        except Exception as e:
            logger.error(f"❌ Error in miner main loop: {e}")
            raise

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get miner performance metrics."""
        completion_rate = (
            self.tasks_completed / max(self.tasks_received, 1) * 100
        )

        return {
            "miner_uid": self.miner_info.uid,
            "mode": self.mode,
            "tasks_received": self.tasks_received,
            "tasks_completed": self.tasks_completed,
            "completion_rate": completion_rate,
            "avg_response_time": self.avg_response_time,
            "network_conditions": self.network_conditions,
            "active_validators": len(self.validator_endpoints),
            "current_timeout_multiplier": self.config.response_timeout_multiplier,
        }


async def run_flexible_miner_process(args):
    """Main process to run the flexible miner."""
    logger.info("⛏️ --- Starting Flexible Subnet1 Miner --- ⛏️")

    # --- Load environment variables ---
    if env_path.exists():
        logger.info(f"📄 Loading environment variables from: {env_path}")
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        logger.warning(f"📄 Environment file (.env) not found at {env_path}")

    # === Get miner configuration ===
    miner_id = args.miner

    # Use specific miner configuration based on miner_id
    miner_readable_id = os.getenv(f"MINER_{miner_id}_ID") or f"subnet1_miner_{miner_id:03d}"
    miner_private_key = os.getenv(f"MINER_{miner_id}_PRIVATE_KEY") or os.getenv("MINER_PRIVATE_KEY")
    miner_address = os.getenv(f"MINER_{miner_id}_ADDRESS")
    miner_api_endpoint = os.getenv(f"MINER_{miner_id}_API_ENDPOINT") or f"http://localhost:{9000 + miner_id}"
    miner_host = os.getenv(f"MINER_{miner_id}_HOST", "0.0.0.0")
    miner_port = int(os.getenv(f"MINER_{miner_id}_PORT", str(9000 + miner_id)))

    # Validate required configurations
    required_configs = {
        f"MINER_{miner_id}_PRIVATE_KEY": miner_private_key,
        "CORE_NODE_URL": os.getenv("CORE_NODE_URL"),
        "CORE_CONTRACT_ADDRESS": os.getenv("CORE_CONTRACT_ADDRESS"),
    }

    missing_configs = [k for k, v in required_configs.items() if not v]
    if missing_configs:
        logger.critical(f"❌ FATAL: Missing configurations in .env: {missing_configs}")
        return

    # === Display configuration ===
    logger.info(f"🏗️ --- Flexible Miner {miner_id} Configuration --- 🏗️")
    logger.info(f"🆔 Miner ID              : [cyan]'{miner_readable_id}'[/]")
    logger.info(f"🔑 Miner Address         : [yellow]{miner_address}[/]")
    logger.info(f"🏗️ Core Node URL         : [cyan]{os.getenv('CORE_NODE_URL')}[/]")
    logger.info(f"📝 Contract Address      : [cyan]{os.getenv('CORE_CONTRACT_ADDRESS')}[/]")
    logger.info(f"👂 API Endpoint          : [link={miner_api_endpoint}]{miner_api_endpoint}[/link]")
    logger.info(f"👂 Listening on          : [bold blue]{miner_host}:{miner_port}[/]")
    logger.info(f"🔄 Miner Mode            : [bold green]{args.mode}[/]")
    logger.info(f"🔍 Auto-detect          : [bold blue]{args.auto_detect_validators}[/]")
    logger.info("=" * 70)

    # === Load miner account ===
    try:
        logger.info(f"🔑 Loading miner {miner_id} account...")
        miner_account = Account.from_key(miner_private_key)
        logger.info(f"✅ Account loaded: {miner_account.address}")

        # Calculate UID
        expected_uid_bytes = miner_readable_id.encode("utf-8")
        expected_uid_hex = expected_uid_bytes.hex()

        # Create MinerInfo
        miner_info = MinerInfo(
            uid=expected_uid_hex,
            address=miner_account.address,
            stake=0,  # Will be populated from chain
            api_endpoint=miner_api_endpoint,
        )

        # Create Web3 client
        web3_client = Web3(Web3.HTTPProvider(os.getenv("CORE_NODE_URL")))
        logger.info(f"🌐 Web3 connected: {web3_client.is_connected()}")

    except Exception as e:
        logger.critical(f"❌ FATAL: Failed to setup miner account: {e}")
        return

    # === Initialize and run flexible miner ===
    try:
        flexible_miner = FlexibleSubnet1Miner(
            miner_info=miner_info,
            core_client=web3_client,
            account=miner_account,
            contract_address=os.getenv("CORE_CONTRACT_ADDRESS"),
            api_port=miner_port,
            host=miner_host,
            mode=args.mode,
            auto_detect_validators=args.auto_detect_validators,
        )

        # Run miner using async context manager
        async with flexible_miner:
            logger.info(f"✅ Flexible Miner {miner_id} started in {args.mode} mode")
            logger.info("📡 Miner is now listening for tasks with adaptive timing...")

            # Show mode-specific features
            config = setup_miner_config(args.mode)
            logger.info(f"⏰ Response multiplier: {config.response_timeout_multiplier}")
            logger.info(f"🛡️ Execution buffer: {config.task_execution_buffer}s")
            logger.info(f"🔄 Auto-adjust: {config.auto_adjust_timing}")

            # Run forever
            await flexible_miner.run_forever()

    except Exception as e:
        logger.exception(f"💥 Error running flexible miner: {e}")
    finally:
        logger.info(f"🛑 Flexible Miner {miner_id} cleanup finished")


async def demo_miner_flexibility():
    """Demonstrate miner flexibility features."""
    logger.info("🎭 FLEXIBLE MINER DEMONSTRATION")
    logger.info("=" * 60)

    modes = ["adaptive", "responsive", "patient", "traditional"]

    for mode in modes:
        logger.info(f"\n📊 {mode.upper()} MODE:")

        config = setup_miner_config(mode)
        logger.info(f"   ⏰ Response multiplier: {config.response_timeout_multiplier}x")
        logger.info(f"   🛡️ Execution buffer: {config.task_execution_buffer}s")
        logger.info(f"   🔍 Detection interval: {config.validator_detection_interval}s")
        logger.info(f"   🔄 Auto-adjust: {config.auto_adjust_timing}")

        # Show characteristics
        if mode == "adaptive":
            logger.info("   📈 Adapts to network conditions automatically")
        elif mode == "responsive":
            logger.info("   ⚡ Fast response for high-performance scenarios")
        elif mode == "patient":
            logger.info("   🐌 Patient execution for stable long-term mining")
        elif mode == "traditional":
            logger.info("   📐 Fixed timing for backward compatibility")

    logger.info("\n💡 KEY BENEFITS:")
    logger.info("   ✅ Automatic validator detection")
    logger.info("   ✅ Adaptive timing based on network conditions")
    logger.info("   ✅ Flexible task execution windows")
    logger.info("   ✅ Performance optimization")


def main():
    """Main entry point."""
    args = parse_arguments()

    # Update log level
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    rich_handler.setLevel(log_level)
    logger.setLevel(log_level)

    if args.demo:
        asyncio.run(demo_miner_flexibility())
    else:
        try:
            asyncio.run(run_flexible_miner_process(args))
        except KeyboardInterrupt:
            logger.info("👋 Flexible miner interrupted by user (Ctrl+C)")
        except Exception as e:
            logger.exception(f"💥 Critical error in main execution: {e}")
        finally:
            logger.info("🏁 Flexible miner script finished")


if __name__ == "__main__":
    main()