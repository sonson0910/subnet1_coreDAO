#!/usr/bin/env python3
"""
Auto-register all entities to the Core smart contract
"""

import json
import os
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv
import time

# Load environment
load_dotenv()

def register_all_entities():
    """Register all miners and validators to the smart contract"""
    print("🚀 AUTO-REGISTERING ALL ENTITIES")
    print("=" * 50)
    
    # Configuration
    rpc_url = os.getenv("CORE_NODE_URL", "https://rpc.test.btcs.network")
    contract_address = os.getenv("CORE_CONTRACT_ADDRESS", "0x3dACb0Ac7A913Fa94f383f7d6CF0a7BC2b5498DD")
    
    print(f"🌐 RPC: {rpc_url}")
    print(f"📝 Contract: {contract_address}")
    
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
            print("⚠️ POA middleware not available")
    
    if not w3.is_connected():
        print("❌ Failed to connect to Core RPC")
        return
    
    print(f"✅ Connected to Core (Chain ID: {w3.eth.chain_id})")
    
    # Contract ABI (simplified for registration)
    contract_abi = [
        {
            "name": "registerMiner",
            "type": "function",
            "inputs": [
                {"name": "coreStake", "type": "uint256"},
                {"name": "btcStake", "type": "uint256"}, 
                {"name": "subnetId", "type": "uint256"}
            ],
            "outputs": [],
            "stateMutability": "payable"
        },
        {
            "name": "registerValidator",
            "type": "function",
            "inputs": [
                {"name": "coreStake", "type": "uint256"},
                {"name": "btcStake", "type": "uint256"},
                {"name": "subnetId", "type": "uint256"}
            ],
            "outputs": [],
            "stateMutability": "payable"
        }
    ]
    
    # Create contract instance
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    
    # Load entities
    entities_dir = Path("entities")
    if not entities_dir.exists():
        print("❌ Entities directory not found")
        return
    
    # Register each entity
    for entity_file in sorted(entities_dir.glob("*.json")):
        with open(entity_file) as f:
            entity = json.load(f)
        
        entity_type = "miner" if "miner" in entity_file.name else "validator"
        address = entity["address"]
        private_key = entity["private_key"]
        
        # Stake amounts (wei)
        if entity_type == "miner":
            core_stake = int(0.05 * 10**18)  # 0.05 CORE
        else:
            core_stake = int(0.08 * 10**18)  # 0.08 CORE  
        
        btc_stake = 0  # No BTC stake for now
        subnet_id = 1  # Default subnet
        
        print(f"\n🔨 REGISTERING {entity_type.upper()}: {address}")
        print(f"  💰 CORE Stake: {core_stake / 10**18} CORE")
        
        try:
            # Check balance
            balance = w3.eth.get_balance(address)
            balance_core = Web3.from_wei(balance, 'ether')
            print(f"  💳 Balance: {balance_core} CORE")
            
            if balance_core < 0.1:
                print(f"  ⚠️ Low balance, may not have enough for gas")
                continue
            
            # Create account from private key
            account = w3.eth.account.from_key(private_key)
            
            # Build transaction
            if entity_type == "miner":
                function = contract.functions.registerMiner(core_stake, btc_stake, subnet_id)
            else:
                function = contract.functions.registerValidator(core_stake, btc_stake, subnet_id)
            
            # Estimate gas
            try:
                gas_estimate = function.estimate_gas({'from': address, 'value': core_stake})
                gas_price = w3.eth.gas_price
                
                print(f"  ⛽ Estimated Gas: {gas_estimate:,}")
                print(f"  ⛽ Gas Price: {Web3.from_wei(gas_price, 'gwei')} Gwei")
                
                # Build transaction
                transaction = function.build_transaction({
                    'from': address,
                    'gas': gas_estimate + 50000,  # Add buffer
                    'gasPrice': gas_price,
                    'nonce': w3.eth.get_transaction_count(address),
                    'value': core_stake  # Send CORE for staking
                })
                
                # Sign transaction
                signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
                
                # Send transaction
                print(f"  📤 Sending transaction...")
                tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                
                print(f"  🔗 Transaction hash: {tx_hash.hex()}")
                print(f"  🔍 Explorer: https://scan.test.btcs.network/tx/{tx_hash.hex()}")
                
                # Wait for confirmation
                print(f"  ⏳ Waiting for confirmation...")
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                
                if receipt.status == 1:
                    print(f"  ✅ Registration SUCCESS!")
                else:
                    print(f"  ❌ Registration FAILED!")
                
                # Wait between transactions
                time.sleep(5)
                
            except Exception as e:
                print(f"  ❌ Gas estimation failed: {e}")
                # Try with manual gas
                print(f"  🔄 Trying with manual gas...")
                try:
                    transaction = function.build_transaction({
                        'from': address,
                        'gas': 300000,  # Manual gas limit
                        'gasPrice': w3.eth.gas_price,
                        'nonce': w3.eth.get_transaction_count(address),
                        'value': core_stake
                    })
                    
                    signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
                    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    
                    print(f"  🔗 Transaction hash: {tx_hash.hex()}")
                    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                    
                    if receipt.status == 1:
                        print(f"  ✅ Registration SUCCESS!")
                    else:
                        print(f"  ❌ Registration FAILED!")
                        
                except Exception as e2:
                    print(f"  ❌ Manual transaction also failed: {e2}")
             
        except Exception as e:
            print(f"  ❌ Error registering {entity_type}: {e}")
    
    print(f"\n🎉 REGISTRATION COMPLETED!")
    print(f"🔍 Check registrations at: https://scan.test.btcs.network/address/{contract_address}")

if __name__ == "__main__":
    register_all_entities()
