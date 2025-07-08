# subnet1/create_initial_state.py
"""
Script to create the initial state UTxO for Subnet 1.

This script generates the TransactionOutput object containing the initial
SubnetStaticDatum locked by the subnet's specific script (e.g., an "always true"
script or a governance script).

This output object then needs to be included in a transaction funded
by a wallet to actually place the UTxO on the blockchain.
"""
from dataclasses import dataclass
import json
import logging
import os
from typing import Optional
from pycardano import (
    TransactionOutput,
    Address,
    Value,
    PlutusV3Script,
    plutus_script_hash,
    Network,
    PlutusData,
)

# --- Import Datum definitions from SDK --- 
try:
    # Import both, although we might only use one for initial state
    from moderntensor_aptos.mt_core.metagraph.metagraph_datum import SubnetStaticDatum, SubnetDynamicDatum
except ImportError:
    print("Error: Could not import SubnetStaticDatum/SubnetDynamicDatum from moderntensor_aptos.mt_core.metagraph.metagraph_datum")
    print("Please ensure the sdk is installed and accessible.")
    # Define placeholders if necessary for the script to potentially run partially
    # Note: This is less useful if the core logic depends heavily on the real datum structure.
    @dataclass
    class SubnetStaticDatum(PlutusData):
        CONSTR_ID = 0
        net_uid: int = 0
        name: bytes = b''
        owner_addr_hash: bytes = b''
        max_miners: int = 0
        max_validators: int = 0
        immunity_period_slots: int = 0
        creation_slot: int = 0
        description: bytes = b''
        version: int = 0
        min_stake_miner: int = 0
        min_stake_validator: int = 0

# Try importing the new function first
try:
    from moderntensor_aptos.mt_core.smartcontract.validator import read_validator_subnet
except ImportError:
    print("Warning: Could not import read_validator_subnet from moderntensor_aptos.mt_core.smartcontract.validator")
    print("Falling back to local script reading.")
    read_validator_subnet = None # Define as None to handle fallback

logger = logging.getLogger(__name__)

# Default minimum ADA for a UTxO (adjust if needed)
DEFAULT_SUBNET_UTXO_LOVELACE = 2000000 # 2 ADA

# --- Helper Functions --- 

def read_script_from_json(file_path: str) -> Optional[PlutusV3Script]:
    """Reads Plutus V3 script CBOR hex from a JSON file."""
    if not os.path.exists(file_path):
        logger.error(f"Script file not found: {file_path}")
        return None
    try:
        with open(file_path, 'r') as f:
            script_data = json.load(f)
        # Common keys used by different tools - adjust if your JSON is different
        cbor_hex = script_data.get("cborHex") or script_data.get("script")
        if not cbor_hex:
            logger.error(f"Could not find 'cborHex' or 'script' key in {file_path}")
            return None
        script_bytes = bytes.fromhex(cbor_hex)
        return PlutusV3Script(script_bytes)
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.error(f"Error reading or decoding script file {file_path}: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error reading script file {file_path}: {e}")
        return None

def create_subnet_state_utxo(
    datum: SubnetStaticDatum, # Expecting SubnetStaticDatum for initial state
    script_file_path: str,
    network: Network,
    amount: int = DEFAULT_SUBNET_UTXO_LOVELACE,
) -> Optional[TransactionOutput]:
    """
    Creates a TransactionOutput (UTxO) locked by the specified Subnet script
    containing the provided SubnetStaticDatum.
    """
    # Check if the provided datum is the correct type
    if not isinstance(datum, SubnetStaticDatum):
        logger.error("Invalid datum provided. Must be an instance of SubnetStaticDatum for initial state.")
        return None

    script = read_script_from_json(script_file_path)
    if not script:
        return None # Error already logged

    script_hash = None
    # Use the imported function if available
    if read_validator_subnet:
        validator_info = read_validator_subnet(script_file_path)
        if validator_info:
            script_hash = validator_info.get("script_hash")
            # script_bytes = validator_info.get("script_bytes") # Not strictly needed here now
        else:
            logger.error(f"Failed to read validator info using read_validator_subnet from {script_file_path}")
            return None # Stop if we intended to use the new function but failed
    else:
        # Fallback to the old method if the new function wasn't imported
        try:
            script_hash = plutus_script_hash(script)
            logger.debug(f"Calculated script hash: {script_hash}")
        except Exception as e:
            logger.error(f"Failed to hash Plutus script from {script_file_path}: {e}")
            return None

    script_address = Address(script_hash=script_hash, network=network)
    logger.info(f"Derived Subnet 1 script address: {script_address}")

    value_to_send = Value(coin=amount)

    try:
        tx_out = TransactionOutput(
            address=script_address,
            amount=value_to_send,
            datum=datum,
        )
        logger.info(f"Created TransactionOutput object for Subnet 1 initial state.")
        logger.debug(f"  Datum: {datum}")
        logger.debug(f"  Value: {value_to_send}")
        return tx_out
    except Exception as e:
        logger.exception(f"Failed to create TransactionOutput: {e}")
        return None

# --- Main execution block --- 
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- CONFIGURE THESE VALUES ---
    # Set target Cardano network (Testnet or Mainnet)
    network = Network.TESTNET

    # Path to the *compiled* Plutus script JSON file for the subnet state
    # This script should be designed to lock/validate the SubnetStaticDatum
    subnet_script_path = "plutus_subnet.json" # <--- CHANGE TO YOUR ACTUAL PATH

    # Set initial values for your Subnet 1 STATIC state
    initial_static_subnet_state = SubnetStaticDatum(
        net_uid=1,                  # Subnet ID
        name=b'ModernTensor Subnet 1', # Subnet Name
        owner_addr_hash=bytes.fromhex('your_owner_address_hash_hex_here'), # <--- CHANGE THIS (Hash of owner's PubKeyHash or ScriptHash)
        max_miners=1024,
        max_validators=64,
        immunity_period_slots=720,  # Example: ~6 hours on mainnet (slots are seconds)
        creation_slot=0,            # Will be set by the chain, but 0 is a placeholder
        description=b'Subnet for decentralized AI model training and inference.',
        version=1,                  # Static Datum structure version
        min_stake_miner=100000000,   # Example: 100 ADA
        min_stake_validator=1000000000 # Example: 1000 ADA
    )

    # --- Optional: Define initial dynamic state if needed elsewhere, but not used for this UTxO --- 
    # initial_dynamic_subnet_state = SubnetDynamicDatum(...)

    # --- END CONFIGURATION ---

    print(f"Attempting to create initial STATIC state UTxO for Subnet {initial_static_subnet_state.net_uid}...")
    print(f"Using script: {subnet_script_path}")
    print(f"Network: {network.name}")
    print(f"Initial Static Datum Values: {initial_static_subnet_state}")

    # Create the TransactionOutput Python object
    subnet_utxo_object = create_subnet_state_utxo(
        datum=initial_static_subnet_state,
        script_file_path=subnet_script_path,
        network=network
    )

    if subnet_utxo_object:
        print("\n" + "="*30)
        print(" SUCCESS: Created Subnet 1 STATIC state UTxO object ")
        print("="*30)
        print(f"  Address: {subnet_utxo_object.address}")
        print(f"  Amount: {subnet_utxo_object.amount}")
        print(f"  Datum: {subnet_utxo_object.datum}")
        # print("\nPrimitive representation:")
        # print(subnet_utxo_object.to_primitive())

        print("\n" + "-"*30)
        print(" NEXT STEPS REQUIRED:")
        print("-"*30)
        print(" 1. Integrate this script or the `create_subnet_state_utxo` function")
        print("    into your transaction building process.")
        print(" 2. Use a wallet (Signing Key + Chain Context like BlockFrost) to:")
        print("    a. Select input UTxOs from the wallet for funding.")
        print("    b. Add this generated `subnet_utxo_object` as an output.")
        print("    c. Add a change output back to the wallet.")
        print("    d. Build, sign, and submit the transaction.")
        print("-"*30)

    else:
        print("\n" + "X"*30)
        print(" FAILURE: Failed to create Subnet 1 STATIC state UTxO object.")
        print("X"*30)
        print(" Please check the logs above for specific errors (e.g., file not found, JSON errors, script hashing errors).") 