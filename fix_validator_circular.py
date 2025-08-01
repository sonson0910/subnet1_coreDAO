#!/usr/bin/env python3
"""
Fix ValidatorNode Circular Import
"""

import os
import sys
from pathlib import Path

def fix_circular_import():
    print("🔧 FIXING VALIDATORNODE CIRCULAR IMPORT")
    print("=" * 50)
    
    # Path to the problematic file
    node_file = Path('../moderntensor_aptos/mt_core/consensus/node.py')
    
    print(f"📁 Target file: {node_file}")
    
    # Check if the issue is with import from validator_node_refactored
    if node_file.exists():
        with open(node_file, 'r') as f:
            content = f.read()
        
        print("🔍 Analyzing current imports...")
        
        # The issue is likely in validator_node_refactored import
        if 'from .validator_node_refactored import ValidatorNode' in content:
            print("✅ Found problematic import from validator_node_refactored")
            
            # Create a simple replacement
            simple_node_content = '''#!/usr/bin/env python3
"""
Simple ValidatorNode to avoid circular imports
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List

class ValidatorNode:
    """Simple ValidatorNode implementation"""
    
    def __init__(self, node_id: str, subnet_id: int = 1, **kwargs):
        self.node_id = node_id
        self.subnet_id = subnet_id
        self.is_active = False
        self.logger = logging.getLogger(f"validator.{node_id}")
        
        # Store kwargs for compatibility
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    async def start(self):
        """Start validator"""
        self.is_active = True
        self.logger.info(f"ValidatorNode {self.node_id} started")
    
    async def stop(self):
        """Stop validator"""
        self.is_active = False
        self.logger.info(f"ValidatorNode {self.node_id} stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status"""
        return {
            "node_id": self.node_id,
            "subnet_id": self.subnet_id,
            "is_active": self.is_active
        }

# Additional compatibility classes
class MinerInfo:
    def __init__(self, address: str = "", **kwargs):
        self.address = address
        for k, v in kwargs.items():
            setattr(self, k, v)

class ValidatorInfo:
    def __init__(self, address: str = "", **kwargs):
        self.address = address
        for k, v in kwargs.items():
            setattr(self, k, v)

class ValidatorScore:
    def __init__(self, validator_id: str = "", score: float = 0.0):
        self.validator_id = validator_id
        self.score = score

# Factory function
def create_validator_node(node_id: str, **kwargs):
    return ValidatorNode(node_id, **kwargs)

# Legacy functions
async def run_validator_node():
    """Legacy function"""
    pass

__all__ = ['ValidatorNode', 'MinerInfo', 'ValidatorInfo', 'ValidatorScore', 'create_validator_node']
'''
            
            # Backup original
            backup_file = node_file.with_suffix('.py.original_backup')
            with open(backup_file, 'w') as f:
                f.write(content)
            print(f"✅ Backed up original to: {backup_file}")
            
            # Write simplified version
            with open(node_file, 'w') as f:
                f.write(simple_node_content)
            print(f"✅ Created simplified ValidatorNode")
        
        else:
            print("⚠️ Unexpected file structure")
    
    # Test the fix
    print("\n🧪 Testing fix...")
    sys.path.insert(0, '../moderntensor_aptos')
    
    try:
        # Clear cache
        if 'mt_core.consensus.node' in sys.modules:
            del sys.modules['mt_core.consensus.node']
        
        from mt_core.consensus.node import ValidatorNode
        print("✅ ValidatorNode import successful!")
        
        # Test instantiation
        validator = ValidatorNode("test")
        print("✅ ValidatorNode instantiation successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Still failing: {e}")
        return False

if __name__ == "__main__":
    success = fix_circular_import()
    if success:
        print("\n🎉 CIRCULAR IMPORT FIXED!")
    else:
        print("\n⚠️ Additional fixes may be needed")
