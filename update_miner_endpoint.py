#!/usr/bin/env python3
"""
Update miner endpoint in smart contract from 8102 to 8101
"""
import os
import sys
import json
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


def update_miner_endpoint():
    """Update miner endpoint in smart contract"""
    print(f"\n🔄 UPDATING MINER ENDPOINT IN SMART CONTRACT")
    print("=" * 60)

    # Contract details
    contract_address = os.getenv("CORE_CONTRACT_ADDRESS")
    core_token_address = os.getenv("CORE_TOKEN_ADDRESS")
    core_node_url = os.getenv("CORE_NODE_URL")

    print(f"🎯 Contract: {contract_address}")
    print(f"🌐 RPC: {core_node_url}")

    # Miner details
    miner_address = "0x16102CA8BEF74fb6214AF352989b664BF0e50498"
    miner_private_key = os.getenv("MINER_2_PRIVATE_KEY")

    if not miner_private_key:
        print("❌ MINER_2_PRIVATE_KEY not found in .env")
        return False

    if not miner_private_key.startswith("0x"):
        miner_private_key = "0x" + miner_private_key

    print(f"🤖 Miner: {miner_address}")
    print(f"🔄 Updating endpoint: 8102 → 8101")

    # Setup Web3
    web3 = Web3(Web3.HTTPProvider(core_node_url))
    if not web3.is_connected():
        print("❌ Cannot connect to Core network")
        return False

    # Load contract ABI (simplified)
    contract_abi = json.loads(
        """[
        {
            "inputs": [
                {"internalType": "string", "name": "newEndpoint", "type": "string"}
            ],
            "name": "updateMinerEndpoint",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]"""
    )

    contract = web3.eth.contract(address=contract_address, abi=contract_abi)
    account = web3.eth.account.from_key(miner_private_key)

    try:
        # Update miner endpoint
        print("📝 Updating miner endpoint...")

        tx_data = contract.functions.updateMinerEndpoint(
            "http://localhost:8101"  # NEW CORRECT ENDPOINT
        ).build_transaction(
            {
                "from": account.address,
                "gas": 200000,
                "gasPrice": web3.to_wei("20", "gwei"),
                "nonce": web3.eth.get_transaction_count(account.address),
            }
        )

        # Sign and send transaction
        signed_tx = web3.eth.account.sign_transaction(tx_data, miner_private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print(f"📡 Transaction sent: {tx_hash.hex()}")

        # Wait for confirmation
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        if receipt.status == 1:
            print(f"✅ Miner endpoint updated successfully!")
            print(f"🎯 New endpoint: http://localhost:8101")
            return True
        else:
            print(f"❌ Transaction failed")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = update_miner_endpoint()
    if success:
        print(f"\n🎉 SUCCESS! Miner endpoint updated to 8101")
        print(f"✅ Validator can now connect to miner properly")
    else:
        print(f"\n❌ FAILED to update miner endpoint")
