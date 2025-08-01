#!/usr/bin/env python3
"""
Flexible Consensus SDK for Subnet1

This SDK provides easy-to-use wrapper functions for integrating flexible consensus
into existing Subnet1 validators and miners. It wraps the enhanced consensus
functionality while maintaining backward compatibility.
"""

import sys
import os
import logging
import asyncio
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# Add path to moderntensor core
sys.path.append(os.path.join(os.path.dirname(__file__), "../../moderntensor_aptos"))

logger = logging.getLogger(__name__)

@dataclass
class FlexibleConsensusConfig:
    """Configuration for flexible consensus in Subnet1"""
    
    # Flexibility settings
    allow_mid_slot_join: bool = True
    auto_extend_on_consensus: bool = True
    max_auto_extension_seconds: int = 60
    
    # Timing buffers
    task_deadline_buffer: int = 20
    consensus_deadline_buffer: int = 30
    metagraph_deadline_buffer: int = 10
    
    # Adaptive settings
    adaptive_timing_enabled: bool = True
    min_validators_for_consensus: int = 2
    flexible_epoch_start: bool = True
    
    # Auto-detection
    auto_detect_epoch: bool = True
    auto_adapt_timing: bool = True

class FlexibleConsensusSDK:
    """
    SDK wrapper for flexible consensus functionality.
    
    This class provides a simple interface for Subnet1 components to use
    flexible consensus without needing to understand the underlying complexity.
    """
    
    def __init__(self, config: Optional[FlexibleConsensusConfig] = None):
        """
        Initialize the flexible consensus SDK.
        
        Args:
            config: Optional configuration (uses defaults if None)
        """
        self.config = config or FlexibleConsensusConfig()
        self.consensus_wrapper = None
        self.validator_node = None
        self.is_flexible_mode = False
        
        logger.info("🔧 Flexible Consensus SDK initialized")
    
    def wrap_validator(self, validator_node) -> 'FlexibleValidatorWrapper':
        """
        Wrap an existing ValidatorNode with flexible consensus capabilities.
        
        Args:
            validator_node: Existing ValidatorNode instance
            
        Returns:
            FlexibleValidatorWrapper instance
        """
        logger.info(f"🔄 Wrapping validator {getattr(validator_node, 'uid', 'unknown')} with flexible consensus")
        
        self.validator_node = validator_node
        wrapper = FlexibleValidatorWrapper(validator_node, self.config)
        
        return wrapper
    
    def create_flexible_config(self, mode: str = "balanced") -> FlexibleConsensusConfig:
        """
        Create a flexible consensus configuration for different use cases.
        
        Args:
            mode: Configuration mode ('ultra_flexible', 'balanced', 'performance')
            
        Returns:
            FlexibleConsensusConfig instance
        """
        if mode == "ultra_flexible":
            return FlexibleConsensusConfig(
                allow_mid_slot_join=True,
                auto_extend_on_consensus=True,
                max_auto_extension_seconds=120,
                task_deadline_buffer=30,
                consensus_deadline_buffer=60,
                metagraph_deadline_buffer=20,
                adaptive_timing_enabled=True,
                min_validators_for_consensus=1,
                flexible_epoch_start=True,
                auto_detect_epoch=True,
                auto_adapt_timing=True
            )
        elif mode == "performance":
            return FlexibleConsensusConfig(
                allow_mid_slot_join=True,
                auto_extend_on_consensus=False,
                max_auto_extension_seconds=30,
                task_deadline_buffer=10,
                consensus_deadline_buffer=15,
                metagraph_deadline_buffer=5,
                adaptive_timing_enabled=False,
                min_validators_for_consensus=2,
                flexible_epoch_start=False,
                auto_detect_epoch=True,
                auto_adapt_timing=False
            )
        else:  # balanced
            return FlexibleConsensusConfig()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current SDK status"""
        status = {
            "sdk_initialized": True,
            "flexible_mode": self.is_flexible_mode,
            "config": {
                "allow_mid_slot_join": self.config.allow_mid_slot_join,
                "auto_extend_on_consensus": self.config.auto_extend_on_consensus,
                "adaptive_timing_enabled": self.config.adaptive_timing_enabled
            }
        }
        
        if self.consensus_wrapper:
            status.update(self.consensus_wrapper.get_status())
            
        return status

class FlexibleValidatorWrapper:
    """
    Wrapper that adds flexible consensus capabilities to existing ValidatorNode.
    
    This wrapper maintains backward compatibility while providing access to
    enhanced flexible consensus features.
    """
    
    def __init__(self, validator_node, config: FlexibleConsensusConfig):
        """
        Initialize the flexible validator wrapper.
        
        Args:
            validator_node: Existing ValidatorNode instance
            config: Flexible consensus configuration
        """
        self.validator_node = validator_node
        self.config = config
        self.flexible_enabled = False
        self.consensus_stats = {
            "flexible_cycles_run": 0,
            "mid_slot_joins": 0,
            "auto_extensions_used": 0,
            "last_consensus_time": None
        }
        
        logger.info(f"🎯 FlexibleValidatorWrapper initialized for {getattr(validator_node, 'uid', 'unknown')}")
    
    def enable_flexible_consensus(self) -> bool:
        """
        Enable flexible consensus mode for this validator.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if validator has consensus component
            if not hasattr(self.validator_node, 'consensus'):
                logger.error("❌ Validator node does not have consensus component")
                return False
            
            # Apply flexible configuration to slot coordinator
            if hasattr(self.validator_node, 'slot_coordinator'):
                slot_config = self.validator_node.slot_coordinator.slot_config
                
                # Update configuration with flexible settings
                slot_config.allow_mid_slot_join = self.config.allow_mid_slot_join
                slot_config.auto_extend_on_consensus = self.config.auto_extend_on_consensus
                slot_config.max_auto_extension_seconds = self.config.max_auto_extension_seconds
                slot_config.task_deadline_buffer = self.config.task_deadline_buffer
                slot_config.consensus_deadline_buffer = self.config.consensus_deadline_buffer
                slot_config.metagraph_deadline_buffer = self.config.metagraph_deadline_buffer
                slot_config.adaptive_timing_enabled = self.config.adaptive_timing_enabled
                slot_config.min_validators_for_consensus = self.config.min_validators_for_consensus
                slot_config.flexible_epoch_start = self.config.flexible_epoch_start
                
                # Enable flexible mode in slot coordinator
                self.validator_node.slot_coordinator.enable_flexible_mode(
                    auto_detect_epoch=self.config.auto_detect_epoch
                )
            
            # Enable flexible mode in consensus
            if hasattr(self.validator_node.consensus, 'enable_flexible_mode'):
                success = self.validator_node.consensus.enable_flexible_mode(
                    auto_detect_epoch=self.config.auto_detect_epoch,
                    adaptive_timing=self.config.auto_adapt_timing
                )
                
                if success:
                    self.flexible_enabled = True
                    logger.info(f"✅ Flexible consensus enabled for validator {getattr(self.validator_node, 'uid', 'unknown')}")
                    return True
                else:
                    logger.error("❌ Failed to enable flexible mode in consensus")
                    return False
            else:
                logger.error("❌ Consensus does not support flexible mode")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error enabling flexible consensus: {e}")
            return False
    
    async def run_flexible_consensus(self, slot: Optional[int] = None) -> bool:
        """
        Run a flexible consensus cycle.
        
        Args:
            slot: Optional slot number (auto-detected if None)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.flexible_enabled:
            logger.warning("⚠️ Flexible consensus not enabled - enabling now")
            if not self.enable_flexible_consensus():
                return False
        
        try:
            logger.info(f"🚀 Starting flexible consensus cycle for slot {slot or 'auto-detect'}")
            
            # Use flexible consensus cycle if available
            if hasattr(self.validator_node.consensus, 'run_flexible_consensus_cycle'):
                await self.validator_node.consensus.run_flexible_consensus_cycle(slot)
                
                # Update stats
                self.consensus_stats["flexible_cycles_run"] += 1
                self.consensus_stats["last_consensus_time"] = time.time()
                
                # Get metrics from consensus
                if hasattr(self.validator_node.consensus, 'flexible_metrics'):
                    metrics = self.validator_node.consensus.flexible_metrics
                    self.consensus_stats["mid_slot_joins"] = metrics.get("mid_slot_joins", 0)
                    self.consensus_stats["auto_extensions_used"] = metrics.get("auto_extensions_used", 0)
                
                logger.info("✅ Flexible consensus cycle completed successfully")
                return True
            else:
                logger.warning("⚠️ Flexible consensus not available - falling back to standard consensus")
                # Fallback to standard consensus if available
                if hasattr(self.validator_node.consensus, 'run_consensus_cycle'):
                    await self.validator_node.consensus.run_consensus_cycle()
                    return True
                else:
                    logger.error("❌ No consensus method available")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error in flexible consensus cycle: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current wrapper status"""
        base_status = {
            "flexible_enabled": self.flexible_enabled,
            "validator_uid": getattr(self.validator_node, 'uid', 'unknown'),
            "config": {
                "allow_mid_slot_join": self.config.allow_mid_slot_join,
                "auto_extend_on_consensus": self.config.auto_extend_on_consensus,
                "adaptive_timing_enabled": self.config.adaptive_timing_enabled
            },
            "stats": self.consensus_stats.copy()
        }
        
        # Add consensus status if available
        if (self.flexible_enabled and 
            hasattr(self.validator_node, 'consensus') and 
            hasattr(self.validator_node.consensus, 'get_flexible_status')):
            
            base_status.update(self.validator_node.consensus.get_flexible_status())
        
        return base_status
    
    def get_consensus_metrics(self) -> Dict[str, Any]:
        """Get detailed consensus metrics"""
        metrics = self.consensus_stats.copy()
        
        if (hasattr(self.validator_node, 'consensus') and 
            hasattr(self.validator_node.consensus, 'flexible_metrics')):
            
            metrics.update(self.validator_node.consensus.flexible_metrics)
            
        return metrics
    
    # Proxy methods to maintain compatibility
    def __getattr__(self, name):
        """Proxy attribute access to underlying validator node"""
        if hasattr(self.validator_node, name):
            return getattr(self.validator_node, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

# Convenience functions for easy integration

def create_flexible_validator(validator_node, mode: str = "balanced") -> FlexibleValidatorWrapper:
    """
    Create a flexible validator wrapper with predefined configuration.
    
    Args:
        validator_node: Existing ValidatorNode instance
        mode: Configuration mode ('ultra_flexible', 'balanced', 'performance')
        
    Returns:
        FlexibleValidatorWrapper instance
    """
    sdk = FlexibleConsensusSDK()
    config = sdk.create_flexible_config(mode)
    return FlexibleValidatorWrapper(validator_node, config)

def enable_flexible_consensus_for_validator(validator_node, mode: str = "balanced") -> FlexibleValidatorWrapper:
    """
    Enable flexible consensus for an existing validator node.
    
    Args:
        validator_node: Existing ValidatorNode instance
        mode: Configuration mode
        
    Returns:
        FlexibleValidatorWrapper instance with flexible consensus enabled
    """
    wrapper = create_flexible_validator(validator_node, mode)
    wrapper.enable_flexible_consensus()
    return wrapper

async def run_flexible_consensus_simple(validator_node, mode: str = "balanced", slot: Optional[int] = None) -> bool:
    """
    Simple function to run flexible consensus on a validator.
    
    Args:
        validator_node: Existing ValidatorNode instance
        mode: Configuration mode
        slot: Optional slot number
        
    Returns:
        True if successful, False otherwise
    """
    wrapper = enable_flexible_consensus_for_validator(validator_node, mode)
    return await wrapper.run_flexible_consensus(slot)

# Example usage and testing functions

def test_flexible_consensus_integration():
    """Test function to validate flexible consensus integration"""
    logger.info("🧪 Testing flexible consensus integration...")
    
    try:
        # Test SDK initialization
        sdk = FlexibleConsensusSDK()
        assert sdk is not None
        logger.info("✅ SDK initialization: PASS")
        
        # Test configuration creation
        config = sdk.create_flexible_config("balanced")
        assert config.allow_mid_slot_join == True
        logger.info("✅ Configuration creation: PASS")
        
        # Test different modes
        ultra_config = sdk.create_flexible_config("ultra_flexible")
        assert ultra_config.max_auto_extension_seconds == 120
        logger.info("✅ Ultra flexible config: PASS")
        
        perf_config = sdk.create_flexible_config("performance")
        assert perf_config.auto_extend_on_consensus == False
        logger.info("✅ Performance config: PASS")
        
        logger.info("🎉 All flexible consensus integration tests PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    # Run tests if script is executed directly
    logging.basicConfig(level=logging.INFO)
    test_flexible_consensus_integration()