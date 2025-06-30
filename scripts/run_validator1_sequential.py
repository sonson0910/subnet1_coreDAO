#!/usr/bin/env python3
"""
Run Validator 1 with Sequential Consensus Mode
This enables true consensus between validators with batch coordination
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "moderntensor"))

from rich.console import Console
from rich.logging import RichHandler

# Setup rich logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)

async def run_validator1_sequential():
    """Run Validator 1 with sequential consensus mode"""
    
    # Load environment
    from dotenv import load_dotenv
    config_path = project_root / "config.env"
    load_dotenv(config_path)
    
    logger.info("🚀 Starting Validator 1 with Sequential Consensus Mode")
    logger.info(f"📁 Config loaded from: {config_path}")
    
    # Import after loading env
    from moderntensor.mt_aptos.consensus.node import create_and_run_validator_sequential
    
    # Configuration
    validator_name = "validator1"
    batch_wait_time = 30.0  # Wait 30 seconds for each batch
    auto_password = "default123"
    
    logger.info(f"🔧 Configuration:")
    logger.info(f"   Validator Name: {validator_name}")
    logger.info(f"   Batch Wait Time: {batch_wait_time}s")
    logger.info(f"   Mode: Sequential Consensus")
    
    try:
        await create_and_run_validator_sequential(
            validator_name=validator_name,
            batch_wait_time=batch_wait_time,
            auto_password=auto_password
        )
    except KeyboardInterrupt:
        logger.info("👋 Validator 1 stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Validator 1 error: {e}")
        raise
    finally:
        logger.info("🏁 Validator 1 sequential script finished")

if __name__ == "__main__":
    asyncio.run(run_validator1_sequential()) 