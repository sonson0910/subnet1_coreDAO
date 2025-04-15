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
from typing import Optional, Tuple, List, Type, Dict # Thêm Dict

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
    Value, # Thêm Value
)

# --- Thêm đường dẫn gốc của project vào sys.path ---
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
# -------------------------------------------------

# Import các thành phần cần thiết từ SDK Moderntensor
try:
    from sdk.metagraph.create_utxo import find_suitable_ada_input # Chỉ cần hàm tìm input
    from sdk.metagraph.metagraph_datum import MinerDatum, ValidatorDatum, STATUS_ACTIVE
    from sdk.metagraph.hash.hash_datum import hash_data
    from sdk.service.context import get_chain_context
    from sdk.keymanager.decryption_utils import decode_hotkey_skey
    from sdk.smartcontract.validator import read_validator
    from sdk.config.settings import settings as sdk_settings # Import settings của SDK
except ImportError as e:
    print(f"Error: Could not import required components from the 'moderntensor' SDK. "
          f"Is the SDK installed correctly? Details: {e}")
    sys.exit(1)

# --- Tải biến môi trường ---
env_path = project_root / '.env'
if env_path.exists():
    print(f"Loading environment variables from: {env_path}")
    load_dotenv(dotenv_path=env_path, override=True)
else:
    print(f"Warning: .env file not found at {env_path}. Using default values or existing environment variables.")
# -----------------------------

# --- Cấu hình Logging ---
log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(level=log_level, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)
DEFAULT_MIN_UTXO_FETCH_ADA = 5_000_000 # Lovelace tối thiểu cho UTXO funding
# ------------------------

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

# --- Hàm tạo Datum Helper ---
def create_and_log_datum(
    datum_type: Type[PlutusData], # <<<--- Sửa type hint
    uid_str: str,
    wallet_addr: str,
    api_endpoint: Optional[str], # <<<--- Cho phép None
    divisor: float,
    subnet_id: int = 1,
    initial_perf: float = 0.5,
    initial_trust: float = 0.5,
    initial_stake: int = 0
) -> Tuple[PlutusData, str]: # <<<--- Sửa kiểu trả về
    """Tạo đối tượng Datum (Miner hoặc Validator) và in ra UID hex tương ứng."""
    # >>> Quan trọng: Tính UID bytes và hex từ uid_str <<<
    try:
        uid_bytes = uid_str.encode('utf-8')
        uid_hex = uid_bytes.hex()
    except Exception as e:
        logger.error(f"Failed to encode UID string '{uid_str}': {e}")
        raise ValueError(f"Invalid UID string: {uid_str}") from e

    logger.info(f"Preparing Datum for String UID: '{uid_str}' -> HEX UID: {uid_hex}")

    # Hash địa chỉ ví (phải là string hợp lệ)
    try:
        wallet_hash_bytes = hash_data(wallet_addr)
    except Exception as e:
        logger.error(f"Failed to hash wallet address '{wallet_addr}': {e}")
        raise ValueError(f"Invalid wallet address: {wallet_addr}") from e

    # Encode API endpoint (nếu có)
    api_bytes: Optional[bytes] = None # <<<--- Khởi tạo là None
    if api_endpoint:
        try:
            api_bytes = api_endpoint.encode('utf-8')
        except Exception as e:
            logger.warning(f"Could not encode API endpoint '{api_endpoint}': {e}. Storing as empty bytes.")
            api_bytes = b'' # Hoặc None tùy theo định nghĩa datum
    # Nếu api_endpoint là None hoặc rỗng, api_bytes sẽ là None hoặc b''

    # Kiểm tra divisor
    if divisor <= 0:
         raise ValueError("DATUM_INT_DIVISOR must be positive.")

    # Các tham số chung cho Datum
    common_args = {
        "uid": uid_bytes,
        "subnet_uid": subnet_id,
        "stake": initial_stake,
        "scaled_last_performance": int(initial_perf * divisor),
        "scaled_trust_score": int(initial_trust * divisor),
        "accumulated_rewards": 0,
        "last_update_slot": 0,
        "performance_history_hash": hash_data([]), # Hash của list rỗng
        "wallet_addr_hash": wallet_hash_bytes,
        "status": STATUS_ACTIVE,
        "registration_slot": 0,
        "api_endpoint": api_bytes if api_bytes is not None else b'', # Đảm bảo là bytes, không phải None
    }

    # Tạo đối tượng Datum cụ thể
    datum_instance: PlutusData
    if datum_type is MinerDatum:
        datum_instance = MinerDatum(**common_args) # type: ignore
    elif datum_type is ValidatorDatum:
        datum_instance = ValidatorDatum(**common_args) # type: ignore
    else:
        raise TypeError(f"Unsupported datum type: {datum_type}")

    logger.info(f" - {datum_type.__name__} object created.")
    return datum_instance, uid_hex

# --- Hàm Chính Async ---
async def prepare_datums():
    logger.info("--- Starting Testnet Datum Preparation ---")

    # 1. Load Khóa Funding
    funding_payment_esk: Optional[ExtendedSigningKey] = None
    funding_stake_esk: Optional[ExtendedSigningKey] = None
    try:
        logger.info(f"Loading funding keys: Coldkey='{FUNDING_COLDKEY_NAME}', Hotkey='{FUNDING_HOTKEY_NAME}'")
        funding_payment_esk, funding_stake_esk = decode_hotkey_skey(
            base_dir=HOTKEY_BASE_DIR,
            coldkey_name=FUNDING_COLDKEY_NAME,
            hotkey_name=FUNDING_HOTKEY_NAME,
            password=FUNDING_PASSWORD # type: ignore
        )
        if not funding_payment_esk: raise ValueError("Failed to decode funding payment key.")
        logger.info("Funding keys loaded.")
    except FileNotFoundError as e:
        logger.error(f"FATAL: Key files not found for funding wallet ({FUNDING_COLDKEY_NAME}/{FUNDING_HOTKEY_NAME}): {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"FATAL: Failed to load/decode funding keys: {e}")
        sys.exit(1)

    # 2. Lấy Context và Script Hash
    context: Optional[BlockFrostChainContext] = None
    script_hash: Optional[ScriptHash] = None
    network = Network.TESTNET # Mặc định hoặc đọc từ settings
    try:
        network_str = getattr(sdk_settings, 'CARDANO_NETWORK', 'TESTNET').upper()
        network = Network.MAINNET if network_str == "MAINNET" else Network.TESTNET
        logger.info(f"Initializing Cardano context for {network.name}...")
        context = get_chain_context(method="blockfrost") # Hàm này nên tự đọc network từ settings
        if not context: raise RuntimeError("Failed to initialize Cardano context.")
        if context.network != network: # Kiểm tra lại network của context
             logger.warning(f"Context network ({context.network.name}) differs from settings network ({network.name}). Using context network.")
             network = context.network

        logger.info(f"Context initialized for {network.name}.")

        logger.info("Loading validator script hash...")
        validator_details = read_validator()
        if not validator_details or "script_hash" not in validator_details:
            raise RuntimeError("Could not load validator script hash.")
        script_hash = validator_details["script_hash"]
        logger.info(f"Script Hash: {script_hash}")
    except Exception as e:
        logger.exception(f"FATAL: Error during context/script initialization: {e}")
        sys.exit(1)

    # 3. Tạo các Đối tượng Datum sử dụng hàm helper
    logger.info("Preparing Miner and Validator Datums...")
    datums_to_create: List[PlutusData] = [] # List để chứa tất cả datum cần tạo
    hex_uids_generated : Dict[str, str] = {} # Lưu UID hex để log
    try:
        divisor = sdk_settings.METAGRAPH_DATUM_INT_DIVISOR

        # --- Tạo Miner Datums ---
        miner_datum_1, miner_1_hex = create_and_log_datum(MinerDatum, MINER_UID_STR, MINER_WALLET_ADDR, MINER_API_ENDPOINT, divisor) # type: ignore
        datums_to_create.append(miner_datum_1)
        hex_uids_generated[MINER_UID_STR] = miner_1_hex # type: ignore

        miner_datum_2, miner_2_hex = create_and_log_datum(MinerDatum, MINER_UID_STR2, MINER_WALLET_ADDR2, MINER_API_ENDPOINT2, divisor) # type: ignore
        datums_to_create.append(miner_datum_2)
        hex_uids_generated[MINER_UID_STR2] = miner_2_hex # type: ignore

        # --- Tạo Validator Datums ---
        validator_datum_1, validator_1_hex = create_and_log_datum(ValidatorDatum, VALIDATOR_UID_STR, VALIDATOR_WALLET_ADDR, VALIDATOR_API_ENDPOINT, divisor, initial_perf=0.8, initial_trust=0.8) # type: ignore
        datums_to_create.append(validator_datum_1)
        hex_uids_generated[VALIDATOR_UID_STR] = validator_1_hex # type: ignore

        validator_datum_2, validator_2_hex = create_and_log_datum(ValidatorDatum, VALIDATOR_UID_STR2, VALIDATOR_WALLET_ADDR2, VALIDATOR_API_ENDPOINT2, divisor, initial_perf=0.8, initial_trust=0.8) # type: ignore
        datums_to_create.append(validator_datum_2)
        hex_uids_generated[VALIDATOR_UID_STR2] = validator_2_hex # type: ignore

        validator_datum_3, validator_3_hex = create_and_log_datum(ValidatorDatum, VALIDATOR_UID_STR3, VALIDATOR_WALLET_ADDR3, VALIDATOR_API_ENDPOINT3, divisor, initial_perf=0.8, initial_trust=0.8) # type: ignore
        datums_to_create.append(validator_datum_3)
        hex_uids_generated[VALIDATOR_UID_STR3] = validator_3_hex # type: ignore

        # >>> Cập nhật Thông báo Quan trọng <<<
        logger.warning("-" * 60)
        logger.warning("IMPORTANT: Ensure the STRING UIDs in your .env file")
        logger.warning("(e.g., SUBNET1_VALIDATOR_UID, SUBNET1_MINER_ID) exactly match")
        logger.warning("the strings used to prepare these datums. The system will")
        logger.warning("derive the necessary HEX UIDs automatically during runtime.")
        logger.warning("Corresponding HEX UIDs for reference:")
        for str_uid, hex_uid in hex_uids_generated.items():
             logger.warning(f" - String '{str_uid}' -> HEX {hex_uid}")
        logger.warning("-" * 60)

    except Exception as e:
        logger.exception(f"Failed to create Datum objects: {e}")
        return

    # 4. Xác định địa chỉ ví funding và địa chỉ contract
    try:
        pay_xvk = funding_payment_esk.to_verification_key()
        owner_address: Address
        if funding_stake_esk:
            stk_xvk = funding_stake_esk.to_verification_key()
            owner_address = Address(pay_xvk.hash(), stk_xvk.hash(), network=network) # type: ignore
        else:
            owner_address = Address(pay_xvk.hash(), network=network) # type: ignore
        contract_address = Address(payment_part=script_hash, network=network) # type: ignore
        logger.info(f"Funding Address: {owner_address}")
        logger.info(f"Contract Address: {contract_address}")
    except Exception as e:
        logger.exception(f"Failed to derive addresses: {e}")
        return

    # 5. Tìm UTXO Input Phù Hợp từ ví Funding
    num_outputs = len(datums_to_create)
    if num_outputs == 0:
        logger.warning("No datums were prepared. Exiting.")
        return
    # Ước tính ADA cần thiết: mỗi output cần DATUM_LOCK_AMOUNT, cộng thêm phí giao dịch
    # Phí ước tính thận trọng: ~0.2 ADA mỗi output + 0.2 ADA cho input/change
    estimated_fee = (num_outputs + 2) * 200_000
    total_output_amount = DATUM_LOCK_AMOUNT * num_outputs
    min_input_ada = total_output_amount + estimated_fee + 1_000_000 # Thêm 1 ADA buffer
    logger.info(f"Need input UTXO with >= {min_input_ada / 1_000_000:.6f} ADA for {num_outputs} outputs + fees.")

    selected_input_utxo = find_suitable_ada_input(context, str(owner_address), min_input_ada)

    if not selected_input_utxo:
        logger.error(f"Could not find a suitable ADA-only UTxO with at least {min_input_ada / 1_000_000:.6f} ADA at {owner_address}.")
        logger.error("Ensure the funding wallet (kickoff/hk1 by default) has enough ADA in a single, simple UTxO on Testnet.")
        # Cung cấp hướng dẫn thêm tADA nếu trên Testnet
        if network == Network.TESTNET:
            logger.info("Request tADA from a faucet: https://docs.cardano.org/cardano-testnets/tools/faucet")
        return

    logger.info(f"Selected input UTxO: {selected_input_utxo.input} ({selected_input_utxo.output.amount.coin / 1_000_000:.6f} ADA)")

    # 6. Xây dựng và Gửi Giao dịch DUY NHẤT
    try:
        builder = TransactionBuilder(context=context)
        builder.add_input(selected_input_utxo) # Thêm input tường minh

        # Thêm output cho từng Datum đã tạo
        for datum_obj in datums_to_create:
            builder.add_output(
                TransactionOutput(
                    address=contract_address,
                    amount=Value(coin=DATUM_LOCK_AMOUNT), # <<<--- Đảm bảo Amount là Value
                    datum=datum_obj
                )
            )
            logger.debug(f"Added output with datum: {datum_obj}")

        # Build, Sign, Submit (chỉ cần khóa payment của funding wallet)
        logger.info("Building and signing the combined transaction...")
        signed_tx = builder.build_and_sign(
            signing_keys=[funding_payment_esk], # Chỉ cần khóa payment
            change_address=owner_address
        )

        logger.info(f"Submitting combined transaction (Estimated Fee: {signed_tx.transaction_body.fee / 1_000_000:.6f} ADA)...")
        # Submit giao dịch - cần await nếu context.submit_tx là async
        # tx_id : TransactionId = await context.submit_tx(signed_tx.to_cbor()) # Nếu async
        tx_id : TransactionId = await asyncio.to_thread(context.submit_tx, signed_tx.to_cbor()) # type: ignore # Nếu sync
        tx_id_str = str(tx_id)
        logger.info(f"Combined transaction submitted successfully: TxID: {tx_id_str}")
        scan_url = f"https://preprod.cardanoscan.io/transaction/{tx_id_str}" if network == Network.TESTNET else f"https://cardanoscan.io/transaction/{tx_id_str}"
        logger.info(f"  -> Check on Cardanoscan ({network.name}): {scan_url}")

    except Exception as e:
        logger.exception(f"Failed to build or submit the combined transaction: {e}")

    logger.info("--- Datum Preparation Script Finished ---")

# --- Chạy hàm chính ---
if __name__ == "__main__":
    try:
        asyncio.run(prepare_datums())
    except KeyboardInterrupt:
        logger.info("Script interrupted by user.")
    except Exception as e:
        logger.exception(f"Failed to run prepare_datums: {e}")