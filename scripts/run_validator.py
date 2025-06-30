# File: moderntensor-subnet1/scripts/run_validator.py
# Chạy Validator instance 1, tự động suy ra UID hex từ ID cấu hình.

import os
import sys
import logging
import binascii # <<<--- Import binascii
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Dict, Any # <<<--- Thêm Dict, Any
from rich.logging import RichHandler # <<<--- Import RichHandler

# --- Thêm đường dẫn gốc của project vào sys.path ---
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
# -------------------------------------------------

# --- Import SDK Runner và Lớp Validator của Subnet ---
try:
    from mt_aptos.runner import ValidatorRunner
    from subnet1.validator import Subnet1Validator
    from mt_aptos.config.settings import settings as sdk_settings
except ImportError as e:
    # Cannot use logger here as it's defined later
    print(f"❌ FATAL: Import Error: {e}")
    sys.exit(1)
# ---------------------------------------------------

# --- Tải biến môi trường ---
env_path = project_root / '.env'

# --- Cấu hình Logging với RichHandler ---
log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)

# Bỏ logging.basicConfig()
# Thay vào đó, cấu hình handler và formatter
rich_handler = RichHandler(
    show_time=True,
    show_level=True,
    show_path=False, # Không hiển thị đường dẫn file cho gọn
    markup=True, # Cho phép dùng markup của Rich trong log
    rich_tracebacks=True, # Traceback đẹp hơn
    log_time_format="[%Y-%m-%d %H:%M:%S]" # Định dạng thời gian
)

logging.basicConfig(
    level=log_level,
    format="%(message)s", # Chỉ cần message vì RichHandler tự thêm các phần khác
    datefmt="[%X]", # datefmt này sẽ bị RichHandler ghi đè, nhưng để đây cho chuẩn
    handlers=[rich_handler]
)

logger = logging.getLogger(__name__)
# ------------------------

# --- Tải biến môi trường (sau khi logger được cấu hình) ---
if env_path.exists():
    logger.info(f"📄 Loading environment variables from: {env_path}") # Use logger
    load_dotenv(dotenv_path=env_path, override=True)
else:
    logger.warning(f"📄 Environment file (.env) not found at {env_path}. Using default settings or environment variables.")
# --------------------------

def main():
    """Hàm chính để cấu hình và chạy ValidatorRunner cho Validator 1."""
    logger.info("🚀 --- Starting Validator Configuration (Instance 1) --- 🚀")

    try:
        # --- Đọc ID validator dạng chuỗi từ .env ---
        validator_readable_id = os.getenv("SUBNET1_VALIDATOR_UID")
        if not validator_readable_id:
            # Sử dụng logger.critical cho lỗi nghiêm trọng dừng chương trình
            logger.critical("❌ FATAL: SUBNET1_VALIDATOR_UID (readable validator ID) is not set in .env. Cannot continue.")
            sys.exit(1)
        logger.info(f"🆔 Read Validator ID from .env: '{validator_readable_id}'")

        # --- Tính toán UID hex từ ID dạng chuỗi --- 
        try:
            expected_uid_bytes = validator_readable_id.encode('utf-8')
            expected_uid_hex = expected_uid_bytes.hex()
            logger.info(f"🔑 Derived On-Chain UID (Hex): {expected_uid_hex}")
        except Exception as e:
            logger.critical(f"❌ FATAL: Could not encode SUBNET1_VALIDATOR_UID ('{validator_readable_id}') to derive UID: {e}")
            sys.exit(1)
        # -----------------------------------------

        # --- Tập hợp cấu hình cho ValidatorRunner --- 
        logger.info("⚙️ Gathering configuration for ValidatorRunner...")
        runner_config: Dict[str, Any] = {
            "validator_class": Subnet1Validator, # Lớp validator cụ thể của subnet
            "host": os.getenv("SUBNET1_API_HOST", "127.0.0.1"),
            "port": int(os.getenv("SUBNET1_API_PORT", 8001)),
            "log_level": log_level_str.lower(), # Truyền log level đã parse

            # --- Cấu hình cần để khởi tạo validator bên trong Runner ---
            "validator_uid": expected_uid_hex, # UID hex đã tính toán
            "validator_address": os.getenv("SUBNET1_VALIDATOR_ADDRESS"),
            "validator_api_endpoint": os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT"),
            "hotkey_base_dir": os.getenv("HOTKEY_BASE_DIR", getattr(sdk_settings, 'HOTKEY_BASE_DIR', 'moderntensor')),
            "coldkey_name": os.getenv("SUBNET1_COLDKEY_NAME", "validator1"), # Tên coldkey riêng
            "hotkey_name": os.getenv("SUBNET1_HOTKEY_NAME"), # Tên hotkey riêng
            "password": os.getenv("SUBNET1_HOTKEY_PASSWORD"), # Mật khẩu riêng
            "aptos_node_url": os.getenv("APTOS_NODE_URL", getattr(sdk_settings, 'APTOS_TESTNET_URL', 'https://fullnode.testnet.aptoslabs.com/v1')),
            "aptos_faucet_url": os.getenv("APTOS_FAUCET_URL", getattr(sdk_settings, 'APTOS_FAUCET_URL', 'https://faucet.testnet.aptoslabs.com')),
            "contract_address": os.getenv("APTOS_CONTRACT_ADDRESS", getattr(sdk_settings, 'CONTRACT_ADDRESS', None)),
            # Thêm các cấu hình khác nếu Subnet1Validator.__init__ cần
        }
        logger.debug(f"⚙️ Runner Config assembled: {runner_config}") # Log config chi tiết ở DEBUG level

        # --- Kiểm tra các giá trị config bắt buộc --- 
        required_keys = [
            'validator_address', 'validator_api_endpoint',
            'coldkey_name', 'hotkey_name', 'password', 'aptos_node_url',
            'validator_uid' # Đã được kiểm tra gián tiếp ở trên
        ]
        missing = [k for k in required_keys if not runner_config.get(k)]
        if missing:
            # Không dùng ValueError mà log lỗi nghiêm trọng và thoát
            logger.critical(f"❌ FATAL: Missing required configurations in .env for Validator 1: {missing}. Cannot continue.")
            sys.exit(1)

        logger.info("✅ Configuration validated. Initializing ValidatorRunner...")
        # Khởi tạo Runner với config đã chuẩn bị
        runner = ValidatorRunner(runner_config)

        logger.info(f"🚀 Starting Validator Node '{validator_readable_id}' (UID: {expected_uid_hex}) and API server...")
        # Chạy server (blocking call)
        runner.run()

    except ValueError as e: # Có thể bắt các lỗi cụ thể hơn nếu cần
         logger.critical(f"❌ Configuration Error: {e}") # Dùng critical nếu lỗi config làm dừng chương trình
         sys.exit(1)
    except Exception as e:
        # Sử dụng logger.exception để log cả traceback
        logger.exception(f"💥 An unexpected critical error occurred: {e}")
        sys.exit(1)

# --- Điểm thực thi chính --- 
if __name__ == "__main__":
    main()