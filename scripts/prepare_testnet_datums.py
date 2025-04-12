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
    from sdk.metagraph.create_utxo import create_utxo_explicit_input
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
    from typing import Optional, Tuple # Import kiểu dữ liệu
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
DEFAULT_MIN_UTXO_FETCH_ADA = 5_000_000  # Ước tính tối thiểu ADA cần có trong UTXO đầu vào (2 ADA output + 3 ADA dự phòng/phí)
# ------------------------

# --- Định nghĩa thông tin cho Miner và Validator ---
# **QUAN TRỌNG**: Thay thế các giá trị này bằng thông tin thực tế của bạn
# Lấy từ biến môi trường hoặc đặt trực tiếp ở đây
MINER_UID_STR = os.getenv("SUBNET1_MINER_ID", "my_cool_image_miner_01") # UID cho miner
MINER_WALLET_ADDR = os.getenv("SUBNET1_MINER_WALLET_ADDR", "addr_test1qpkxr3kpzex93m646qr7w82d56md2kchtsv9jy39dykn4cmcxuuneyeqhdc4wy7de9mk54fndmckahxwqtwy3qg8pums5vlxhz") # Địa chỉ ví liên kết với miner (nếu có)
MINER_API_ENDPOINT = os.getenv("SUBNET1_MINER_API_ENDPOINT") # URL thực tế miner sẽ chạy (VÍ DỤ: http://<miner_ip>:9001)

VALIDATOR_UID_STR = os.getenv("SUBNET1_VALIDATOR_UID", "validator_001_subnet1_hex") # UID cho validator
VALIDATOR_WALLET_ADDR = os.getenv("SUBNET1_VALIDATOR_ADDRESS", "addr_test1qz9twyn8njyux586y7c92c3ldwk33xgutw4qjtjahjnqqytyau03kld4qfhqnd77r8jcmr39zn3cpr003pxccr5sjsnq9m4n4c") # Địa chỉ ví của validator
VALIDATOR_API_ENDPOINT = os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT") # URL thực tế validator API sẽ chạy (VÍ DỤ: http://<your_ip>:8000)

# Cấu hình ví Funding (ví trả phí giao dịch)
FUNDING_COLDKEY_NAME = os.getenv("FUNDING_COLDKEY_NAME", "kickoff") # Thay bằng coldkey của ví funding
FUNDING_HOTKEY_NAME = os.getenv("FUNDING_HOTKEY_NAME", "hk1")     # Thay bằng hotkey của ví funding
FUNDING_PASSWORD = os.getenv("FUNDING_PASSWORD", "sonlearn2003")                # Mật khẩu ví funding
HOTKEY_BASE_DIR = os.getenv("HOTKEY_BASE_DIR", getattr(sdk_settings, 'HOTKEY_BASE_DIR', 'moderntensor'))

#
VALIDATOR_UID_STR2 = os.getenv("SUBNET1_VALIDATOR_UID2", "validator_002_subnet2_hex") # UID cho validator
VALIDATOR_WALLET_ADDR2 = os.getenv("SUBNET1_VALIDATOR_ADDRESS2", "addr_test1qqzd49tpd3jhj8x5zccj4gs86jw5azmxh72aj4qu7qq5w2nkdkeqgaum48adxlmfrauaun4txvrkp80wr55l0xuy07fsmr9ayj") # Địa chỉ ví của validator
VALIDATOR_API_ENDPOINT2 = os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT2")

# Cấu hình ví Funding (ví trả phí giao dịch)
FUNDING_COLDKEY_NAME = os.getenv("FUNDING_COLDKEY_NAME2", "validator2") # Thay bằng coldkey của ví funding
FUNDING_HOTKEY_NAME = os.getenv("FUNDING_HOTKEY_NAME2", "hk1")     # Thay bằng hotkey của ví funding
FUNDING_PASSWORD = os.getenv("FUNDING_PASSWORD2", "sonlearn2003")                # Mật khẩu ví funding
HOTKEY_BASE_DIR = os.getenv("HOTKEY_BASE_DIR2", getattr(sdk_settings, 'HOTKEY_BASE_DIR', 'moderntensor'))

MINER_UID_STR2 = os.getenv("SUBNET1_MINER_ID2", "my_cool_image_miner_02") # UID cho miner
MINER_WALLET_ADDR2 = os.getenv("SUBNET1_MINER_WALLET_ADDR", "addr_test1qqcxrwktpurgvrqt28xr5ha039j7ga59x33wp0r8dzkt4zysckcur8c2yu2975qwvtcg3gn73rf3v5e3wz0yaffkx7use04tnu") # Địa chỉ ví liên kết với miner (nếu có)
MINER_API_ENDPOINT2 = os.getenv("SUBNET1_MINER_API_ENDPOINT2") # URL thực tế miner sẽ chạy (VÍ DỤ: http://<miner_ip>:9001)

# Lượng ADA lock trong mỗi UTXO (ví dụ: 2 tADA)
DATUM_LOCK_AMOUNT = 2_000_000

# --------------------------------------------------

async def prepare_datums():
    """Hàm async để chuẩn bị và gửi MỘT giao dịch tạo cả hai UTXO."""
    logger.info("--- Starting Testnet Datum Preparation (Single Transaction) ---")

    # ... (Kiểm tra biến môi trường và load khóa funding giữ nguyên) ...
    if not MINER_API_ENDPOINT or not VALIDATOR_API_ENDPOINT:
        logger.error("FATAL: SUBNET1_MINER_API_ENDPOINT or SUBNET1_VALIDATOR_API_ENDPOINT not set in .env")
        return
    if not FUNDING_PASSWORD:
        logger.error("FATAL: FUNDING_PASSWORD not set in .env for the funding wallet.")
        return

    # --- 1. Load Khóa Funding ---
    funding_payment_esk: Optional[ExtendedSigningKey] = None
    funding_stake_esk: Optional[ExtendedSigningKey] = None
    try:
        logger.info(f"Loading funding keys: Coldkey='{FUNDING_COLDKEY_NAME}', Hotkey='{FUNDING_HOTKEY_NAME}'")
        funding_payment_esk, funding_stake_esk = decode_hotkey_skey(
            base_dir=HOTKEY_BASE_DIR,
            coldkey_name=FUNDING_COLDKEY_NAME,
            hotkey_name=FUNDING_HOTKEY_NAME,
            password=FUNDING_PASSWORD
        )
        if not funding_payment_esk:
             raise ValueError("Failed to decode funding payment signing key.")
        logger.info("Funding keys loaded.")
    except Exception as e:
        logger.exception(f"Failed to load funding keys: {e}")
        return

    # --- 2. Lấy Context và Script Hash ---
    context: Optional[BlockFrostChainContext] = None
    script_hash: Optional[ScriptHash] = None
    network = Network.TESTNET # Hoặc lấy từ settings/env
    try:
        logger.info("Initializing Cardano context...")
        context = get_chain_context(method="blockfrost")
        if not context: raise RuntimeError("Failed to get Cardano context.")
        # context.network = network
        logger.info(f"Context initialized for {context.network.name}.")

        logger.info("Loading validator script hash...")
        validator_details = read_validator()
        if not validator_details or "script_hash" not in validator_details:
            raise RuntimeError("Failed to load validator script hash.")
        script_hash = validator_details["script_hash"]
        logger.info(f"Script Hash: {script_hash}")
    except Exception as e:
        logger.exception(f"Failed to initialize context or script hash: {e}")
        return

    # --- 3. Tạo Đối tượng MinerDatum và ValidatorDatum ---
    logger.info("Preparing Miner and Validator Datums...")
    try:
        divisor = getattr(sdk_settings, 'METAGRAPH_DATUM_INT_DIVISOR', 1_000_000.0)
        # Miner Datum
        miner_uid_bytes = MINER_UID_STR.encode('utf-8')
        miner_wallet_hash_bytes = hash_data(MINER_WALLET_ADDR)
        miner_api_bytes = MINER_API_ENDPOINT.encode('utf-8')
        miner_datum = MinerDatum(
            uid=miner_uid_bytes, subnet_uid=1, stake=0,
            scaled_last_performance=int(0.5 * divisor), scaled_trust_score=int(0.5 * divisor),
            accumulated_rewards=0, last_update_slot=0, performance_history_hash=hash_data([]),
            wallet_addr_hash=miner_wallet_hash_bytes, status=STATUS_ACTIVE, registration_slot=0,
            api_endpoint=miner_api_bytes,
        )
        logger.info(f"Miner Datum prepared for UID: {MINER_UID_STR}")

        # Validator Datum
        validator_uid_bytes = VALIDATOR_UID_STR.encode('utf-8')
        validator_wallet_hash_bytes = hash_data(VALIDATOR_WALLET_ADDR)
        validator_api_bytes = VALIDATOR_API_ENDPOINT.encode('utf-8')
        validator_datum = ValidatorDatum(
            uid=validator_uid_bytes, subnet_uid=1, stake=0,
            scaled_last_performance=int(0.8 * divisor), scaled_trust_score=int(0.8 * divisor),
            accumulated_rewards=0, last_update_slot=0, performance_history_hash=hash_data([]),
            wallet_addr_hash=validator_wallet_hash_bytes, status=STATUS_ACTIVE, registration_slot=0,
            api_endpoint=validator_api_bytes,
        )
        logger.info(f"Validator Datum prepared for UID: {VALIDATOR_UID_STR}")

        miner_uid_bytes2 = MINER_UID_STR2.encode('utf-8')
        miner_wallet_hash_bytes2 = hash_data(MINER_WALLET_ADDR2)
        miner_api_bytes2 = MINER_API_ENDPOINT2.encode('utf-8')
        miner_datum2 = MinerDatum(
            uid=miner_uid_bytes2, subnet_uid=1, stake=0,
            scaled_last_performance=int(0.5 * divisor), scaled_trust_score=int(0.5 * divisor),
            accumulated_rewards=0, last_update_slot=0, performance_history_hash=hash_data([]),
            wallet_addr_hash=miner_wallet_hash_bytes2, status=STATUS_ACTIVE, registration_slot=0,
            api_endpoint=miner_api_bytes2,
        )
        logger.info(f"Miner Datum prepared for UID: {MINER_UID_STR}")

        # Validator Datum
        validator_uid_bytes2 = VALIDATOR_UID_STR2.encode('utf-8')
        validator_wallet_hash_bytes2 = hash_data(VALIDATOR_WALLET_ADDR)
        validator_api_bytes2 = VALIDATOR_API_ENDPOINT2.encode('utf-8')
        validator_datum2 = ValidatorDatum(
            uid=validator_uid_bytes2, subnet_uid=1, stake=0,
            scaled_last_performance=int(0.8 * divisor), scaled_trust_score=int(0.8 * divisor),
            accumulated_rewards=0, last_update_slot=0, performance_history_hash=hash_data([]),
            wallet_addr_hash=validator_wallet_hash_bytes2, status=STATUS_ACTIVE, registration_slot=0,
            api_endpoint=validator_api_bytes2,
        )
        logger.info(f"Validator Datum prepared for UID: {VALIDATOR_UID_STR2}")

    except Exception as e:
        logger.exception(f"Failed to create Datum objects: {e}")
        return

    # --- 4. Xác định địa chỉ ví funding và địa chỉ contract ---
    pay_xvk = funding_payment_esk.to_verification_key()
    owner_address: Address
    if funding_stake_esk:
        stk_xvk = funding_stake_esk.to_verification_key()
        owner_address = Address(pay_xvk.hash(), stk_xvk.hash(), network=network)
    else:
        owner_address = Address(pay_xvk.hash(), network=network)
    contract_address = Address(payment_part=script_hash, network=network) # type: ignore
    logger.info(f"Funding Address: {owner_address}")
    logger.info(f"Contract Address: {contract_address}")

    # --- 5. Tìm UTXO Input Phù Hợp (Cần đủ cho CẢ HAI output + phí) ---
    total_output_amount = DATUM_LOCK_AMOUNT * 2 # Cần 2 UTXO output
    min_input_ada = total_output_amount + 1_000_000 # Ước tính cần thêm 1 ADA cho phí
    logger.info(f"Finding suitable ADA-only input UTXO with >= {min_input_ada} lovelace...")
    selected_input_utxo = find_suitable_ada_input(context, str(owner_address), min_input_ada)

    if not selected_input_utxo:
        logger.error(f"Could not find a suitable ADA-only UTxO with at least {min_input_ada} lovelace at {owner_address}. "
                     "Please ensure the funding wallet has adequate, simple UTxOs.")
        return

    logger.info(f"Selected input UTxO: {selected_input_utxo.input} ({selected_input_utxo.output.amount.coin} lovelace)")

    # --- 6. Xây dựng và Gửi Giao dịch DUY NHẤT ---
    try:
        builder = TransactionBuilder(context=context)
        builder.add_input(selected_input_utxo) # Thêm input tường minh

        # # Thêm output cho Miner Datum
        # builder.add_output(
        #     TransactionOutput(
        #         address=contract_address,
        #         amount=DATUM_LOCK_AMOUNT,
        #         datum=miner_datum
        #     )
        # )

        builder.add_output(
            TransactionOutput(
                address=contract_address,
                amount=DATUM_LOCK_AMOUNT,
                datum=miner_datum2
            )
        )

        # # Thêm output cho Validator Datum
        # builder.add_output(
        #     TransactionOutput(
        #         address=contract_address,
        #         amount=DATUM_LOCK_AMOUNT,
        #         datum=validator_datum
        #     )
        # )

        # builder.add_output(
        #     TransactionOutput(
        #         address=contract_address,
        #         amount=DATUM_LOCK_AMOUNT,
        #         datum=validator_datum2
        #     )
        # )

        logger.info("Building and signing the combined transaction...")
        signed_tx = builder.build_and_sign(
            signing_keys=[funding_payment_esk], # Chỉ cần khóa payment
            change_address=owner_address
        )

        logger.info(f"Submitting combined transaction (Tx Fee: {signed_tx.transaction_body.fee} lovelace)...")
        tx_id = context.submit_tx(signed_tx)
        tx_id_str = str(tx_id)
        logger.info(f"Combined transaction submitted successfully: {tx_id_str}")
        logger.info(f"  -> Check: https://testnet.cardanoscan.io/transaction/{tx_id_str}")

    except Exception as e:
        logger.exception(f"Failed to build or submit the combined transaction: {e}")

    logger.info("--- Datum Preparation Script Finished ---")


def find_suitable_ada_input(
    context: BlockFrostChainContext,
    address: str,
    min_ada: int = DEFAULT_MIN_UTXO_FETCH_ADA,
) -> Optional[UTxO]:
    """
    Tìm một UTxO chỉ chứa ADA tại địa chỉ cho trước với lượng ADA tối thiểu.

    Args:
        context: Context blockchain.
        address: Địa chỉ ví cần tìm UTXO.
        min_ada: Lượng ADA tối thiểu (lovelace) mà UTxO phải có.

    Returns:
        UTxO phù hợp đầu tiên tìm thấy, hoặc None.
    """
    logger.info(
        f"Searching for suitable ADA-only UTxO at {address} with at least {min_ada} lovelace..."
    )
    try:
        utxos = context.utxos(address)
        logger.debug(f"Found {len(utxos)} total UTxOs at address.")

        suitable_utxos = []
        for utxo in utxos:
            # Kiểm tra xem có multi_asset không và lượng ADA có đủ không
            if (
                not utxo.output.amount.multi_asset
                and utxo.output.amount.coin >= min_ada
            ):
                suitable_utxos.append(utxo)
                logger.debug(
                    f"  - Found suitable ADA-only UTxO: {utxo.input} with {utxo.output.amount.coin} lovelace"
                )
                # Có thể trả về ngay cái đầu tiên tìm thấy để đơn giản
                # return utxo

        # Nếu muốn chọn UTXO nhỏ nhất đủ dùng thay vì cái đầu tiên:
        if suitable_utxos:
            suitable_utxos.sort(
                key=lambda u: u.output.amount.coin
            )  # Sắp xếp theo ADA tăng dần
            logger.info(
                f"Found {len(suitable_utxos)} suitable ADA-only UTxOs. Selecting the smallest one: {suitable_utxos[0].input}"
            )
            return suitable_utxos[0]

    except Exception as e:
        logger.exception(f"Error fetching or filtering UTxOs for {address}: {e}")

    logger.warning(
        f"No suitable ADA-only UTxO found with at least {min_ada} lovelace at {address}."
    )
    return None

if __name__ == "__main__":
    try:
        asyncio.run(prepare_datums())
    except KeyboardInterrupt:
        logger.info("Script interrupted by user.")
    except Exception as e:
        logger.exception(f"Failed to run prepare_datums: {e}")