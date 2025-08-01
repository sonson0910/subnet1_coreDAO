#!/usr/bin/env python3
"""
Auto-register entities with ModernTensorAI v2.0 - Bittensor Edition
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

def register_v2_entities():
    """Auto-register all entities with v2 contract"""
    print("🚀 AUTO-REGISTERING WITH V2.0 CONTRACT")
    print("=" * 60)
    
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
    
    # Contract ABIs for tokens and main contract
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
    
    # Transfer tokens to entities first
    entities = [
        ("Miner 1", "0xd89fBAbb72190ed22F012ADFC693ad974bAD3005", "e9c03148c011d553d43b485d73b1407d24f1498a664f782dc0204e524855be4e", "miner", "0.05"),
        ("Validator 1", "0x25F3D6316017FDF7A4f4e54003b29212a198768f", "3ac6e82cf34e51d376395af0338d0b1162c1d39b9d34614ed40186fd2367b33d", "validator", "0.08")
    ]
    
    # Step 1: Transfer CORE tokens to entities
    print(f"\n💰 TRANSFERRING CORE TOKENS TO ENTITIES...")
    for name, address, private_key, entity_type, stake_amount in entities:
        stake_wei = w3.to_wei(stake_amount, 'ether')
        transfer_amount = stake_wei * 2  # Transfer 2x needed for approval + stake
        
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
    for name, address, private_key, entity_type, stake_amount in entities:
        stake_wei = w3.to_wei(stake_amount, 'ether')
        api_endpoint = f"http://{entity_type}1-api.moderntensor.com"
        
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
                'value': 0  # No direct ETH transfer needed for v2
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
    
    print(f"\n🎉 REGISTRATION COMPLETED!")
    print(f"🔍 Check contract: https://scan.test.btcs.network/address/{contract_address}")

if __name__ == "__main__":
    register_v2_entities()
