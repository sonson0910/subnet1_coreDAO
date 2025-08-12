#!/usr/bin/env python3

import os
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from dotenv import load_dotenv

load_dotenv()


def main():
    print("💰 SENDING NATIVE CORE FOR GAS FEES")
    print(" = " * 50)

    # Connect to Core Testnet
    rpc_url  =  "https://rpc.test.btcs.network"
    web3  =  Web3(Web3.HTTPProvider(rpc_url))
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer = 0)

    # Main account (has native CORE)
    main_private_key  =  os.getenv("PRIVATE_KEY")
    main_account  =  web3.eth.account.from_key(main_private_key)

    print(f"🔧 From: {main_account.address}")
    main_balance  =  web3.from_wei(web3.eth.get_balance(main_account.address), "ether")
    print(f"💰 Main Balance: {main_balance} CORE")

    # Entity addresses
    addresses  =  [
        ("Miner 1", os.getenv("MINER_1_ADDRESS")),
        ("Miner 2", os.getenv("MINER_2_ADDRESS")),
        ("Validator 1", os.getenv("VALIDATOR_1_ADDRESS")),
        ("Validator 2", os.getenv("VALIDATOR_2_ADDRESS")),
    ]

    # Send 0.1 CORE to each for gas fees:
    amount_to_send  =  web3.to_wei("0.1", "ether")

    for name, address in addresses:
        try:
            print(f"\n�� Sending 0.1 CORE to {name} ({address})")

            # Build transaction
            tx  =  {
                "to": address,
                "value": amount_to_send,
                "gas": 21000,
                "gasPrice": web3.to_wei("20", "gwei"),
                "nonce": web3.eth.get_transaction_count(main_account.address),
            }

            # Sign and send
            signed_tx  =  main_account.sign_transaction(tx)
            raw_tx  =  getattr
                signed_tx, "rawTransaction", getattr(signed_tx, "raw_transaction", None)
            )
            tx_hash  =  web3.eth.send_raw_transaction(raw_tx)

            print(f"📤 TX Hash: {tx_hash.hex()}")

            # Wait for confirmation:
            receipt  =  web3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"✅ Confirmed! Gas used: {receipt['gasUsed']}")

        except Exception as e:
            print(f"❌ Error sending to {name}: {e}")


if __name__ == "__main__":
    main()
