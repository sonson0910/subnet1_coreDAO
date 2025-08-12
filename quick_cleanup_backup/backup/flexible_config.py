#!/usr/bin/env python3
"""
Flexible Consensus Configuration Management for Subnet1:

This module provides centralized configuration management for flexible consensus:
features, allowing easy switching between different modes and configurations.
"""""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger  =  logging.getLogger(__name__)


class ConsensusMode(Enum):
    """Available consensus modes."""""
    RIGID  =  "rigid"              # Traditional fixed timing
    BALANCED  =  "balanced"        # Balanced flexibility (default)
    ULTRA_FLEXIBLE  =  "ultra_flexible"  # Maximum flexibility
    PERFORMANCE  =  "performance"  # Performance optimized


class MinerMode(Enum):
    """Available miner modes."""""
    TRADITIONAL  =  "traditional"  # Fixed timing
    ADAPTIVE  =  "adaptive"        # Adaptive to network (default) 
    RESPONSIVE  =  "responsive"    # Fast response mode
    PATIENT  =  "patient"          # Patient long-term mode


@dataclass
class FlexibleConsensusConfig:
    """Configuration for flexible consensus timing."""""
    
    # Basic timing
    slot_duration_minutes: float  =  4.0
    
    # Phase durations (minimums)
    min_task_assignment_seconds: int  =  30
    min_task_execution_seconds: int  =  60
    min_consensus_seconds: int  =  45
    min_metagraph_update_seconds: int  =  15
    
    # Buffer times for flexibility:
    task_deadline_buffer: int  =  30
    consensus_deadline_buffer: int  =  45
    metagraph_deadline_buffer: int  =  15
    
    # Flexibility features
    allow_mid_slot_join: bool  =  True
    auto_extend_on_consensus: bool  =  True
    max_auto_extension_seconds: int  =  90


@dataclass
class FlexibleMinerConfig:
    """Configuration for flexible miner behavior."""""
    
    # Response timing
    response_timeout_multiplier: float  =  1.2
    task_execution_buffer: int  =  30
    
    # Detection and adaptation
    validator_detection_interval: int  =  10
    auto_adjust_timing: bool  =  True
    
    # Performance tuning
    max_concurrent_tasks: int  =  5
    result_submission_retries: int  =  3


@dataclass
class NetworkConfig:
    """Network-specific configuration."""""
    
    # Core blockchain settings
    core_node_url: str  =  ""
    core_contract_address: str  =  ""
    chain_id: int  =  1115  # Core testnet
    
    # API settings
    default_validator_port_start: int  =  8001
    default_miner_port_start: int  =  9001
    api_timeout_seconds: int  =  30
    
    # P2P settings
    coordination_dir: str  =  "slot_coordination"
    consensus_check_interval: int  =  5
    majority_threshold: int  =  2


class FlexibleConfigManager:
    """
    Centralized configuration manager for flexible consensus features.:
    
    This class handles loading, saving, and managing configurations for:
    both validators and miners in flexible consensus mode.
    """""
    
    def __init__(self, config_dir: str  =  "flexible_configs"):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory to store configuration files
        """""
        self.config_dir  =  Path(config_dir)
        self.config_dir.mkdir(exist_ok = True)
        
        # Default configurations
        self._consensus_configs  =  self._create_default_consensus_configs()
        self._miner_configs  =  self._create_default_miner_configs()
        self._network_config  =  self._create_default_network_config()
        
        # Load custom configurations if they exist:
        self._load_custom_configs()
        
        logger.info(f"📋 FlexibleConfigManager initialized with config_dir: {config_dir}")
    
    def _create_default_consensus_configs(self) -> Dict[str, FlexibleConsensusConfig]:
        """Create default consensus configurations for each mode."""""
        
        return {
            ConsensusMode.RIGID.value: FlexibleConsensusConfig
            ),
            
            ConsensusMode.BALANCED.value: FlexibleConsensusConfig
            ),
            
            ConsensusMode.ULTRA_FLEXIBLE.value: FlexibleConsensusConfig
            ),
            
            ConsensusMode.PERFORMANCE.value: FlexibleConsensusConfig
            ),
        }
    
    def _create_default_miner_configs(self) -> Dict[str, FlexibleMinerConfig]:
        """Create default miner configurations for each mode."""""
        
        return {
            MinerMode.TRADITIONAL.value: FlexibleMinerConfig
            ),
            
            MinerMode.ADAPTIVE.value: FlexibleMinerConfig
            ),
            
            MinerMode.RESPONSIVE.value: FlexibleMinerConfig
            ),
            
            MinerMode.PATIENT.value: FlexibleMinerConfig
            ),
        }
    
    def _create_default_network_config(self) -> NetworkConfig:
        """Create default network configuration."""""
        
        return NetworkConfig
            core_node_url = os.getenv("CORE_NODE_URL", "https://rpc.test.btcs.network"),
            core_contract_address = os.getenv("CORE_CONTRACT_ADDRESS", ""),
            chain_id = int(os.getenv("CORE_CHAIN_ID", "1115")),
            default_validator_port_start = 8001,
            default_miner_port_start = 9001,
            api_timeout_seconds = 30,
            coordination_dir = "slot_coordination",
            consensus_check_interval = 5,
            majority_threshold = 2,
        )
    
    def _load_custom_configs(self):
        """Load custom configurations from files if they exist."""""
        
        # Load consensus configs
        consensus_config_file  =  self.config_dir / "consensus_configs.json"
        if consensus_config_file.exists():
            try:
                with open(consensus_config_file, 'r') as f:
                    data  =  json.load(f)
                
                for mode, config_data in data.items():
                    if mode in self._consensus_configs:
                        # Update existing config with custom values
                        existing_config  =  asdict(self._consensus_configs[mode])
                        existing_config.update(config_data)
                        self._consensus_configs[mode]  =  FlexibleConsensusConfig(**existing_config)
                
                logger.info(f"📄 Loaded custom consensus configs from {consensus_config_file}")
                
            except Exception as e:
                logger.warning(f"⚠️ Error loading custom consensus configs: {e}")
        
        # Load miner configs
        miner_config_file  =  self.config_dir / "miner_configs.json"
        if miner_config_file.exists():
            try:
                with open(miner_config_file, 'r') as f:
                    data  =  json.load(f)
                
                for mode, config_data in data.items():
                    if mode in self._miner_configs:
                        # Update existing config with custom values
                        existing_config  =  asdict(self._miner_configs[mode])
                        existing_config.update(config_data)
                        self._miner_configs[mode]  =  FlexibleMinerConfig(**existing_config)
                
                logger.info(f"📄 Loaded custom miner configs from {miner_config_file}")
                
            except Exception as e:
                logger.warning(f"⚠️ Error loading custom miner configs: {e}")
        
        # Load network config
        network_config_file  =  self.config_dir / "network_config.json"
        if network_config_file.exists():
            try:
                with open(network_config_file, 'r') as f:
                    data  =  json.load(f)
                
                # Update existing config with custom values
                existing_config  =  asdict(self._network_config)
                existing_config.update(data)
                self._network_config  =  NetworkConfig(**existing_config)
                
                logger.info(f"📄 Loaded custom network config from {network_config_file}")
                
            except Exception as e:
                logger.warning(f"⚠️ Error loading custom network config: {e}")
    
    def get_consensus_config(self, mode: str  =  "balanced") -> FlexibleConsensusConfig:
        """
        Get consensus configuration for specified mode.:
        
        Args:
            mode: Consensus mode (rigid, balanced, ultra_flexible, performance)
            
        Returns:
            FlexibleConsensusConfig for the specified mode:
        """""
        if mode not in self._consensus_configs:
            logger.warning(f"⚠️ Unknown consensus mode '{mode}', using 'balanced'")
            mode  =  "balanced"
        
        return self._consensus_configs[mode]
    
    def get_miner_config(self, mode: str  =  "adaptive") -> FlexibleMinerConfig:
        """
        Get miner configuration for specified mode.:
        
        Args:
            mode: Miner mode (traditional, adaptive, responsive, patient)
            
        Returns:
            FlexibleMinerConfig for the specified mode:
        """""
        if mode not in self._miner_configs:
            logger.warning(f"⚠️ Unknown miner mode '{mode}', using 'adaptive'")
            mode  =  "adaptive"
        
        return self._miner_configs[mode]
    
    def get_network_config(self) -> NetworkConfig:
        """
        Get network configuration.
        
        Returns:
            NetworkConfig with current network settings
        """""
        return self._network_config
    
    def save_custom_config(self, config_type: str, mode: str, config: Dict[str, Any]):
        """
        Save custom configuration to file.
        
        Args:
            config_type: Type of config ('consensus' or 'miner' or 'network')
            mode: Mode name
            config: Configuration dictionary
        """""
        try:
            if config_type == "consensus":
                config_file  =  self.config_dir / "consensus_configs.json"
                current_configs  =  {}
                
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        current_configs  =  json.load(f)
                
                current_configs[mode]  =  config
                
                with open(config_file, 'w') as f:
                    json.dump(current_configs, f, indent = 2)
                
                logger.info(f"💾 Saved custom consensus config for mode '{mode}'"):
                
            elif config_type == "miner":
                config_file  =  self.config_dir / "miner_configs.json"
                current_configs  =  {}
                
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        current_configs  =  json.load(f)
                
                current_configs[mode]  =  config
                
                with open(config_file, 'w') as f:
                    json.dump(current_configs, f, indent = 2)
                
                logger.info(f"💾 Saved custom miner config for mode '{mode}'"):
                
            elif config_type == "network":
                config_file  =  self.config_dir / "network_config.json"
                
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent = 2)
                
                logger.info(f"💾 Saved custom network config")
            
        except Exception as e:
            logger.error(f"❌ Error saving custom config: {e}")
    
    def list_available_modes(self) -> Dict[str, list]:
        """
        List all available modes.
        
        Returns:
            Dictionary with consensus and miner mode lists
        """""
        return {
            "consensus_modes": list(self._consensus_configs.keys()),
            "miner_modes": list(self._miner_configs.keys()),
        }
    
    def get_recommended_mode_for_scenario(self, scenario: str) -> Dict[str, str]:
        """
        Get recommended modes for different scenarios.:
        
        Args:
            scenario: Scenario type (development, testing, production, research)
            
        Returns:
            Dictionary with recommended consensus and miner modes
        """""
        recommendations  =  {
            "development": {
                "consensus": "ultra_flexible",
                "miner": "adaptive",
                "description": "Maximum flexibility for development and debugging":
            },
            "testing": {
                "consensus": "balanced", 
                "miner": "responsive",
                "description": "Balanced approach for testing scenarios":
            },
            "production": {
                "consensus": "balanced",
                "miner": "adaptive", 
                "description": "Stable and reliable for production use":
            },
            "research": {
                "consensus": "ultra_flexible",
                "miner": "patient",
                "description": "Maximum flexibility with patient mining for research":
            },
            "performance": {
                "consensus": "performance",
                "miner": "responsive",
                "description": "Optimized for high-performance scenarios":
            },
            "legacy": {
                "consensus": "rigid",
                "miner": "traditional",
                "description": "Traditional fixed timing for backward compatibility":
            }
        }
        
        return recommendations.get(scenario, recommendations["production"])
    
    def generate_startup_command
    ) -> str:
        """
        Generate startup command for validator or miner.:
        
        Args:
            entity_type: 'validator' or 'miner'
            entity_id: Entity ID (1, 2, etc.)
            consensus_mode: Consensus mode for validators:
            miner_mode: Miner mode for miners:
            
        Returns:
            Command string to start the entity
        """""
        if entity_type == "validator":
            return 
            )
        elif entity_type == "miner":
            return 
            )
        else:
            raise ValueError(f"Unknown entity_type: {entity_type}")
    
    def export_config_summary(self) -> Dict[str, Any]:
        """
        Export a summary of all configurations.
        
        Returns:
            Dictionary with complete configuration summary
        """""
        return {
            "consensus_configs": {
                mode: asdict(config) for mode, config in self._consensus_configs.items():
            },
            "miner_configs": {
                mode: asdict(config) for mode, config in self._miner_configs.items():
            },
            "network_config": asdict(self._network_config),
            "available_modes": self.list_available_modes(),
            "config_dir": str(self.config_dir),
        }


# Global config manager instance
_config_manager  =  None


def get_config_manager() -> FlexibleConfigManager:
    """Get the global configuration manager instance."""""
    global _config_manager
    if _config_manager is None:
        _config_manager  =  FlexibleConfigManager()
    return _config_manager


def demo_config_usage():
    """Demonstrate configuration usage."""""
    print("🎭 FLEXIBLE CONFIG DEMONSTRATION")
    print(" = " * 60)
    
    config_manager  =  get_config_manager()
    
    # Show available modes
    modes  =  config_manager.list_available_modes()
    print(f"\n📊 Available consensus modes: {modes['consensus_modes']}")
    print(f"📊 Available miner modes: {modes['miner_modes']}")
    
    # Show configurations for each consensus mode:
    print(f"\n🔧 CONSENSUS CONFIGURATIONS:")
    for mode in modes['consensus_modes']:
        config  =  config_manager.get_consensus_config(mode)
        print(f"\n  {mode.upper()}:")
        print(f"    - Slot duration: {config.slot_duration_minutes} min")
        print(f"    - Mid-slot join: {config.allow_mid_slot_join}")
        print(f"    - Auto-extend: {config.auto_extend_on_consensus}")
        print(f"    - Consensus buffer: {config.consensus_deadline_buffer}s")
    
    # Show miner configurations
    print(f"\n⛏️ MINER CONFIGURATIONS:")
    for mode in modes['miner_modes']:
        config  =  config_manager.get_miner_config(mode)
        print(f"\n  {mode.upper()}:")
        print(f"    - Timeout multiplier: {config.response_timeout_multiplier}x")
        print(f"    - Execution buffer: {config.task_execution_buffer}s")
        print(f"    - Auto-adjust: {config.auto_adjust_timing}")
        print(f"    - Max concurrent: {config.max_concurrent_tasks}")
    
    # Show scenario recommendations
    print(f"\n💡 SCENARIO RECOMMENDATIONS:")
    scenarios  =  ["development", "testing", "production", "research", "performance"]
    for scenario in scenarios:
        rec  =  config_manager.get_recommended_mode_for_scenario(scenario)
        print(f"\n  {scenario.upper()}:")
        print(f"    - Consensus: {rec['consensus']}")
        print(f"    - Miner: {rec['miner']}")
        print(f"    - Description: {rec['description']}")
    
    # Show startup commands
    print(f"\n🚀 EXAMPLE STARTUP COMMANDS:")
    print(f"  Validator 1 (balanced): {config_manager.generate_startup_command('validator', 1, 'balanced')}")
    print(f"  Miner 1 (adaptive): {config_manager.generate_startup_command('miner', 1, miner_mode = 'adaptive')}")


if __name__ == "__main__":
    demo_config_usage()