#!/usr/bin/env python3
"""
Quick check của validators trên blockchain
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from moderntensor_aptos.mt_core.metagraph.core_metagraph_adapter import CoreMetagraphClient
    
    print("🔍 QUICK VALIDATOR CHECK")
    print("=" * 50)
    
    print("📊 Checking blockchain...")
    core_client = CoreMetagraphClient()
    
    validators_addresses = core_client.get_all_validators()
    miners_addresses = core_client.get_all_miners()
    
    print(f"✅ Validators registered: {len(validators_addresses)}")
    for i, addr in enumerate(validators_addresses):
        print(f"   [{i+1}] {addr}")
        try:
            validator_info = core_client.get_validator_info(addr)
            status = validator_info.get('status', 'N/A')
            endpoint = validator_info.get('api_endpoint', 'N/A')
            uid = validator_info.get('uid', 'N/A')
            print(f"       UID: {uid}")
            print(f"       Status: {status} ({type(status)})")
            print(f"       Endpoint: {endpoint}")
        except Exception as ve:
            print(f"       ❌ Error: {ve}")
        print()
            
    print(f"✅ Miners registered: {len(miners_addresses)}")
    for i, addr in enumerate(miners_addresses):
        print(f"   [{i+1}] {addr}")
        try:
            miner_info = core_client.get_miner_info(addr)
            status = miner_info.get('status', 'N/A')
            endpoint = miner_info.get('api_endpoint', 'N/A')
            uid = miner_info.get('uid', 'N/A')
            print(f"       UID: {uid}")
            print(f"       Status: {status} ({type(status)})")
            print(f"       Endpoint: {endpoint}")
        except Exception as me:
            print(f"       ❌ Error: {me}")
        print()
        
    print("🎯 SUMMARY:")
    print(f"   - Validators: {len(validators_addresses)}")
    print(f"   - Miners: {len(miners_addresses)}")
    
    if len(validators_addresses) <= 1:
        print("   ❌ PROBLEM: Chỉ có ≤1 validator → Không thể P2P!")
        print("   💡 SOLUTION: Cần register thêm validators")
    else:
        print("   ✅ Multiple validators → P2P có thể work")
        
    # Check endpoints
    active_endpoints = []
    for addr in validators_addresses:
        try:
            validator_info = core_client.get_validator_info(addr)
            endpoint = validator_info.get('api_endpoint', '')
            if endpoint and endpoint.startswith('http'):
                active_endpoints.append(endpoint)
        except:
            pass
            
    print(f"   - Active endpoints: {len(active_endpoints)}")
    for ep in active_endpoints:
        print(f"     • {ep}")
        
    if len(active_endpoints) <= 1:
        print("   ❌ PROBLEM: ≤1 active endpoint → No P2P targets!")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()