# File: scripts/prepare_testnet_datums.py
# Chuẩn bị và gửi các Datum ban đầu cho Miners và Validators lên Cardano Testnet.
# Sử dụng một giao dịch duy nhất để tạo nhiều UTXO tại địa chỉ script.

import os
import sys
import logging
import asyncio
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Tuple, List, Type, Dict, Any, cast
from rich.logging import RichHandler

from pycardano import (
    TransactionBuilder,
    TransactionOutput,
    Address,
    ScriptHash,
    PlutusData,
    BlockFrostChainContext,
    Network,
    TransactionId,
    ExtendedSigningKey,
    UTxO,
    Value,
    Asset,
    MultiAsset
)

# --- Thêm đường dẫn gốc của project vào sys.path ---
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
# -------------------------------------------------

# Import các thành phần cần thiết từ SDK Moderntensor
try:
    from sdk.metagraph.create_utxo import find_suitable_ada_input
    from sdk.metagraph.metagraph_datum import MinerDatum, ValidatorDatum, STATUS_ACTIVE, METAGRAPH_NFT_POLICY_ID_PLACEHOLDER, METAGRAPH_NFT_ASSET_NAME_PLACEHOLDER, MetagraphDatum, MinerInfo, ValidatorInfo
    from sdk.metagraph.hash.hash_datum import hash_data
    from sdk.service.context import get_chain_context
    from sdk.keymanager.decryption_utils import decode_hotkey_skey
    from sdk.smartcontract.validator import read_validator
    from sdk.config.settings import settings as sdk_settings
    from sdk.service.blockfrost_service import BlockFrostService
    from sdk.service.transaction_service import TransactionService
except ImportError as e:
    print(f"❌ FATAL: Import Error in prepare_testnet_datums.py: {e}")
    sys.exit(1)

# --- Tải biến môi trường ---
env_path = project_root / '.env'

# --- Cấu hình Logging với RichHandler ---
log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)

rich_handler = RichHandler(
    show_time=True,
    show_level=True,
    show_path=False,
    markup=True,
    rich_tracebacks=True,
    log_time_format="[%Y-%m-%d %H:%M:%S]"
)

logging.basicConfig(
    level=log_level,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[rich_handler]
)

logger = logging.getLogger(__name__)
# ------------------------

# --- Tải biến môi trường (sau khi logger được cấu hình) ---
if env_path.exists():
    logger.info(f"📄 Loading environment variables from: {env_path}")
    load_dotenv(dotenv_path=env_path, override=True)
else:
    logger.warning(f"📄 Environment file (.env) not found at {env_path}.")
# --------------------------

# --- Lấy thông tin Miner và Validator từ .env ---
# Sử dụng ID dạng String để tạo Datum, UID hex sẽ được suy ra khi chạy node
MINER_UID_STR = os.getenv("SUBNET1_MINER_ID") # Ví dụ: "my_cool_image_miner_01"
MINER_WALLET_ADDR = os.getenv("SUBNET1_MINER_WALLET_ADDR")
MINER_API_ENDPOINT = os.getenv("SUBNET1_MINER_API_ENDPOINT")

MINER_UID_STR2 = os.getenv("SUBNET1_MINER_ID2") # Ví dụ: "my_cool_image_miner_02"
MINER_WALLET_ADDR2 = os.getenv("SUBNET1_MINER_WALLET_ADDR2")
MINER_API_ENDPOINT2 = os.getenv("SUBNET1_MINER_API_ENDPOINT2")

VALIDATOR_UID_STR = os.getenv("SUBNET1_VALIDATOR_UID") # Ví dụ: "validator_001"
VALIDATOR_WALLET_ADDR = os.getenv("SUBNET1_VALIDATOR_ADDRESS")
VALIDATOR_API_ENDPOINT = os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT")

VALIDATOR_UID_STR2 = os.getenv("SUBNET1_VALIDATOR_UID2")
VALIDATOR_WALLET_ADDR2 = os.getenv("SUBNET1_VALIDATOR_ADDRESS2")
VALIDATOR_API_ENDPOINT2 = os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT2")

VALIDATOR_UID_STR3 = os.getenv("SUBNET1_VALIDATOR_UID3")
VALIDATOR_WALLET_ADDR3 = os.getenv("SUBNET1_VALIDATOR_ADDRESS3")
VALIDATOR_API_ENDPOINT3 = os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT3")

# --- Lấy cấu hình ví Funding ---
FUNDING_COLDKEY_NAME = os.getenv("FUNDING_COLDKEY_NAME", "kickoff")
FUNDING_HOTKEY_NAME = os.getenv("FUNDING_HOTKEY_NAME", "hk1")
FUNDING_PASSWORD = os.getenv("FUNDING_PASSWORD") # Bỏ mặc định, yêu cầu đặt trong .env
HOTKEY_BASE_DIR = os.getenv("HOTKEY_BASE_DIR", getattr(sdk_settings, 'HOTKEY_BASE_DIR', 'moderntensor'))

DATUM_LOCK_AMOUNT = 2_000_000 # 2 ADA mỗi UTXO Datum

# --- Kiểm tra các biến môi trường bắt buộc ---
required_env_vars = {
    "SUBNET1_MINER_ID": MINER_UID_STR, "SUBNET1_MINER_WALLET_ADDR": MINER_WALLET_ADDR, "SUBNET1_MINER_API_ENDPOINT": MINER_API_ENDPOINT,
    "SUBNET1_MINER_ID2": MINER_UID_STR2, "SUBNET1_MINER_WALLET_ADDR2": MINER_WALLET_ADDR2, "SUBNET1_MINER_API_ENDPOINT2": MINER_API_ENDPOINT2,
    "SUBNET1_VALIDATOR_UID": VALIDATOR_UID_STR, "SUBNET1_VALIDATOR_ADDRESS": VALIDATOR_WALLET_ADDR, "SUBNET1_VALIDATOR_API_ENDPOINT": VALIDATOR_API_ENDPOINT,
    "SUBNET1_VALIDATOR_UID2": VALIDATOR_UID_STR2, "SUBNET1_VALIDATOR_ADDRESS2": VALIDATOR_WALLET_ADDR2, "SUBNET1_VALIDATOR_API_ENDPOINT2": VALIDATOR_API_ENDPOINT2,
    "SUBNET1_VALIDATOR_UID3": VALIDATOR_UID_STR3, "SUBNET1_VALIDATOR_ADDRESS3": VALIDATOR_WALLET_ADDR3, "SUBNET1_VALIDATOR_API_ENDPOINT3": VALIDATOR_API_ENDPOINT3,
    "FUNDING_PASSWORD": FUNDING_PASSWORD,
    "BLOCKFROST_PROJECT_ID": getattr(sdk_settings,'BLOCKFROST_PROJECT_ID', None) # Kiểm tra cả blockfrost ID
}
missing_vars = [k for k, v in required_env_vars.items() if not v]
if missing_vars:
    logger.error(f"FATAL: Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)
# --------------------------------------------------

# === Constants (Placeholders - Replace with actual values) ===
# These should ideally come from a config file or constants module
# Replace with your ACTUAL deployed script address
METAGRAPH_SCRIPT_ADDRESS_BECH32 = os.getenv("METAGRAPH_SCRIPT_ADDRESS") or "addr_test1w...your_script_address..."
# Replace with your ACTUAL Metagraph NFT Policy ID and Asset Name (hex)
METAGRAPH_NFT_POLICY_ID = os.getenv("METAGRAPH_NFT_POLICY_ID") or METAGRAPH_NFT_POLICY_ID_PLACEHOLDER
METAGRAPH_NFT_ASSET_NAME = os.getenv("METAGRAPH_NFT_ASSET_NAME") or METAGRAPH_NFT_ASSET_NAME_PLACEHOLDER

# === Helper Functions ===

def load_funding_keys(
    base_dir: str,
    coldkey_name: str,
    hotkey_name: str,
    password: str
) -> Tuple[ExtendedSigningKey, Address]:
    """Loads funding keys and derives the address."""
    logger.info(f"🔑 Loading funding keys (Cold: '{coldkey_name}', Hot: '{hotkey_name}')...")
    try:
        payment_esk, _ = decode_hotkey_skey(base_dir, coldkey_name, hotkey_name, password)
        payment_vk = payment_esk.to_verification_key()
        funding_address = Address(payment_vk.hash(), network=get_network())
        logger.info(f"✅ Funding keys loaded. Address: [cyan]{funding_address}[/]")
        return payment_esk, funding_address
    except Exception as e:
        logger.exception(f"💥 Failed to load funding keys: {e}")
        raise

def get_network() -> Network:
    """Determines the Cardano network from environment or SDK settings."""
    network_str = (os.getenv("CARDANO_NETWORK") or getattr(sdk_settings, 'CARDANO_NETWORK', 'TESTNET')).upper()
    return Network.MAINNET if network_str == "MAINNET" else Network.TESTNET

def create_metagraph_datum(
    validators: List[ValidatorInfo],
    miners: List[MinerInfo],
    current_cycle: int = 0 # Initial cycle
) -> MetagraphDatum:
    """Creates the MetagraphDatum object."""
    logger.info(f"🧩 Creating Metagraph Datum (Cycle: {current_cycle})...")
    datum = MetagraphDatum(
        validators=validators,
        miners=miners,
        last_update_cycle=current_cycle
    )
    logger.info(f"✅ Metagraph Datum created with {len(validators)} validators and {len(miners)} miners.")
    return datum

def build_and_submit_transaction(
    tx_service: TransactionService,
    funding_address: Address,
    funding_skey: ExtendedSigningKey,
    script_address: Address,
    metagraph_datum: MetagraphDatum,
    nft_policy_id: str,
    nft_asset_name: str,
    min_utxo_lovelace: int
) -> str:
    """Builds, signs, and submits the transaction to create the initial datum UTXO."""
    logger.info("🏗️ Building transaction to create initial Metagraph UTXO...")
    try:
        # 1. Define the output to the script address
        nft_asset = Asset.from_primitive({bytes.fromhex(nft_policy_id): {bytes.fromhex(nft_asset_name): 1}})
        output_value = Value(min_utxo_lovelace, MultiAsset({nft_asset.policy: nft_asset.assets}))
        script_output = TransactionOutput(script_address, output_value, datum=metagraph_datum, datum_hash=metagraph_datum.hash())
        logger.info(f"   ➡️ Output to Script: {script_address}")
        logger.info(f"   💰 Value: {min_utxo_lovelace} Lovelace + 1 Metagraph NFT")
        logger.info(f"   📄 Datum Hash: {metagraph_datum.hash().hex()}")

        # 2. Build the transaction (TxService handles finding inputs, change, fees)
        tx_builder = tx_service.create_transaction_builder(funding_address)
        tx_builder.add_output(script_output)

        # Explicitly add the funding key as a required signer (might be handled by TxService)
        # tx_builder.required_signers = [funding_skey.to_verification_key().hash()]

        logger.info("✍️ Signing transaction...")
        signed_tx = tx_service.sign_transaction(tx_builder, [funding_skey])

        logger.info("📤 Submitting transaction...")
        tx_hash = tx_service.submit_transaction(signed_tx)
        logger.info(f"✅ Transaction submitted successfully! Tx Hash: [bold green]{tx_hash}[/]")
        logger.info(f"   View on Cardanoscan ({get_network().name}): [link=https://{get_network().name.lower()}.cardanoscan.io/transaction/{tx_hash}]https://{get_network().name.lower()}.cardanoscan.io/transaction/{tx_hash}[/link]")
        return tx_hash

    except Exception as e:
        logger.exception(f"💥 Failed during transaction build/sign/submit: {e}")
        raise

# === Main Execution Logic ===

def main():
    """Main function to prepare the initial Metagraph Datum UTXO."""
    logger.info("✨ --- Starting Metagraph Datum Preparation Script --- ✨")

    # --- Load Configuration --- 
    logger.info("⚙️ Loading configuration from .env...")
    try:
        network = get_network()
        blockfrost_project_id = os.getenv("BLOCKFROST_PROJECT_ID") or getattr(sdk_settings, 'BLOCKFROST_PROJECT_ID', None)
        hotkey_base_dir = os.getenv("HOTKEY_BASE_DIR") or getattr(sdk_settings, 'HOTKEY_BASE_DIR', 'moderntensor')
        funding_coldkey = os.getenv("FUNDING_COLDKEY_NAME")
        funding_hotkey = os.getenv("FUNDING_HOTKEY_NAME")
        funding_password = os.getenv("FUNDING_PASSWORD")

        if not all([blockfrost_project_id, funding_coldkey, funding_hotkey, funding_password]):
            missing = [k for k,v in {"BLOCKFROST_PROJECT_ID": blockfrost_project_id,
                                      "FUNDING_COLDKEY_NAME": funding_coldkey,
                                      "FUNDING_HOTKEY_NAME": funding_hotkey,
                                      "FUNDING_PASSWORD": funding_password}.items() if not v]
            logger.critical(f"❌ FATAL: Missing required funding configurations in .env: {missing}")
            sys.exit(1)

        script_address = Address.from_primitive(METAGRAPH_SCRIPT_ADDRESS_BECH32)
        logger.info(f"🎯 Target Script Address: [magenta]{script_address}[/]")
        logger.info(f"    NFT Policy ID: [yellow]{METAGRAPH_NFT_POLICY_ID}[/]")
        logger.info(f"    NFT Asset Name: [yellow]{METAGRAPH_NFT_ASSET_NAME}[/]")

    except Exception as cfg_err:
        logger.exception(f"💥 Error loading configuration: {cfg_err}")
        sys.exit(1)

    # --- Initialize Services --- 
    try:
        logger.info(f"🔗 Initializing BlockFrostService (Network: {network.name})...")
        bf_service = BlockFrostService(project_id=blockfrost_project_id, network=network)
        logger.info("🔗 Initializing TransactionService...")
        tx_service = TransactionService(blockfrost_service=bf_service)
        min_utxo = bf_service.fetch_protocol_parameters()["minUTxOValue"]
        logger.info(f"💰 Minimum UTXO Value (Lovelace): {min_utxo}")
    except Exception as svc_err:
        logger.exception(f"💥 Error initializing services: {svc_err}")
        sys.exit(1)

    # --- Load Funding Wallet --- 
    try:
        funding_skey, funding_address = load_funding_keys(
            hotkey_base_dir, funding_coldkey, funding_hotkey, funding_password # type: ignore
        )
        # Check balance (optional but recommended)
        balance = bf_service.get_address_balance(str(funding_address))
        logger.info(f"💰 Funding Wallet Balance: {balance / 1_000_000} ADA")
        if balance < min_utxo * 2: # Need minUTXO + fees + buffer
             logger.warning(f"⚠️ Funding wallet balance might be too low! Required ~ {min_utxo * 2 / 1_000_000} ADA.")

    except Exception as fund_err:
        logger.exception(f"💥 Error loading funding wallet: {fund_err}")
        sys.exit(1)

    # --- Define Initial Validators and Miners --- 
    # Load these from .env or a separate config file
    logger.info("👥 Defining initial validator and miner list...")
    validators = []
    miners = []
    # Example: Load Validator 1 info
    try:
        val1_uid = os.getenv("SUBNET1_VALIDATOR_UID")
        val1_addr = os.getenv("SUBNET1_VALIDATOR_ADDRESS")
        val1_api = os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT")
        if val1_uid and val1_addr and val1_api:
            validators.append(ValidatorInfo(uid=val1_uid.encode().hex(), address=val1_addr, api_endpoint=val1_api, status=STATUS_ACTIVE))
            logger.info(f"  ➕ Added Validator 1: UID={val1_uid.encode().hex()[:10]}... Addr={val1_addr[:15]}... API={val1_api}")
        else: logger.warning("⚠️ Validator 1 info missing in .env, skipping.")
        # Add similar logic for Validator 2, 3...
        # ... (Load Val 2, Val 3)

        # Example: Load Miner 1 info
        miner1_uid = os.getenv("SUBNET1_MINER_ID")
        miner1_addr = os.getenv("SUBNET1_MINER_WALLET_ADDR")
        miner1_api = os.getenv("SUBNET1_MINER_API_ENDPOINT")
        if miner1_uid and miner1_addr and miner1_api:
             miners.append(MinerInfo(uid=miner1_uid.encode().hex(), address=miner1_addr, api_endpoint=miner1_api, status=STATUS_ACTIVE))
             logger.info(f"  ➕ Added Miner 1: UID={miner1_uid.encode().hex()[:10]}... Addr={miner1_addr[:15]}... API={miner1_api}")
        else: logger.warning("⚠️ Miner 1 info missing in .env, skipping.")
        # Add similar logic for Miner 2...
        # ... (Load Miner 2)

        if not validators and not miners:
            logger.critical("❌ FATAL: No validators or miners could be loaded from .env configuration. Cannot create datum.")
            sys.exit(1)

    except Exception as list_err:
         logger.exception(f"💥 Error loading validator/miner lists: {list_err}")
         sys.exit(1)

    # --- Create Datum & Build/Submit TX --- 
    try:
        metagraph_datum = create_metagraph_datum(validators, miners)
        build_and_submit_transaction(
            tx_service,
            funding_address,
            funding_skey,
            script_address,
            metagraph_datum,
            METAGRAPH_NFT_POLICY_ID,
            METAGRAPH_NFT_ASSET_NAME,
            min_utxo
        )
        logger.info("✅🏁 Metagraph datum preparation script finished successfully! 🏁✅")

    except Exception as final_err:
        logger.exception(f"💥 Final error during datum creation or transaction submission: {final_err}")
        sys.exit(1)

# --- Run Main --- 
if __name__ == "__main__":
    main()