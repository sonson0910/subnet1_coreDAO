#!/usr/bin/env python3

import os
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🔄 TRANSFER 0.1 CORE FROM EACH ENTITY BACK TO MAIN WALLET")
    print("=" * 60)
    
    # Connect to Core Testnet
    rpc_url = "https://rpc.test.btcs.network"
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    
    # Main deployer address (destination)
    main_address = "0x16102CA8BEF74fb6214AF352989b664BF0e50498"
    print(f"🎯 Destination: {main_address}")
    
    # Check main wallet balance before
    main_balance_before = web3.from_wei(web3.eth.get_balance(main_address), 'ether')
    print(f"💰 Main Balance Before: {main_balance_before} CORE")
    
    # Entity wallets with their private keys
    entities = [
        {
            'name': 'Miner 1',
            'private_key': os.getenv('MINER_1_PRIVATE_KEY'),
            'address': os.getenv('MINER_1_ADDRESS')
        },
        {
            'name': 'Miner 2', 
            'private_key': os.getenv('MINER_2_PRIVATE_KEY'),
            'address': os.getenv('MINER_2_ADDRESS')
        },
        {
            'name': 'Validator 1',
            'private_key': os.getenv('VALIDATOR_1_PRIVATE_KEY'),
            'address': os.getenv('VALIDATOR_1_ADDRESS')
        },
        {
            'name': 'Validator 2',
            'private_key': os.getenv('VALIDATOR_2_PRIVATE_KEY'),
            'address': os.getenv('VALIDATOR_2_ADDRESS')
        }
    ]
    
    # Amount to transfer from each (0.1 CORE)
    amount_to_transfer = web3.to_wei('0.1', 'ether')
    
    print(f"\n📊 TRANSFERRING 0.1 CORE FROM EACH ENTITY...")
    print("-" * 50)
    
    total_transferred = 0
    
    for entity in entities:
        try:
            print(f"\n💸 Transferring from {entity['name']}...")
            print(f"   Address: {entity['address']}")
            
            # Create account from private key
            account = web3.eth.account.from_key(entity['private_key'])
            
            # Check current balance
            balance = web3.eth.get_balance(account.address)
            balance_eth = web3.from_wei(balance, 'ether')
            print(f"   Balance: {balance_eth} CORE")
            
            if balance_eth < 0.11:  # Need 0.1 + gas
                print(f"   ❌ Insufficient balance for transfer")
                continue
            
            # Build transaction
            tx = {
                'to': main_address,
                'value': amount_to_transfer,
                'gas': 21000,
                'gasPrice': web3.to_wei('20', 'gwei'),
                'nonce': web3.eth.get_transaction_count(account.address)
            }
            
            # Sign and send
            signed_tx = account.sign_transaction(tx)
            raw_tx = getattr(signed_tx, 'rawTransaction', getattr(signed_tx, 'raw_transaction', None))
            tx_hash = web3.eth.send_raw_transaction(raw_tx)
            
            print(f"   📤 TX Hash: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"   ✅ Transfer confirmed! Gas used: {receipt['gasUsed']}")
            
            total_transferred += 0.1
            
        except Exception as e:
            print(f"   ❌ Error transferring from {entity['name']}: {e}")
    
    # Check main wallet balance after
    main_balance_after = web3.from_wei(web3.eth.get_balance(main_address), 'ether')
    print(f"\n🎯 TRANSFER SUMMARY:")
    print("=" * 30)
    print(f"💰 Main Balance Before: {main_balance_before} CORE")
    print(f"💰 Main Balance After: {main_balance_after} CORE")
    print(f"📈 Total Gained: {main_balance_after - main_balance_before} CORE")
    print(f"📊 Expected Gain: {total_transferred} CORE")

if __name__ == "__main__":
    main()
