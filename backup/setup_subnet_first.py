#!/usr/bin/env python3

import os
import sys
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import json
from dotenv import load_dotenv

load_dotenv()


def main():
    print("🚀 SETUP SUBNET 0 BEFORE REGISTRATION")
    print(" = " * 50)

    # Connect to Core Testnet
    rpc_url  =  "https://rpc.test.btcs.network"
    web3  =  Web3(Web3.HTTPProvider(rpc_url))
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer = 0)

    contract_address  =  os.getenv("CORE_CONTRACT_ADDRESS")

    # Load contract ABI
    abi_path  =  "../moderntensor_aptos/mt_core/smartcontract/artifacts/contracts/ModernTensor.sol/ModernTensor.json"
    with open(abi_path, "r") as f:
        contract_data  =  json.load(f)
        contract_abi  =  contract_data["abi"]

    contract = web3.eth.contract(address=contract_address, abi = contract_abi)

    # Use deployer account (Miner 2 who deployed the contract)
    deployer_key  =  "0x3ace434e2cd05cd0e614eb5d423cf04e4b925c17db9869e9c598851f88f52840"
    deployer_account  =  web3.eth.account.from_key(deployer_key)

    print(f"🔧 Deployer: {deployer_account.address}")

    try:
        # Create subnet 0 first
        print("\n🌐 Creating Subnet 0...")

        tx_data  =  contract.functions.createSubnet
            web3.to_wei(0.05, "ether"),  # minStakeMiner
            web3.to_wei(0.08, "ether"),  # minStakeValidator
        ).build_transaction
                "gasPrice": web3.to_wei(30, "gwei"),
                "nonce": web3.eth.get_transaction_count(deployer_account.address),
            }
        )

        # Sign and send
        signed_tx  =  web3.eth.account.sign_transaction(tx_data, deployer_key)
        raw_tx  =  getattr
            signed_tx, "rawTransaction", getattr(signed_tx, "raw_transaction", None)
        )
        tx_hash  =  web3.eth.send_raw_transaction(raw_tx)

        print(f"📤 Subnet creation tx: {tx_hash.hex()}")
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout = 60)

        if receipt.status == 1:
            print("✅ Subnet 0 created successfully!")
        else:
            print("❌ Subnet creation failed")
            return

    except Exception as e:
        print(f"⚠️ Subnet creation error (might already exist): {e}")

        # Check subnet info using available functions
    try:
        print(f"\n📊 Subnet 0 Info:")
        miners  =  contract.functions.getSubnetMiners(0).call()
        validators  =  contract.functions.getSubnetValidators(0).call()

        print(f"   Current Miners: {len(miners)}")
        print(f"   Current Validators: {len(validators)}")
        print(f"   Subnet ready for registration!"):

    except Exception as e:
        print(f"❌ Error getting subnet info: {e}")


if __name__ == "__main__":
    main()
