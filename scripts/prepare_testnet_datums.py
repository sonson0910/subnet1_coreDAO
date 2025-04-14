# File: scripts/prepare_testnet_datums.py (ĐÃ SỬA ĐỔI)

import os
import sys
import logging
import asyncio
import hashlib
from pathlib import Path
from dotenv import load_dotenv
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
)

# --- Thêm đường dẫn gốc của project vào sys.path ---
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
# -------------------------------------------------

# Import các thành phần cần thiết từ SDK Moderntensor
try:
    # <<<--- SỬA LỖI IMPORT: create_utxo đã chuyển sang create_utxo_explicit_input ---<<<
    # from sdk.metagraph.create_utxo import create_utxo # Bỏ dòng này
    from sdk.metagraph.create_utxo import create_utxo_explicit_input, find_suitable_ada_input # Thêm find_suitable_ada_input
    # -----------------------------------------------------------------------------
    from sdk.metagraph.metagraph_datum import MinerDatum, ValidatorDatum, STATUS_ACTIVE
    from sdk.metagraph.hash.hash_datum import hash_data
    from sdk.service.context import get_chain_context
    from sdk.keymanager.decryption_utils import decode_hotkey_skey
    from sdk.smartcontract.validator import read_validator
    from sdk.config.settings import settings as sdk_settings # Import settings của SDK
    from pycardano import (
        Network, ScriptHash, ExtendedSigningKey, BlockFrostChainContext,
        TransactionId # Import TransactionId để kiểm tra kiểu trả về
    )
    from typing import Optional, Tuple, List # Thêm List
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
DEFAULT_MIN_UTXO_FETCH_ADA = 5_000_000
# ------------------------

# --- Lấy thông tin Miner và Validator từ .env ---
MINER_UID_STR = os.getenv("SUBNET1_MINER_ID", "my_cool_image_miner_01")
MINER_WALLET_ADDR = os.getenv("SUBNET1_MINER_WALLET_ADDR") # Bỏ giá trị mặc định để bắt lỗi thiếu
MINER_API_ENDPOINT = os.getenv("SUBNET1_MINER_API_ENDPOINT")

VALIDATOR_UID_STR = os.getenv("SUBNET1_VALIDATOR_UID") # <<< Lấy UID dạng STRING
VALIDATOR_WALLET_ADDR = os.getenv("SUBNET1_VALIDATOR_ADDRESS")
VALIDATOR_API_ENDPOINT = os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT")

VALIDATOR_UID_STR2 = os.getenv("SUBNET1_VALIDATOR_UID2") # <<< Lấy UID dạng STRING
VALIDATOR_WALLET_ADDR2 = os.getenv("SUBNET1_VALIDATOR_ADDRESS2")
VALIDATOR_API_ENDPOINT2 = os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT2")

VALIDATOR_UID_STR3 = os.getenv("SUBNET1_VALIDATOR_UID3") # <<< Lấy UID dạng STRING
VALIDATOR_WALLET_ADDR3 = os.getenv("SUBNET1_VALIDATOR_ADDRESS3")
VALIDATOR_API_ENDPOINT3 = os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT3")

MINER_UID_STR2 = os.getenv("SUBNET1_MINER_ID2", "my_cool_image_miner_02")
MINER_WALLET_ADDR2 = os.getenv("SUBNET1_MINER_WALLET_ADDR2") # Bỏ giá trị mặc định
MINER_API_ENDPOINT2 = os.getenv("SUBNET1_MINER_API_ENDPOINT2")

# --- Lấy cấu hình ví Funding ---
FUNDING_COLDKEY_NAME = os.getenv("FUNDING_COLDKEY_NAME", "kickoff")
FUNDING_HOTKEY_NAME = os.getenv("FUNDING_HOTKEY_NAME", "hk1")
FUNDING_PASSWORD = os.getenv("FUNDING_PASSWORD", "sonlearn2003") # Bỏ mặc định
HOTKEY_BASE_DIR = os.getenv("HOTKEY_BASE_DIR", getattr(sdk_settings, 'HOTKEY_BASE_DIR', 'moderntensor'))

DATUM_LOCK_AMOUNT = 2_000_000 # 2 ADA

# --- Kiểm tra các biến môi trường bắt buộc ---
required_env_vars = {
    "MINER_WALLET_ADDR": MINER_WALLET_ADDR, "MINER_API_ENDPOINT": MINER_API_ENDPOINT,
    "VALIDATOR_UID_STR": VALIDATOR_UID_STR, "VALIDATOR_WALLET_ADDR": VALIDATOR_WALLET_ADDR, "VALIDATOR_API_ENDPOINT": VALIDATOR_API_ENDPOINT,
    "VALIDATOR_UID_STR2": VALIDATOR_UID_STR2, "VALIDATOR_WALLET_ADDR2": VALIDATOR_WALLET_ADDR2, "VALIDATOR_API_ENDPOINT2": VALIDATOR_API_ENDPOINT2,
    "VALIDATOR_UID_STR3": VALIDATOR_UID_STR3, "VALIDATOR_WALLET_ADDR3": VALIDATOR_WALLET_ADDR3, "VALIDATOR_API_ENDPOINT3": VALIDATOR_API_ENDPOINT3,
    "MINER_WALLET_ADDR2": MINER_WALLET_ADDR2, "MINER_API_ENDPOINT2": MINER_API_ENDPOINT2,
    "FUNDING_PASSWORD": FUNDING_PASSWORD,
}
missing_vars = [k for k, v in required_env_vars.items() if not v]
if missing_vars:
    logger.error(f"FATAL: Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)
# --------------------------------------------------

# --- Hàm tạo Datum Helper (để tránh lặp code và in UID hex) ---
def create_and_log_datum(datum_type: type, uid_str: str, wallet_addr: str, api_endpoint: str, divisor: float, subnet_id: int = 1, initial_perf: float = 0.5, initial_trust: float = 0.5, initial_stake: int = 0):
    """Tạo đối tượng Datum (Miner hoặc Validator) và in ra UID hex tương ứng."""
    uid_bytes = uid_str.encode('utf-8')
    uid_hex = uid_bytes.hex() # <<< TÍNH HEX Ở ĐÂY
    logger.info(f"Preparing Datum for String UID: '{uid_str}' -> HEX UID: {uid_hex}") # <<< IN RA HEX

    wallet_hash_bytes = hash_data(wallet_addr)
    api_bytes = api_endpoint.encode('utf-8') if api_endpoint else b'' # Xử lý None

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
        "api_endpoint": api_bytes,
    }

    if datum_type == MinerDatum:
        datum = MinerDatum(**common_args)
    elif datum_type == ValidatorDatum:
         # Giả sử ValidatorDatum có cùng các trường cơ bản
         # Nếu khác, cần điều chỉnh common_args hoặc thêm logic riêng
        datum = ValidatorDatum(**common_args)
    else:
        raise TypeError(f"Unsupported datum type: {datum_type}")

    logger.info(f" - {datum_type.__name__} object created.")
    # Trả về cả datum và hex để tiện dùng nếu cần
    return datum, uid_hex

# --- Hàm Chính Async ---
async def prepare_datums():
    logger.info("--- Starting Testnet Datum Preparation ---")

    # 1. Load Khóa Funding (Giữ nguyên logic)
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
        if not funding_payment_esk: raise ValueError("...")
        logger.info("Funding keys loaded.")
    except Exception as e: logger.exception(...) ; return

    # 2. Lấy Context và Script Hash (Giữ nguyên logic)
    context: Optional[BlockFrostChainContext] = None
    script_hash: Optional[ScriptHash] = None
    network = Network.TESTNET
    try:
        logger.info("Initializing Cardano context...")
        context = get_chain_context(method="blockfrost")
        if not context: raise RuntimeError("...")
        logger.info(f"Context initialized for {context.network.name}.")

        logger.info("Loading validator script hash...")
        validator_details = read_validator()
        if not validator_details or "script_hash" not in validator_details: raise RuntimeError("...")
        script_hash = validator_details["script_hash"]
        logger.info(f"Script Hash: {script_hash}")
    except Exception as e: logger.exception(...) ; return

    # 3. Tạo các Đối tượng Datum sử dụng hàm helper
    logger.info("Preparing Miner and Validator Datums...")
    datums_to_create: List[PlutusData] = [] # List để chứa tất cả datum cần tạo
    try:
        divisor = getattr(sdk_settings, 'METAGRAPH_DATUM_INT_DIVISOR', 1_000_000.0)

        # Tạo Miner 1
        miner_datum_1, miner_1_hex = create_and_log_datum(MinerDatum, MINER_UID_STR, MINER_WALLET_ADDR, MINER_API_ENDPOINT, divisor) # type: ignore
        datums_to_create.append(miner_datum_1)

        # Tạo Miner 2
        miner_datum_2, miner_2_hex = create_and_log_datum(MinerDatum, MINER_UID_STR2, MINER_WALLET_ADDR2, MINER_API_ENDPOINT2, divisor) # type: ignore
        datums_to_create.append(miner_datum_2)

        # Tạo Validator 1
        validator_datum_1, validator_1_hex = create_and_log_datum(ValidatorDatum, VALIDATOR_UID_STR, VALIDATOR_WALLET_ADDR, VALIDATOR_API_ENDPOINT, divisor, initial_perf=0.8, initial_trust=0.8) # type: ignore
        datums_to_create.append(validator_datum_1)

        # Tạo Validator 2
        validator_datum_2, validator_2_hex = create_and_log_datum(ValidatorDatum, VALIDATOR_UID_STR2, VALIDATOR_WALLET_ADDR2, VALIDATOR_API_ENDPOINT2, divisor, initial_perf=0.8, initial_trust=0.8) # type: ignore
        datums_to_create.append(validator_datum_2)

        # Tạo Validator 3
        validator_datum_3, validator_3_hex = create_and_log_datum(ValidatorDatum, VALIDATOR_UID_STR3, VALIDATOR_WALLET_ADDR3, VALIDATOR_API_ENDPOINT3, divisor, initial_perf=0.8, initial_trust=0.8) # type: ignore
        datums_to_create.append(validator_datum_3)

        # >>> QUAN TRỌNG: NHẮC NGƯỜI DÙNG CẬP NHẬT .env <<<
        logger.warning("IMPORTANT: Update your .env file(s) for validator/miner processes with the HEX UIDs printed above!")
        logger.warning(f" - Example for Validator 1: SUBNET1_VALIDATOR_UID={validator_1_hex}")
        logger.warning(f" - Example for Validator 2: SUBNET1_VALIDATOR_UID2={validator_2_hex}")
        logger.warning(f" - Example for Validator 3: SUBNET1_VALIDATOR_UID3={validator_3_hex}")
        logger.warning(f" - Example for Miner 1: MINER_UID_HEX={miner_1_hex}") # Dùng MINER_UID_HEX cho agent
        logger.warning(f" - Example for Miner 2: MINER_UID_HEX={miner_2_hex}") # Dùng MINER_UID_HEX cho agent

    except Exception as e:
        logger.exception(f"Failed to create Datum objects: {e}")
        return

    # 4. Xác định địa chỉ ví funding và địa chỉ contract (Giữ nguyên logic)
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

    # 5. Tìm UTXO Input Phù Hợp (Cần đủ cho TẤT CẢ output + phí)
    num_outputs = len(datums_to_create)
    total_output_amount = DATUM_LOCK_AMOUNT * num_outputs
    min_input_ada = total_output_amount + (num_outputs + 1) * 180000 # Ước tính phí (~0.18 ADA mỗi input/output) + buffer
    logger.info(f"Need input UTXO with >= {min_input_ada} lovelace for {num_outputs} outputs.")
    selected_input_utxo = find_suitable_ada_input(context, str(owner_address), min_input_ada)

    if not selected_input_utxo:
        logger.error(f"Could not find a suitable ADA-only UTxO with at least {min_input_ada} lovelace at {owner_address}. Ensure funding wallet has enough ADA in a single UTxO.")
        return

    logger.info(f"Selected input UTxO: {selected_input_utxo.input} ({selected_input_utxo.output.amount.coin} lovelace)")

    # 6. Xây dựng và Gửi Giao dịch DUY NHẤT
    try:
        builder = TransactionBuilder(context=context)
        builder.add_input(selected_input_utxo) # Thêm input tường minh

        # Thêm output cho từng Datum đã tạo
        for datum_obj in datums_to_create:
            builder.add_output(
                TransactionOutput(
                    address=contract_address,
                    amount=DATUM_LOCK_AMOUNT, # type: ignore
                    datum=datum_obj
                )
            )
            logger.debug(f"Added output with datum: {datum_obj}")

        # Build, Sign, Submit
        logger.info("Building and signing the combined transaction...")
        # Chỉ cần khóa payment vì input là từ ví funding (trừ khi script yêu cầu khác)
        signed_tx = builder.build_and_sign(
            signing_keys=[funding_payment_esk], # type: ignore
            change_address=owner_address
        )

        logger.info(f"Submitting combined transaction (Tx Fee: {signed_tx.transaction_body.fee} lovelace)...")
        tx_id : TransactionId = context.submit_tx(signed_tx) # type: ignore
        tx_id_str = str(tx_id)
        logger.info(f"Combined transaction submitted successfully: TxID: {tx_id_str}")
        logger.info(f"  -> Check on Cardanoscan (Preprod): https://preprod.cardanoscan.io/transaction/{tx_id_str}") # Sửa link cho Preprod

    except Exception as e:
        logger.exception(f"Failed to build or submit the combined transaction: {e}")

    logger.info("--- Datum Preparation Script Finished ---")

# --- find_suitable_ada_input (Giữ nguyên) ---
def find_suitable_ada_input(context: BlockFrostChainContext, address: str, min_ada: int) -> Optional[UTxO]:
    # ... (logic tìm UTXO như cũ) ...
    logger.info(f"Searching for ADA-only UTxO at {address} with >= {min_ada} lovelace...")
    try:
        utxos = context.utxos(address)
        suitable_utxos = [u for u in utxos if not u.output.amount.multi_asset and u.output.amount.coin >= min_ada]
        if suitable_utxos:
            suitable_utxos.sort(key=lambda u: u.output.amount.coin)
            logger.info(f"Found {len(suitable_utxos)} suitable UTxOs. Selecting smallest: {suitable_utxos[0].input}")
            return suitable_utxos[0]
    except Exception as e: logger.exception(...)
    logger.warning(f"No suitable ADA-only UTxO found with >= {min_ada} lovelace at {address}.")
    return None

# --- Chạy hàm chính ---
if __name__ == "__main__":
    try:
        asyncio.run(prepare_datums())
    except KeyboardInterrupt:
        logger.info("Script interrupted by user.")
    except Exception as e:
        logger.exception(f"Failed to run prepare_datums: {e}")