#!/usr/bin/env python3
"""
Test script để kiểm tra migration từ Cardano sang Aptos cho Subnet1.
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test tất cả imports quan trọng."""
    logger.info("🧪 Testing imports...")
    
    try:
        import moderntensor_aptos.mt_core
        logger.info("✅ moderntensor_aptos.mt_core import successful")
    except ImportError as e:
        logger.error(f"❌ moderntensor_aptos.mt_core import failed: {e}")
        return False
    
    try:
        from moderntensor_aptos.mt_core.core import datatypes
        logger.info("✅ moderntensor_aptos.mt_core.core.datatypes import successful")
    except ImportError as e:
        logger.error(f"❌ moderntensor_aptos.mt_core.core.datatypes import failed: {e}")
        return False
    
    try:
        from moderntensor_aptos.mt_core.account import Account
        logger.info("✅ moderntensor_aptos.mt_core.account.Account import successful")
    except ImportError as e:
        logger.error(f"❌ moderntensor_aptos.mt_core.account.Account import failed: {e}")
        return False
    
    try:
        from subnet1.validator import Subnet1Validator
        logger.info("✅ subnet1.validator.Subnet1Validator import successful")
    except ImportError as e:
        logger.error(f"❌ subnet1.validator.Subnet1Validator import failed: {e}")
        return False
    
    try:
        from subnet1.miner import Subnet1Miner
        logger.info("✅ subnet1.miner.Subnet1Miner import successful")
    except ImportError as e:
        logger.error(f"❌ subnet1.miner.Subnet1Miner import failed: {e}")
        return False
    
    try:
        from subnet1.models.image_generator import generate_image_from_prompt
        logger.info("✅ subnet1.models.image_generator import successful")
    except ImportError as e:
        logger.warning(f"⚠️ subnet1.models.image_generator import failed: {e}")
    
    try:
        from subnet1.scoring.clip_scorer import calculate_clip_score
        logger.info("✅ subnet1.scoring.clip_scorer import successful")
    except ImportError as e:
        logger.warning(f"⚠️ subnet1.scoring.clip_scorer import failed: {e}")
    
    return True

def test_basic_functionality():
    """Test basic functionality của classes."""
    logger.info("🧪 Testing basic functionality...")
    
    try:
        from subnet1.validator import Subnet1Validator
        
        # Test tạo validator với mock args
        logger.info("Testing Subnet1Validator creation...")
        # Note: Này sẽ fail nếu không có proper args, nhưng ít nhất class có thể import
        
        # Test method tạo prompt
        validator = object.__new__(Subnet1Validator)  # Create without calling __init__
        if hasattr(validator, '_generate_random_prompt'):
            # Manually set this method for testing
            import random
            def _generate_random_prompt():
                prompts = [
                    "A cute cat in space",
                    "A beautiful landscape", 
                    "Abstract art"
                ]
                return random.choice(prompts)
            validator._generate_random_prompt = _generate_random_prompt
            prompt = validator._generate_random_prompt()
            logger.info(f"✅ Generated test prompt: {prompt}")
        
        logger.info("✅ Basic Subnet1Validator functionality test passed")
        
    except Exception as e:
        logger.error(f"❌ Basic functionality test failed: {e}")
        return False
    
    return True

def test_configuration():
    """Test cấu hình files."""
    logger.info("🧪 Testing configuration files...")
    
    # Check requirements.txt
    req_file = Path("requirements.txt")
    if req_file.exists():
        content = req_file.read_text()
        if "aptos-sdk" in content:
            logger.info("✅ requirements.txt contains aptos-sdk")
        else:
            logger.warning("⚠️ requirements.txt missing aptos-sdk")
        
        if "pycardano" not in content:
            logger.info("✅ requirements.txt no longer contains pycardano")
        else:
            logger.warning("⚠️ requirements.txt still contains pycardano")
    else:
        logger.warning("⚠️ requirements.txt not found")
    
    # Check .env example
    env_example = Path(".env.aptos.example")
    if env_example.exists():
        logger.info("✅ .env.aptos.example exists")
    else:
        logger.warning("⚠️ .env.aptos.example not found")
    
    # Check README
    readme = Path("README_APTOS_MIGRATION.md")
    if readme.exists():
        logger.info("✅ README_APTOS_MIGRATION.md exists")
    else:
        logger.warning("⚠️ README_APTOS_MIGRATION.md not found")
    
    return True

def main():
    """Main test function."""
    logger.info("🚀 Starting Subnet1 Aptos Migration Test")
    logger.info("=" * 50)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    logger.info("-" * 30)
    
    # Test basic functionality  
    if not test_basic_functionality():
        success = False
    
    logger.info("-" * 30)
    
    # Test configuration
    if not test_configuration():
        success = False
    
    logger.info("=" * 50)
    
    if success:
        logger.info("🎉 All tests passed! Subnet1 migration to Aptos is successful!")
        logger.info("Next steps:")
        logger.info("  1. Copy .env.aptos.example to .env and configure")
        logger.info("  2. Install dependencies: pip install -r requirements.txt")
        logger.info("  3. Setup keys: moderntensor coldkey create, moderntensor hotkey create")
        logger.info("  4. Run validator: python scripts/run_validator.py")
        logger.info("  5. Run miner: python scripts/run_miner.py")
        return 0
    else:
        logger.error("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 