#!/usr/bin/env python3
"""
Register remaining entities: Miner 2, Validator 2, Validator 3
"""

import sys
import os
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv
import json
import time

# Load environment
load_dotenv()

def register_remaining_entities():
    """Register the remaining entities to complete the network"""
    print("🚀 REGISTERING REMAINING ENTITIES")
    print("=" * 50)
    print("Target: 2 Miners + 3 Validators")
    print()
    
    # Configuration
    rpc_url = os.getenv("CORE_NODE_URL", "https://rpc.test.btcs.network")
    contract_address = os.getenv("CORE_CONTRACT_ADDRESS")
    core_token_address = os.getenv("CORE_TOKEN_ADDRESS")
    
    print(f"🌐 RPC URL: {rpc_url}")
    print(f"📝 Contract: {contract_address}")
    print(f"💰 CORE Token: {core_token_address}")
    print()
    
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
    
    # Contract ABIs
    erc20_abi = [
        {
            "name": "transfer",
            "type": "function",
            "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}],
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "nonpayable"
        },
        {
            "name": "balanceOf",
            "type": "function",
            "inputs": [{"name": "account", "type": "address"}],
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view"
        },
        {
            "name": "approve",
            "type": "function",
            "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "nonpayable"
        }
    ]
    
    contract_abi = [
        {
            "name": "registerMiner",
            "type": "function",
            "inputs": [
                {"name": "subnetId", "type": "uint64"},
                {"name": "coreStake", "type": "uint256"},
                {"name": "btcStake", "type": "uint256"},
                {"name": "apiEndpoint", "type": "string"}
            ],
            "outputs": [],
            "stateMutability": "payable"
        },
        {
            "name": "registerValidator",
            "type": "function",
            "inputs": [
                {"name": "subnetId", "type": "uint64"},
                {"name": "coreStake", "type": "uint256"},
                {"name": "btcStake", "type": "uint256"},
                {"name": "apiEndpoint", "type": "string"}
            ],
            "outputs": [],
            "stateMutability": "payable"
        },
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
        }
    ]
    
    # Create contract instances
    core_token = w3.eth.contract(address=core_token_address, abi=erc20_abi)
    main_contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    
    # Get deployer account
    deployer_private_key = "0xa07b6e0db803f9a21ffd1001c76b0aa0b313aaba8faab8c771af47301c4452b4"
    deployer_account = w3.eth.account.from_key(deployer_private_key)
    deployer_address = deployer_account.address
    
    print(f"👤 Deployer: {deployer_address}")
    
    # Check current network state
    print(f"\n📊 CURRENT NETWORK STATE:")
    try:
        network_stats = main_contract.functions.getNetworkStats().call()
        print(f"  👥 Current Miners: {network_stats[0]}")
        print(f"  🛡️ Current Validators: {network_stats[1]}")
        print(f"  💰 Total Staked: {Web3.from_wei(network_stats[2], 'ether')} CORE")
    except Exception as e:
        print(f"  ❌ Error getting stats: {e}")
    
    # Entities to register (remaining ones)
    remaining_entities = [
        ("Miner 2", os.getenv("MINER_2_ADDRESS"), os.getenv("MINER_2_PRIVATE_KEY"), "miner", "0.05"),
        ("Validator 2", os.getenv("VALIDATOR_2_ADDRESS"), os.getenv("VALIDATOR_2_PRIVATE_KEY"), "validator", "0.08"),
        ("Validator 3", os.getenv("VALIDATOR_3_ADDRESS", "0x352516F491DFB3E6a55bFa9c58C551Ef10267dbB"), os.getenv("VALIDATOR_3_PRIVATE_KEY", "df51093c674459eb0a5cc8a273418061fe4d7ca189bd84b74f478271714e0920"), "validator", "0.08")
    ]
    
    print(f"\n🎯 ENTITIES TO REGISTER:")
    for name, address, private_key, entity_type, stake in remaining_entities:
        if address and private_key:
            print(f"  ✅ {name}: {address} ({entity_type}, {stake} CORE)")
        else:
            print(f"  ❌ {name}: Missing config")
    
    # Step 1: Transfer CORE tokens to entities
    print(f"\n💰 TRANSFERRING CORE TOKENS...")
    for name, address, private_key, entity_type, stake_amount in remaining_entities:
        if not address or not private_key:
            print(f"  ⏭️ Skipping {name} - missing config")
            continue
            
        stake_wei = w3.to_wei(stake_amount, 'ether')
        transfer_amount = stake_wei * 2  # Transfer 2x needed
        
        print(f"\n🔄 Transferring to {name}...")
        try:
            # Build transfer transaction
            transfer_txn = core_token.functions.transfer(
                address, transfer_amount
            ).build_transaction({
                'from': deployer_address,
                'gas': 100000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(deployer_address)
            })
            
            # Sign and send
            signed_txn = w3.eth.account.sign_transaction(transfer_txn, deployer_private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                print(f"  ✅ Transferred {Web3.from_wei(transfer_amount, 'ether')} CORE to {name}")
            else:
                print(f"  ❌ Transfer failed for {name}")
                
        except Exception as e:
            print(f"  ❌ Transfer error for {name}: {e}")
        
        time.sleep(2)
    
    # Step 2: Register entities
    print(f"\n🔨 REGISTERING ENTITIES...")
    for name, address, private_key, entity_type, stake_amount in remaining_entities:
        if not address or not private_key:
            print(f"  ⏭️ Skipping {name} - missing config")
            continue
            
        stake_wei = w3.to_wei(stake_amount, 'ether')
        api_endpoint = f"http://{entity_type}2-api.moderntensor.com" if "2" in name else f"http://{entity_type}3-api.moderntensor.com"
        
        print(f"\n🚀 Registering {name}...")
        try:
            # Create account
            account = w3.eth.account.from_key(private_key)
            
            # Check balance
            balance = core_token.functions.balanceOf(address).call()
            print(f"  💳 Balance: {Web3.from_wei(balance, 'ether')} CORE")
            
            if balance < stake_wei:
                print(f"  ❌ Insufficient balance for {name}")
                continue
            
            # Approve spending
            approve_txn = core_token.functions.approve(
                contract_address, stake_wei
            ).build_transaction({
                'from': address,
                'gas': 100000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(address)
            })
            
            signed_approve = w3.eth.account.sign_transaction(approve_txn, private_key)
            approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
            approve_receipt = w3.eth.wait_for_transaction_receipt(approve_hash)
            
            if approve_receipt.status == 1:
                print(f"  ✅ Approved spending for {name}")
            else:
                print(f"  ❌ Approval failed for {name}")
                continue
            
            time.sleep(3)
            
            # Register entity
            if entity_type == "miner":
                register_function = main_contract.functions.registerMiner(
                    0,  # subnetId
                    stake_wei,  # coreStake
                    0,  # btcStake
                    api_endpoint
                )
            else:
                register_function = main_contract.functions.registerValidator(
                    0,  # subnetId
                    stake_wei,  # coreStake
                    0,  # btcStake
                    api_endpoint
                )
            
            register_txn = register_function.build_transaction({
                'from': address,
                'gas': 500000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(address),
                'value': 0
            })
            
            signed_register = w3.eth.account.sign_transaction(register_txn, private_key)
            register_hash = w3.eth.send_raw_transaction(signed_register.raw_transaction)
            
            print(f"  📤 Registration TX: {register_hash.hex()}")
            register_receipt = w3.eth.wait_for_transaction_receipt(register_hash)
            
            if register_receipt.status == 1:
                print(f"  🎉 {name} registered successfully!")
                print(f"  🔗 Explorer: https://scan.test.btcs.network/tx/{register_hash.hex()}")
            else:
                print(f"  ❌ Registration failed for {name}")
                
        except Exception as e:
            print(f"  ❌ Registration error for {name}: {e}")
        
        time.sleep(5)
    
    # Final network state check
    print(f"\n📊 FINAL NETWORK STATE:")
    try:
        network_stats = main_contract.functions.getNetworkStats().call()
        print(f"  👥 Total Miners: {network_stats[0]} / 2 target")
        print(f"  🛡️ Total Validators: {network_stats[1]} / 3 target")
        print(f"  💰 Total Staked: {Web3.from_wei(network_stats[2], 'ether')} CORE")
        
        if network_stats[0] >= 2 and network_stats[1] >= 3:
            print(f"\n🎉 TARGET ACHIEVED! 2 Miners + 3 Validators!")
        else:
            print(f"\n⚠️ Still need more entities to reach target")
            
    except Exception as e:
        print(f"  ❌ Error getting final stats: {e}")
    
    print(f"\n🔍 Check contract: https://scan.test.btcs.network/address/{contract_address}")

if __name__ == "__main__":
    register_remaining_entities()
