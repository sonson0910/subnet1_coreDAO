# File: scripts/run_miner2.py
# Chạy cả Miner Server (xử lý task AI) và Miner Agent (cập nhật blockchain)
# Sử dụng SUBNET1_MINER_ID để tự động suy ra UID hex on-chain.

import os
import sys
import logging
import asyncio
import threading
import binascii # <<<--- Import binascii
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# --- Thêm đường dẫn gốc của project vào sys.path ---
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
# -------------------------------------------------

# --- Import các lớp cần thiết ---
try:
    # Lớp Miner của Subnet 1 (xử lý task AI)
    from subnet1.miner import Subnet1Miner
    # Lớp Miner Agent từ SDK (xử lý blockchain)
    from sdk.agent.miner_agent import MinerAgent
    # Các thành phần khác từ SDK
    from sdk.config.settings import settings as sdk_settings
    from sdk.keymanager.decryption_utils import decode_hotkey_skey
    from pycardano import ExtendedSigningKey
except ImportError as e:
    print(f"Error: Could not import required classes. Details: {e}")
    print("Ensure the moderntensor SDK is installed correctly and accessible.")
    sys.exit(1)
# ---------------------------------------------------

# --- Tải biến môi trường (.env) ---
env_path = project_root / '.env'
if env_path.exists():
    print(f"Loading environment variables from: {env_path}")
    load_dotenv(dotenv_path=env_path, override=True)
else:
    print(f"Warning: .env file not found at {env_path}. Using default values or existing environment variables.")
# ------------------------------------

# --- Cấu hình Logging ---
log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(level=log_level, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)
# ------------------------

async def run_miner_processes():
    """Hàm async để cấu hình và chạy cả Miner Server và Miner Agent."""

    # === Cấu hình chung cho Miner ===
    miner_readable_id = os.getenv("SUBNET1_MINER_ID2")
    if not miner_readable_id:
        logger.error("FATAL: SUBNET1_MINER_ID2 (the readable miner identifier) is not set in .env.")
        return

    # --- Tính toán UID hex dự kiến từ ID cấu hình ---
    try:
        expected_uid_bytes = miner_readable_id.encode('utf-8')
        expected_uid_hex = expected_uid_bytes.hex()
        logger.info(f"Derived On-Chain UID Hex from SUBNET1_MINER_ID2 ('{miner_readable_id}'): {expected_uid_hex}")
    except Exception as e:
        logger.error(f"FATAL: Could not encode SUBNET1_MINER_ID2 ('{miner_readable_id}') to derive UID: {e}")
        return
    # --------------------------------------------------

    # === Cấu hình cho Subnet1Miner (Xử lý Task AI) ===
    validator_result_submit_url = os.getenv("SUBNET1_VALIDATOR_URL2")
    if not validator_result_submit_url:
        logger.error("FATAL: SUBNET1_VALIDATOR_URL2 (for AI results submission) is not set.")
        return
    miner_host = os.getenv("SUBNET1_MINER_HOST", "0.0.0.0") # Lắng nghe trên tất cả interfaces
    miner_port = int(os.getenv("SUBNET1_MINER_PORT", 9001)) # Cổng mặc định

    logger.info("--- Subnet 1 Miner AI Task Server Configuration ---")
    logger.info(f"Miner Readable ID     : {miner_readable_id}")
    logger.info(f"Listening on          : {miner_host}:{miner_port}")
    logger.info(f"Validator Submit URL  : {validator_result_submit_url}")
    logger.info("-------------------------------------------------")

    # === Cấu hình cho MinerAgent (Cập nhật Blockchain) ===
    # Sử dụng expected_uid_hex đã tính toán
    miner_coldkey_name = os.getenv("MINER_COLDKEY_NAME2")
    miner_hotkey_name = os.getenv("MINER_HOTKEY_NAME2")
    miner_password = os.getenv("MINER_HOTKEY_PASSWORD2")
    # URL API của Validator để Miner Agent fetch kết quả đồng thuận
    validator_consensus_api_url = os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT2") # Ví dụ: http://127.0.0.1:8001
    miner_check_interval = int(os.getenv("MINER_AGENT_CHECK_INTERVAL", 300)) # Khoảng thời gian check (giây)

    # Kiểm tra các cấu hình cần thiết cho Agent
    if not all([miner_coldkey_name, miner_hotkey_name, miner_password, validator_consensus_api_url]):
        missing_agent_configs = [
            k for k, v in {
                # Không cần kiểm tra UID hex ở đây nữa
                "MINER_COLDKEY_NAME2": miner_coldkey_name,
                "MINER_HOTKEY_NAME2": miner_hotkey_name,
                "MINER_HOTKEY_PASSWORD2": miner_password,
                "SUBNET1_VALIDATOR_API_ENDPOINT2": validator_consensus_api_url
            }.items() if not v
        ]
        logger.error(f"FATAL: Missing Miner Agent configurations in .env: {missing_agent_configs}")
        return

    logger.info("--- Miner Agent (Blockchain Update) Configuration ---")
    logger.info(f"Miner Agent UID (Hex) : {expected_uid_hex}") # Log UID hex dùng cho agent
    logger.info(f"Coldkey Name          : {miner_coldkey_name}")
    logger.info(f"Hotkey Name           : {miner_hotkey_name}")
    logger.info(f"Validator Result API  : {validator_consensus_api_url}")
    logger.info(f"Check Interval (s)    : {miner_check_interval}")
    logger.info("---------------------------------------------------")

    # Load khóa ký cho Miner Agent
    miner_payment_skey: Optional[ExtendedSigningKey] = None
    miner_stake_skey: Optional[ExtendedSigningKey] = None
    try:
        # Lấy thư mục base từ env hoặc settings SDK
        base_dir_agent = os.getenv("HOTKEY_BASE_DIR", getattr(sdk_settings, 'HOTKEY_BASE_DIR', 'moderntensor'))
        miner_payment_skey, miner_stake_skey = decode_hotkey_skey(
            base_dir=base_dir_agent,
            coldkey_name=miner_coldkey_name, # type: ignore
            hotkey_name=miner_hotkey_name,   # type: ignore
            password=miner_password         # type: ignore
        )
        if not miner_payment_skey:
            raise ValueError("Failed to decode miner payment signing key.")
        logger.info("Miner Agent signing keys loaded successfully.")
    except FileNotFoundError as fnf_err:
         logger.exception(f"FATAL: Could not find key files for Miner Agent: {fnf_err}. Check HOTKEY_BASE_DIR, MINER_COLDKEY_NAME2, MINER_HOTKEY_NAME2.")
         return
    except Exception as key_err:
        logger.exception(f"FATAL: Failed to load/decode keys for Miner Agent: {key_err}")
        return

    # --- Khởi tạo các tiến trình ---
    miner_agent_instance: Optional[MinerAgent] = None
    try:
        # Tạo instance MinerAgent với UID hex đã tính toán
        miner_agent_instance = MinerAgent(
            miner_uid_hex=expected_uid_hex, # <<<--- UID hex đã tính
            config=sdk_settings,
            miner_skey=miner_payment_skey, # type: ignore
            miner_stake_skey=miner_stake_skey # type: ignore
        )

        # Tạo instance Subnet1Miner với UID hex đã tính toán và ID dễ đọc
        miner_server_instance = Subnet1Miner(
            validator_url=validator_result_submit_url, # URL để gửi kết quả AI
            on_chain_uid_hex=expected_uid_hex,       # <<<--- UID hex đã tính
            host=miner_host,
            port=miner_port,
            miner_id=miner_readable_id               # <<<--- ID dễ đọc cho log server
        )

        # Chạy Miner Server (xử lý task AI) trong một thread riêng vì nó blocking
        miner_server_thread = threading.Thread(target=miner_server_instance.run, daemon=True)
        miner_server_thread.start()
        logger.info(f"Started Subnet1Miner server in background thread for '{miner_readable_id}' (UID: {expected_uid_hex})...")

        # Đợi server khởi động một chút (tùy chọn)
        await asyncio.sleep(5)

        # Chạy Miner Agent (cập nhật blockchain) trong vòng lặp async chính
        logger.info(f"Starting Miner Agent loop for UID {expected_uid_hex}...")
        # Hàm run của Agent là blocking (cho đến khi có lỗi hoặc bị dừng)
        await miner_agent_instance.run(
            validator_api_url=validator_consensus_api_url, # type: ignore
            check_interval_seconds=miner_check_interval
        )

    except Exception as e:
        logger.exception(f"An unexpected error occurred during miner process startup or execution: {e}")
    finally:
        # Dọn dẹp khi kết thúc (ví dụ đóng http client của agent)
        if miner_agent_instance:
            await miner_agent_instance.close()
        logger.info("Miner processes finished.")


# --- Điểm thực thi chính ---
if __name__ == "__main__":
    try:
        # Chạy hàm async chính
        asyncio.run(run_miner_processes())
    except KeyboardInterrupt:
        logger.info("Miner processes interrupted by user.")
    except Exception as main_err:
        logger.exception(f"Critical error running miner processes: {main_err}")