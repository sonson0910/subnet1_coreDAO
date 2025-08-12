#!/usr/bin/env python3

import os
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from dotenv import load_dotenv

load_dotenv()

def main():
    print("💸 TRANSFER CORE FROM OTHER WALLET")
    print(" = " * 50)
    
    # Connect to Core Testnet
    rpc_url  =  "https://rpc.test.btcs.network"
    web3  =  Web3(Web3.HTTPProvider(rpc_url))
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer = 0)
    
    # Input source wallet private key
    source_private_key  =  input("�� Enter source wallet private key (with 0x): ").strip()
    
    if not source_private_key.startswith('0x'):
        source_private_key  =  '0x' + source_private_key
    
    try:
        source_account  =  web3.eth.account.from_key(source_private_key)
        print(f"📱 Source Address: {source_account.address}")
        
        # Check source balance
        source_balance  =  web3.eth.get_balance(source_account.address)
        source_balance_eth  =  web3.from_wei(source_balance, 'ether')
        print(f"💰 Source Balance: {source_balance_eth} CORE")
        
        if source_balance_eth < 0.1:
            print("❌ Source wallet has insufficient balance!")
            return
        
        # Destination (main deployer account)
        destination  =  "0x16102CA8BEF74fb6214AF352989b664BF0e50498"
        print(f"🎯 Destination: {destination}")
        
        # Check destination balance before
        dest_balance_before  =  web3.from_wei(web3.eth.get_balance(destination), 'ether')
        print(f"💰 Destination Balance Before: {dest_balance_before} CORE")
        
        # Calculate amount to send (leave 0.01 for gas):
        amount_to_send  =  source_balance_eth - 0.01
        amount_wei  =  web3.to_wei(str(amount_to_send), 'ether')
        
        print(f"\n💸 Sending {amount_to_send} CORE...")
        
        # Build transaction
        tx  =  {
            'to': destination,
            'value': amount_wei,
            'gas': 21000,
            'gasPrice': web3.to_wei('20', 'gwei'),
            'nonce': web3.eth.get_transaction_count(source_account.address)
        }
        
        # Sign and send
        signed_tx  =  source_account.sign_transaction(tx)
        raw_tx  =  getattr(signed_tx, 'rawTransaction', getattr(signed_tx, 'raw_transaction', None))
        tx_hash  =  web3.eth.send_raw_transaction(raw_tx)
        
        print(f"📤 TX Hash: {tx_hash.hex()}")
        
        # Wait for confirmation:
        receipt  =  web3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Transfer confirmed! Gas used: {receipt['gasUsed']}")
        
        # Check final balances
        dest_balance_after  =  web3.from_wei(web3.eth.get_balance(destination), 'ether')
        print(f"💰 Destination Balance After: {dest_balance_after} CORE")
        print(f"📈 Gained: {dest_balance_after - dest_balance_before} CORE")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
