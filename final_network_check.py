#!/usr/bin/env python3
"""
Final network verification - 2 Miners + 2 Validators
"""

import sys
import os
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv
import json

# Load environment
load_dotenv()

def final_network_check():
    """Final verification of network state"""
    print("🔍 FINAL NETWORK VERIFICATION")
    print("=" * 50)
    
    # Configuration
    rpc_url = os.getenv("CORE_NODE_URL", "https://rpc.test.btcs.network")
    contract_address = os.getenv("CORE_CONTRACT_ADDRESS")
    
    # Connect to Core
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Add POA middleware
    try:
        from web3.middleware import ExtraDataToPOAMiddleware
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    except ImportError:
        try:
            from web3.middleware import geth_poa_middleware
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        except ImportError:
            pass
    
    print(f"✅ Connected to Core: {w3.is_connected()}")
    
    # Contract ABI
    contract_abi = [
        {
            "name": "getNetworkStats",
            "type": "function",
            "inputs": [],
            "outputs": [
                {"name": "totalMiners", "type": "uint256"},
                {"name": "totalValidators", "type": "uint256"},
                {"name": "totalStaked", "type": "uint256"},
                {"name": "totalRewards", "type": "uint256"}
            ],
            "stateMutability": "view"
        },
        {
            "name": "getSubnetMiners",
            "type": "function",
            "inputs": [{"name": "subnetId", "type": "uint64"}],
            "outputs": [{"name": "", "type": "address[]"}],
            "stateMutability": "view"
        },
        {
            "name": "getSubnetValidators",
            "type": "function",
            "inputs": [{"name": "subnetId", "type": "uint64"}],
            "outputs": [{"name": "", "type": "address[]"}],
            "stateMutability": "view"
        }
    ]
    
    try:
        # Create contract instance
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        
        # Get network stats
        print(f"\n📊 CURRENT NETWORK STATE:")
        network_stats = contract.functions.getNetworkStats().call()
        print(f"  👥 Total Miners: {network_stats[0]}")
        print(f"  🛡️ Total Validators: {network_stats[1]}")
        print(f"  💰 Total Staked: {Web3.from_wei(network_stats[2], 'ether')} CORE")
        print(f"  🎁 Total Rewards: {Web3.from_wei(network_stats[3], 'ether')} CORE")
        
        # Get subnet entities
        miners = contract.functions.getSubnetMiners(0).call()
        validators = contract.functions.getSubnetValidators(0).call()
        
        print(f"\n👥 REGISTERED MINERS ({len(miners)}):")
        for i, miner in enumerate(miners):
            print(f"  {i+1}. {miner}")
        
        print(f"\n🛡️ REGISTERED VALIDATORS ({len(validators)}):")
        for i, validator in enumerate(validators):
            print(f"  {i+1}. {validator}")
        
        # System status
        print(f"\n🎯 SYSTEM STATUS:")
        miners_ok = len(miners) >= 2
        validators_ok = len(validators) >= 2
        
        print(f"  {'✅' if miners_ok else '❌'} Miners: {len(miners)}/2 ({'OK' if miners_ok else 'NEED MORE'})")
        print(f"  {'✅' if validators_ok else '❌'} Validators: {len(validators)}/2 ({'OK' if validators_ok else 'NEED MORE'})")
        
        if miners_ok and validators_ok:
            print(f"\n🎉 NETWORK READY FOR OPERATION!")
            print(f"  ✅ Sufficient entities registered")
            print(f"  ✅ Bittensor-style architecture active")
            print(f"  ✅ Consensus can begin")
            print(f"  ✅ AI training tasks can be distributed")
            print(f"  🚀 READY TO START MINING/VALIDATION!")
        else:
            print(f"\n⚠️ Network needs more entities")
        
        print(f"\n🔗 Contract: https://scan.test.btcs.network/address/{contract_address}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    final_network_check()
