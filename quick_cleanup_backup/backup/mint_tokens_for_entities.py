#!/usr/bin/env python3

import os
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import json
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🪙 MINTING CORE TOKENS FOR ENTITIES")
    print(" = " * 50)
    
    # Connect to Core Testnet
    rpc_url  =  "https://rpc.test.btcs.network"
    web3  =  Web3(Web3.HTTPProvider(rpc_url))
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer = 0)
    
    core_token_address  =  os.getenv('CORE_TOKEN_ADDRESS')
    deployer_key  =  "0x3ace434e2cd05cd0e614eb5d423cf04e4b925c17db9869e9c598851f88f52840"
    deployer_account  =  web3.eth.account.from_key(deployer_key)
    
    print(f"🔧 Core Token: {core_token_address}")
    print(f"🔧 Token Owner: {deployer_account.address}")
    
    # ERC20 ABI with mint function
    erc20_abi  =  [
        {
            "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}],
            "name": "mint",
            "outputs": [],
            "type": "function"
        },
        {
            "inputs": [{"name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function"
        }
    ]
    
    core_token = web3.eth.contract(address=core_token_address, abi = erc20_abi)
    
    # Entity addresses
    entities  =  [
        ("Miner 1", os.getenv('MINER_1_ADDRESS'), "1.0"),
        ("Miner 2", os.getenv('MINER_2_ADDRESS'), "1.0"), 
        ("Validator 1", os.getenv('VALIDATOR_1_ADDRESS'), "1.0"),
        ("Validator 2", os.getenv('VALIDATOR_2_ADDRESS'), "1.0")
    ]
    
    for name, address, amount in entities:
        if not address:
            print(f"❌ No address for {name}"):
            continue
            
        print(f"\n🪙 Minting {amount} CORE tokens for {name} ({address})"):
        
        try:
            # Check current balance
            current_balance  =  core_token.functions.balanceOf(address).call()
            print(f"   Current balance: {web3.from_wei(current_balance, 'ether')} CORE")
            
            # Mint tokens
            mint_amount  =  web3.to_wei(amount, 'ether')
            
            tx_data  =  core_token.functions.mint(address, mint_amount).build_transaction
                'gasPrice': web3.to_wei(30, 'gwei'),
                'nonce': web3.eth.get_transaction_count(deployer_account.address),
            })
            
            # Sign and send
            signed_tx  =  web3.eth.account.sign_transaction(tx_data, deployer_key)
            raw_tx  =  getattr(signed_tx, 'rawTransaction', getattr(signed_tx, 'raw_transaction', None))
            tx_hash  =  web3.eth.send_raw_transaction(raw_tx)
            
            print(f"   📤 Mint tx: {tx_hash.hex()}")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout = 60)
            
            if receipt.status == 1:
                # Check new balance
                new_balance  =  core_token.functions.balanceOf(address).call()
                print(f"   ✅ Minted successfully! New balance: {web3.from_wei(new_balance, 'ether')} CORE")
            else:
                print(f"   ❌ Mint failed for {name}"):
                
        except Exception as e:
            print(f"   💥 Error minting for {name}: {e}"):

if __name__ == "__main__":
    main()
