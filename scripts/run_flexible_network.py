#!/usr/bin/env python3
"""
Flexible Network Runner for Subnet1
Comprehensive script to run validators and miners with flexible consensus

This script provides:
- Easy startup of entire network
- Flexible mode configuration
- Automatic entity management
- Network monitoring and status
"""

import os
import sys
import logging
import asyncio
import argparse
import time
import signal
from pathlib import Path
from typing import List, Dict, Optional
from rich.logging import RichHandler
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# --- Add project root to sys.path ---
project_root = Path(__file__).parent.parent  # Go to subnet1_aptos root
sys.path.insert(0, str(project_root))
# Add moderntensor_aptos path
moderntensor_path = project_root.parent / "moderntensor_aptos"
sys.path.insert(0, str(moderntensor_path))

# --- Import configuration management ---
try:
    from flexible_config import (
        get_config_manager,
        ConsensusMode,
        MinerMode,
        FlexibleConfigManager,
    )
except ImportError as e:
    print(f"❌ FATAL: Import Error: {e}")
    sys.exit(1)

# --- Configure logging and console ---
console = Console()
rich_handler = RichHandler(
    console=console,
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


class FlexibleNetworkManager:
    """
    Manager for running a complete flexible network with validators and miners.
    """
    
    def __init__(self, config_manager: FlexibleConfigManager):
        self.config_manager = config_manager
        self.processes = {}  # entity_id -> process
        self.entity_configs = {}  # entity_id -> config info
        self.network_status = "stopped"
        self.start_time = None
        
    async def start_network(
        self, 
        num_validators: int = 2,
        num_miners: int = 3,
        consensus_mode: str = "balanced",
        miner_mode: str = "adaptive",
        staggered_start: bool = True,
        stagger_delay: int = 10
    ):
        """
        Start a complete network with validators and miners.
        
        Args:
            num_validators: Number of validators to start
            num_miners: Number of miners to start
            consensus_mode: Consensus mode for validators
            miner_mode: Mode for miners
            staggered_start: Whether to stagger entity startup
            stagger_delay: Delay between entity starts (seconds)
        """
        logger.info("🚀 Starting Flexible Network")
        logger.info(f"📊 Configuration:")
        logger.info(f"   - Validators: {num_validators} ({consensus_mode} mode)")
        logger.info(f"   - Miners: {num_miners} ({miner_mode} mode)")
        logger.info(f"   - Staggered start: {staggered_start} ({stagger_delay}s delay)")
        
        self.network_status = "starting"
        self.start_time = time.time()
        
        try:
            # Start validators first
            for validator_id in range(1, num_validators + 1):
                await self._start_validator(validator_id, consensus_mode)
                
                if staggered_start and validator_id < num_validators:
                    logger.info(f"⏳ Waiting {stagger_delay}s before starting next validator...")
                    await asyncio.sleep(stagger_delay)
            
            # Wait a bit before starting miners
            if staggered_start:
                logger.info(f"⏳ Waiting {stagger_delay}s before starting miners...")
                await asyncio.sleep(stagger_delay)
            
            # Start miners
            for miner_id in range(1, num_miners + 1):
                await self._start_miner(miner_id, miner_mode)
                
                if staggered_start and miner_id < num_miners:
                    logger.info(f"⏳ Waiting {stagger_delay // 2}s before starting next miner...")
                    await asyncio.sleep(stagger_delay // 2)
            
            self.network_status = "running"
            logger.info("✅ Flexible Network started successfully")
            
            # Show network status
            await self._show_network_status()
            
        except Exception as e:
            logger.error(f"❌ Error starting network: {e}")
            self.network_status = "error"
            raise
    
    async def _start_validator(self, validator_id: int, mode: str):
        """Start a single validator."""
        logger.info(f"🛡️ Starting Validator {validator_id} in {mode} mode...")
        
        try:
            # Generate startup command
            command = self.config_manager.generate_startup_command(
                "validator", validator_id, mode
            )
            
            # Create process
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=project_root
            )
            
            self.processes[f"validator_{validator_id}"] = process
            self.entity_configs[f"validator_{validator_id}"] = {
                "type": "validator",
                "id": validator_id,
                "mode": mode,
                "command": command,
                "start_time": time.time(),
                "port": 8000 + validator_id,
            }
            
            logger.info(f"✅ Validator {validator_id} started (PID: {process.pid})")
            
        except Exception as e:
            logger.error(f"❌ Error starting Validator {validator_id}: {e}")
            raise
    
    async def _start_miner(self, miner_id: int, mode: str):
        """Start a single miner."""
        logger.info(f"⛏️ Starting Miner {miner_id} in {mode} mode...")
        
        try:
            # Generate startup command
            command = self.config_manager.generate_startup_command(
                "miner", miner_id, miner_mode=mode
            )
            
            # Create process
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=project_root
            )
            
            self.processes[f"miner_{miner_id}"] = process
            self.entity_configs[f"miner_{miner_id}"] = {
                "type": "miner",
                "id": miner_id,
                "mode": mode,
                "command": command,
                "start_time": time.time(),
                "port": 9000 + miner_id,
            }
            
            logger.info(f"✅ Miner {miner_id} started (PID: {process.pid})")
            
        except Exception as e:
            logger.error(f"❌ Error starting Miner {miner_id}: {e}")
            raise
    
    async def _show_network_status(self):
        """Display current network status."""
        table = Table(title="🌐 Flexible Network Status")
        
        table.add_column("Entity", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Mode", style="yellow")
        table.add_column("PID", style="blue")
        table.add_column("Port", style="magenta")
        table.add_column("Uptime", style="white")
        
        current_time = time.time()
        
        for entity_id, config in self.entity_configs.items():
            process = self.processes.get(entity_id)
            pid = process.pid if process else "N/A"
            uptime = int(current_time - config["start_time"])
            
            table.add_row(
                f"{config['type'].title()} {config['id']}",
                config["type"],
                config["mode"],
                str(pid),
                str(config["port"]),
                f"{uptime}s"
            )
        
        console.print(table)
        
        # Show network summary
        validators = [k for k in self.entity_configs.keys() if k.startswith("validator")]
        miners = [k for k in self.entity_configs.keys() if k.startswith("miner")]
        
        summary = f"""
📊 Network Summary:
   • Validators: {len(validators)}
   • Miners: {len(miners)}
   • Total Entities: {len(self.entity_configs)}
   • Network Status: {self.network_status}
   • Total Uptime: {int(current_time - self.start_time) if self.start_time else 0}s
        """
        
        console.print(Panel(summary.strip(), title="Network Summary", style="green"))
    
    async def stop_network(self):
        """Stop all network entities."""
        logger.info("🛑 Stopping Flexible Network...")
        
        try:
            # Stop all processes
            for entity_id, process in self.processes.items():
                if process.returncode is None:  # Process is still running
                    logger.info(f"🛑 Stopping {entity_id}...")
                    process.terminate()
                    
                    try:
                        await asyncio.wait_for(process.wait(), timeout=10.0)
                        logger.info(f"✅ {entity_id} stopped gracefully")
                    except asyncio.TimeoutError:
                        logger.warning(f"⚠️ {entity_id} didn't stop gracefully, killing...")
                        process.kill()
                        await process.wait()
            
            self.network_status = "stopped"
            logger.info("✅ Flexible Network stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping network: {e}")
    
    async def monitor_network(self, check_interval: int = 30):
        """Monitor network health and status."""
        logger.info(f"👁️ Starting network monitoring (check every {check_interval}s)")
        
        while self.network_status == "running":
            try:
                # Check process health
                dead_processes = []
                
                for entity_id, process in self.processes.items():
                    if process.returncode is not None:
                        dead_processes.append(entity_id)
                
                if dead_processes:
                    logger.warning(f"⚠️ Dead processes detected: {dead_processes}")
                    # Optionally restart dead processes here
                
                # Show periodic status
                await self._show_network_status()
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in network monitoring: {e}")
                await asyncio.sleep(check_interval)
    
    def get_network_metrics(self) -> Dict:
        """Get network performance metrics."""
        current_time = time.time()
        
        metrics = {
            "network_status": self.network_status,
            "total_entities": len(self.entity_configs),
            "validators": len([k for k in self.entity_configs.keys() if k.startswith("validator")]),
            "miners": len([k for k in self.entity_configs.keys() if k.startswith("miner")]),
            "uptime": int(current_time - self.start_time) if self.start_time else 0,
            "entities": {}
        }
        
        for entity_id, config in self.entity_configs.items():
            process = self.processes.get(entity_id)
            
            metrics["entities"][entity_id] = {
                "type": config["type"],
                "mode": config["mode"],
                "pid": process.pid if process else None,
                "port": config["port"],
                "uptime": int(current_time - config["start_time"]),
                "status": "running" if process and process.returncode is None else "stopped"
            }
        
        return metrics


async def run_network_command(args):
    """Main function to run network management commands."""
    
    config_manager = get_config_manager()
    network_manager = FlexibleNetworkManager(config_manager)
    
    if args.command == "start":
        logger.info("🚀 Starting Flexible Network")
        
        try:
            await network_manager.start_network(
                num_validators=args.validators,
                num_miners=args.miners,
                consensus_mode=args.consensus_mode,
                miner_mode=args.miner_mode,
                staggered_start=args.staggered,
                stagger_delay=args.delay
            )
            
            # Set up signal handlers for graceful shutdown
            def signal_handler(signum, frame):
                logger.info("👋 Received shutdown signal")
                asyncio.create_task(network_manager.stop_network())
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Monitor network
            if args.monitor:
                await network_manager.monitor_network(args.monitor_interval)
            else:
                # Just wait forever
                while True:
                    await asyncio.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("👋 Network interrupted by user")
        finally:
            await network_manager.stop_network()
    
    elif args.command == "config":
        # Show configuration information
        console.print("\n🔧 FLEXIBLE CONSENSUS CONFIGURATION")
        console.print("=" * 60)
        
        # Show available modes
        modes = config_manager.list_available_modes()
        console.print(f"\n📊 Available Modes:")
        console.print(f"   Consensus: {', '.join(modes['consensus_modes'])}")
        console.print(f"   Miner: {', '.join(modes['miner_modes'])}")
        
        # Show scenario recommendations
        console.print(f"\n💡 Scenario Recommendations:")
        scenarios = ["development", "testing", "production", "research", "performance"]
        
        for scenario in scenarios:
            rec = config_manager.get_recommended_mode_for_scenario(scenario)
            console.print(f"   {scenario.title()}: {rec['consensus']} + {rec['miner']} ({rec['description']})")
    
    elif args.command == "demo":
        # Run configuration demo
        from flexible_config import demo_config_usage
        demo_config_usage()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Flexible Network Manager for Subnet1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  start   : Start the flexible network
  config  : Show configuration information
  demo    : Show configuration demo

Examples:
  # Start network with default settings
  python run_flexible_network.py start
  
  # Start network with custom configuration
  python run_flexible_network.py start --validators 3 --miners 5 --consensus-mode ultra_flexible
  
  # Start for development
  python run_flexible_network.py start --consensus-mode ultra_flexible --miner-mode adaptive --staggered
  
  # Show configuration info
  python run_flexible_network.py config
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start the flexible network")
    start_parser.add_argument(
        "--validators", "-v", 
        type=int, 
        default=2, 
        help="Number of validators (default: 2)"
    )
    start_parser.add_argument(
        "--miners", "-m", 
        type=int, 
        default=3, 
        help="Number of miners (default: 3)"
    )
    start_parser.add_argument(
        "--consensus-mode",
        choices=["rigid", "balanced", "ultra_flexible", "performance"],
        default="balanced",
        help="Consensus mode for validators (default: balanced)"
    )
    start_parser.add_argument(
        "--miner-mode",
        choices=["traditional", "adaptive", "responsive", "patient"],
        default="adaptive",
        help="Mode for miners (default: adaptive)"
    )
    start_parser.add_argument(
        "--staggered",
        action="store_true",
        default=True,
        help="Stagger entity startup (default: True)"
    )
    start_parser.add_argument(
        "--delay",
        type=int,
        default=10,
        help="Delay between entity starts in seconds (default: 10)"
    )
    start_parser.add_argument(
        "--monitor",
        action="store_true",
        default=True,
        help="Enable network monitoring (default: True)"
    )
    start_parser.add_argument(
        "--monitor-interval",
        type=int,
        default=30,
        help="Network monitoring interval in seconds (default: 30)"
    )
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Show configuration information")
    
    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Show configuration demo")
    
    # Global options
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Update log level
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    rich_handler.setLevel(log_level)
    logger.setLevel(log_level)
    
    # Set default command if none provided
    if not args.command:
        args.command = "start"
    
    try:
        asyncio.run(run_network_command(args))
    except KeyboardInterrupt:
        logger.info("👋 Network manager interrupted by user (Ctrl+C)")
    except Exception as e:
        logger.exception(f"💥 Critical error in network manager: {e}")
    finally:
        logger.info("🏁 Network manager finished")


if __name__ == "__main__":
    main()