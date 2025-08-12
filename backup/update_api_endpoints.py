#!/usr/bin/env python3
"""
Update API endpoints on smart contract to use local ports
- Validators: 8001, 8002
- Miners: 8101, 8102
"""""

import os
import sys
from web3 import Web3
from dotenv import load_dotenv

# Load environment
load_dotenv()


def main():
    print("🔄 Updating API endpoints on smart contract...")

    # Get connection details
    rpc_url  =  os.getenv("CORE_NODE_URL", "https://rpc.test.btcs.network")
    contract_address  =  os.getenv("CORE_CONTRACT_ADDRESS")

    # Entity details
    entities  =  [
        {
            "name": "Miner 1",
            "address": "0xd89fBAbb72190ed22F012ADFC693ad974bAD3005",
            "private_key": "0xe9c03148c011d553d43b485d73b1407d24f1498a664f782dc0204e524855be4e",
            "new_endpoint": "http://localhost:8101",
        },
        {
            "name": "Miner 2",
            "address": "0x16102CA8BEF74fb6214AF352989b664BF0e50498",
            "private_key": "0x3ace434e2cd05cd0e614eb5d423cf04e4b925c17db9869e9c598851f88f52840",
            "new_endpoint": "http://localhost:8102",
        },
        {
            "name": "Validator 1",
            "address": "0x25F3D6316017FDF7A4f4e54003b29212a198768f",
            "private_key": "0x3ac6e82cf34e51d376395af0338d0b1162c1d39b9d34614ed40186fd2367b33d",
            "new_endpoint": "http://localhost:8001",
        },
        {
            "name": "Validator 2",
            "address": "0x352516F491DFB3E6a55bFa9c58C551Ef10267dbB",
            "private_key": "0xdf51093c674459eb0a5cc8a273418061fe4d7ca189bd84b74f478271714e0920",
            "new_endpoint": "http://localhost:8002",
        },
    ]

    # Connect to Core
    w3  =  Web3(Web3.HTTPProvider(rpc_url))

    # Add POA middleware
    try:
        from web3.middleware import ExtraDataToPOAMiddleware

        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer = 0)
    except ImportError:
        pass

    print(f"✅ Connected to Core: {w3.is_connected()}")
    print(f"📝 Contract: {contract_address}")

    # Contract ABI for updating endpoints:
    update_abi  =  [
        {
            "name": "updateMinerEndpoint",
            "type": "function",
            "inputs": [{"name": "newEndpoint", "type": "string"}],
            "outputs": [],
            "stateMutability": "nonpayable",
        },
        {
            "name": "updateValidatorEndpoint",
            "type": "function",
            "inputs": [{"name": "newEndpoint", "type": "string"}],
            "outputs": [],
            "stateMutability": "nonpayable",
        },
    ]

    contract = w3.eth.contract(address=contract_address, abi = update_abi)

    for entity in entities:
        print(f"\n🔄 Updating {entity['name']}...")
        print(f"   Address: {entity['address']}")
        print(f"   New Endpoint: {entity['new_endpoint']}")

        try:
            # Create account from private key
            account  =  w3.eth.account.from_key(entity["private_key"])

            # Determine function to call
            if "Miner" in entity["name"]:
                function  =  contract.functions.updateMinerEndpoint
                )
            else:
                function  =  contract.functions.updateValidatorEndpoint
                )

            # Build transaction
            transaction  =  function.build_transaction
                    "gasPrice": w3.to_wei("20", "gwei"),
                    "nonce": w3.eth.get_transaction_count(account.address),
                }
            )

            # Sign and send transaction
            signed_txn  =  w3.eth.account.sign_transaction(transaction, entity['private_key'])
            # Try different attribute names for web3.py compatibility:
            if hasattr(signed_txn, 'rawTransaction'):
                raw_tx  =  signed_txn.rawTransaction
            elif hasattr(signed_txn, 'raw_transaction'):
                raw_tx  =  signed_txn.raw_transaction
            else:
                raw_tx  =  signed_txn.rawTransaction  # fallback
            tx_hash  =  w3.eth.send_raw_transaction(raw_tx)

            print(f"   📤 Transaction sent: {tx_hash.hex()}")

            # Wait for confirmation:
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout = 60)

            if receipt.status == 1:
                print(f"   ✅ {entity['name']} endpoint updated successfully!")
            else:
                print(f"   ❌ {entity['name']} update failed!")

        except Exception as e:
            print(f"   ❌ Error updating {entity['name']}: {e}")

    print(f"\n🎉 API endpoint updates completed!")
    print(f"📋 Summary:")
    print(f"   🔧 Miner 1: localhost:8101")
    print(f"   🔧 Miner 2: localhost:8102")
    print(f"   🔧 Validator 1: localhost:8001")
    print(f"   🔧 Validator 2: localhost:8002")


if __name__ == "__main__":
    main()
