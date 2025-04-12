# Trong file: scripts/run_miner.py

import os
import sys
import logging
import asyncio # Thêm asyncio
import threading # Có thể dùng thread nếu muốn chạy song song blocking
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
# --- Thêm đường dẫn gốc của project vào sys.path ---
# (Giữ nguyên)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# --- Import các lớp cần thiết ---
try:
    from subnet1.miner import Subnet1Miner
    # Import MinerAgent từ SDK
    from sdk.agent.miner_agent import MinerAgent
    # Import các thành phần khác từ SDK nếu cần (keymanager, settings,...)
    from sdk.config.settings import settings as sdk_settings
    from sdk.keymanager.decryption_utils import decode_hotkey_skey
    from pycardano import ExtendedSigningKey # Import ExtendedSigningKey
except ImportError as e:
    print(f"Error: Could not import required classes. Details: {e}")
    sys.exit(1)

# --- Tải biến môi trường (.env) ---
# (Giữ nguyên)
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# --- Cấu hình Logging ---
# (Giữ nguyên)
log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(level=log_level, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

# --- Hàm chạy chính (Sửa đổi) ---
async def run_miner_processes():
    """Hàm async để cấu hình và chạy cả Miner Server và Miner Agent."""

    # === Cấu hình cho Subnet1Miner (Xử lý Task AI) ===
    validator_result_submit_url = os.getenv("SUBNET1_VALIDATOR_URL") # URL validator nhận kết quả AI
    if not validator_result_submit_url:
        logger.error("FATAL: SUBNET1_VALIDATOR_URL (for AI results) is not set.")
        return
    miner_host = os.getenv("SUBNET1_MINER_HOST", "0.0.0.0")
    miner_port = int(os.getenv("SUBNET1_MINER_PORT", 9001))
    miner_id_for_server = os.getenv("SUBNET1_MINER_ID", f"subnet1_miner_{miner_port}") # ID dùng trong log của server

    logger.info("--- Subnet 1 Miner AI Task Server Configuration ---")
    logger.info(f"Miner ID (Server Log) : {miner_id_for_server}")
    logger.info(f"Listening on          : {miner_host}:{miner_port}")
    logger.info(f"Validator Submit URL  : {validator_result_submit_url}")
    logger.info("-------------------------------------------------")

    # === Cấu hình cho MinerAgent (Cập nhật Blockchain) ===
    miner_uid_hex = miner_id_for_server.encode('utf-8')
    miner_coldkey_name = os.getenv("MINER_COLDKEY_NAME")
    miner_hotkey_name = os.getenv("MINER_HOTKEY_NAME")
    miner_password = os.getenv("MINER_HOTKEY_PASSWORD")
    # Lấy URL của validator để fetch kết quả consensus
    validator_consensus_api_url = os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT") # Ví dụ: http://127.0.0.1:8001
    miner_check_interval = int(os.getenv("MINER_AGENT_CHECK_INTERVAL", 300)) # Giây

    # Kiểm tra config agent
    if not all([miner_uid_hex, miner_coldkey_name, miner_hotkey_name, miner_password, validator_consensus_api_url]):
        missing_agent_configs = [
            k for k, v in {
                "MINER_UID_HEX": miner_uid_hex,
                "MINER_COLDKEY_NAME": miner_coldkey_name,
                "MINER_HOTKEY_NAME": miner_hotkey_name,
                "MINER_HOTKEY_PASSWORD": miner_password,
                "VALIDATOR_CONSENSUS_API_URL": validator_consensus_api_url
            }.items() if not v
        ]
        logger.error(f"FATAL: Missing Miner Agent configurations in .env: {missing_agent_configs}")
        return

    logger.info("--- Miner Agent (Blockchain Update) Configuration ---")
    logger.info(f"Miner UID (Hex)       : {miner_uid_hex}")
    logger.info(f"Coldkey Name          : {miner_coldkey_name}")
    logger.info(f"Hotkey Name           : {miner_hotkey_name}")
    logger.info(f"Validator Result API  : {validator_consensus_api_url}")
    logger.info(f"Check Interval (s)    : {miner_check_interval}")
    logger.info("---------------------------------------------------")

    # Load khóa ký cho Miner Agent
    miner_payment_skey: Optional[ExtendedSigningKey] = None
    miner_stake_skey: Optional[ExtendedSigningKey] = None
    try:
        base_dir_agent = os.getenv("HOTKEY_BASE_DIR", "moderntensor") # Dùng thư mục riêng hoặc chung
        miner_payment_skey, miner_stake_skey = decode_hotkey_skey(
            base_dir=base_dir_agent,
            coldkey_name=miner_coldkey_name,
            hotkey_name=miner_hotkey_name,
            password=miner_password
        )
        if not miner_payment_skey: raise ValueError("Failed to decode miner payment key")
        logger.info("Miner Agent signing keys loaded successfully.")
    except Exception as key_err:
        logger.exception(f"FATAL: Failed to load keys for Miner Agent: {key_err}")
        return

    # --- Khởi tạo các tiến trình ---
    miner_agent_instance: Optional[MinerAgent] = None
    try:
        # Tạo instance MinerAgent
        miner_agent_instance = MinerAgent(
            miner_uid_hex=miner_uid_hex,
            config=sdk_settings, # Truyền đối tượng settings SDK
            miner_skey=miner_payment_skey, # type: ignore
            miner_stake_skey=miner_stake_skey # type: ignore
        )

        # Tạo instance Subnet1Miner (cần chạy trong thread riêng vì nó blocking)
        miner_server_instance = Subnet1Miner(
            validator_url=validator_result_submit_url, # URL để gửi kết quả AI
            host=miner_host,
            port=miner_port,
            miner_id=miner_id_for_server # ID cho log server
        )

        # Chạy Miner Server trong một thread riêng
        miner_server_thread = threading.Thread(target=miner_server_instance.run, daemon=True)
        miner_server_thread.start()
        logger.info(f"Started Subnet1Miner server in background thread for '{miner_id_for_server}'...")

        # Đợi server khởi động một chút (tùy chọn)
        await asyncio.sleep(5)

        # Chạy Miner Agent trong vòng lặp async chính
        logger.info(f"Starting Miner Agent loop for UID {miner_uid_hex}...")
        await miner_agent_instance.run(
            validator_api_url=validator_consensus_api_url,
            check_interval_seconds=miner_check_interval
        ) # Blocking call (cho đến khi có lỗi hoặc bị dừng)

    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
    finally:
        # Dọn dẹp khi kết thúc (ví dụ đóng client của agent)
        if miner_agent_instance:
            await miner_agent_instance.close()
        logger.info("Miner processes finished.")


if __name__ == "__main__":
    try:
        asyncio.run(run_miner_processes())
    except KeyboardInterrupt:
        logger.info("Miner processes interrupted by user.")