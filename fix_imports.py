#!/usr/bin/env python3
"""
Fix ModernTensor Import Issues
"""

import os
import re
from pathlib import Path

def fix_file(file_path):
    """Fix import issues in a file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original = content
        
        # Add sys.path if not exists
        if 'from moderntensor_aptos' in content and 'sys.path.append' not in content:
            # Add path setup at top
            path_code = '''import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../moderntensor_aptos'))

'''
            # Find first import
            first_import = re.search(r'^(import |from )', content, re.MULTILINE)
            if first_import:
                pos = first_import.start()
                content = content[:pos] + path_code + content[pos:]
        
        # Fix import paths
        fixes = [
            ('from moderntensor_aptos.mt_core', 'from mt_core'),
        ]
        
        for old, new in fixes:
            content = content.replace(old, new)
        
        if content != original:
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    files = [
        'subnet1/miner.py',
        'subnet1/validator.py', 
        'subnet1/create_initial_state.py'
    ]
    
    print("🔧 Fixing import issues...")
    fixed = 0
    
    for file_path in files:
        if os.path.exists(file_path):
            if fix_file(file_path):
                print(f"✅ Fixed: {file_path}")
                fixed += 1
            else:
                print(f"➡️ No changes: {file_path}")
        else:
            print(f"❌ Not found: {file_path}")
    
    print(f"\n📊 Fixed {fixed} files")
    
    # Test import
    print("\n🧪 Testing imports...")
    import sys
    sys.path.append('../moderntensor_aptos')
    
    try:
        from mt_core.config.settings import settings
        print("✅ mt_core.config.settings: SUCCESS")
    except Exception as e:
        print(f"❌ mt_core.config.settings: {e}")

if __name__ == "__main__":
    main()
