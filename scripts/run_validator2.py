# File: moderntensor-subnet1/scripts/run_validator2.py
# Chạy Validator instance 2, tự động suy ra UID hex từ ID cấu hình.

import os
import sys
import logging
import binascii
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from rich.logging import RichHandler # <<< Import RichHandler

# --- Thêm đường dẫn gốc của project vào sys.path ---
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
# -------------------------------------------------

# --- Import SDK Runner và Lớp Validator của Subnet ---
try:
    from sdk.runner import ValidatorRunner
    from subnet1.validator import Subnet1Validator
    from sdk.config.settings import settings as sdk_settings
    from pycardano import Network
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

def main():
    """Hàm chính để cấu hình và chạy ValidatorRunner cho Validator 2."""
    logger.info("🚀 --- Starting Validator Configuration ([bold yellow]Instance 2[/]) --- 🚀")

    try:
        # --- Đọc ID validator 2 dạng chuỗi từ .env --- 
        validator_readable_id = os.getenv("SUBNET1_VALIDATOR_UID2")
        if not validator_readable_id:
            logger.critical("❌ FATAL: SUBNET1_VALIDATOR_UID2 is not set in .env.")
            sys.exit(1)
        logger.info(f"🆔 Read Validator ID (Instance 2) from .env: '{validator_readable_id}'")

        # --- Tính toán UID hex từ ID dạng chuỗi --- 
        try:
            expected_uid_bytes = validator_readable_id.encode('utf-8')
            expected_uid_hex = expected_uid_bytes.hex()
            logger.info(f"🔑 Derived On-Chain UID (Hex): {expected_uid_hex}")
        except Exception as e:
            logger.critical(f"❌ FATAL: Could not encode SUBNET1_VALIDATOR_UID2 ('{validator_readable_id}') to derive UID: {e}")
            sys.exit(1)
        # -----------------------------------------

        # --- Tập hợp cấu hình cho ValidatorRunner (Instance 2) --- 
        logger.info("⚙️ Gathering configuration for ValidatorRunner (Instance 2)...")
        runner_config: Dict[str, Any] = {
            "validator_class": Subnet1Validator,
            # Sử dụng các biến môi trường có hậu tố 2
            "host": os.getenv("SUBNET1_API_HOST2") or getattr(sdk_settings, 'DEFAULT_API_HOST', "127.0.0.1"),
            "port": int(os.getenv("SUBNET1_API_PORT2") or getattr(sdk_settings, 'DEFAULT_API_PORT', 8002)), # Port mặc định khác
            "log_level": log_level_str.lower(),
            "validator_uid": expected_uid_hex,
            "validator_address": os.getenv("SUBNET1_VALIDATOR_ADDRESS2"),
            "validator_api_endpoint": os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT2"),
            "hotkey_base_dir": os.getenv("HOTKEY_BASE_DIR2") or getattr(sdk_settings, 'HOTKEY_BASE_DIR', 'moderntensor'), # Có thể base dir khác?
            "coldkey_name": os.getenv("SUBNET1_COLDKEY_NAME2") or getattr(sdk_settings, 'DEFAULT_COLDKEY_NAME', "validator2"), # Coldkey khác
            "hotkey_name": os.getenv("SUBNET1_HOTKEY_NAME2"),
            "password": os.getenv("SUBNET1_HOTKEY_PASSWORD2"),
            "blockfrost_project_id": os.getenv("BLOCKFROST_PROJECT_ID") or getattr(sdk_settings, 'BLOCKFROST_PROJECT_ID', None),
            "network": Network.MAINNET if (os.getenv("CARDANO_NETWORK") or getattr(sdk_settings, 'CARDANO_NETWORK', 'TESTNET')).upper() == "MAINNET" else Network.TESTNET,
        }
        logger.debug(f"⚙️ Runner Config (Instance 2) assembled: {runner_config}")

        # --- Kiểm tra các giá trị config bắt buộc --- 
        required_keys = [
            'validator_address', 'validator_api_endpoint',
            'coldkey_name', 'hotkey_name', 'password', 'blockfrost_project_id',
            'validator_uid'
        ]
        missing = [k for k in required_keys if not runner_config.get(k)]
        if missing:
            logger.critical(f"❌ FATAL: Missing required configurations in .env for Validator 2: {missing}.")
            sys.exit(1)

        logger.info("✅ Configuration validated. Initializing ValidatorRunner (Instance 2)...")
        runner = ValidatorRunner(runner_config)

        logger.info(f"🚀 Starting Validator Node '{validator_readable_id}' ([bold yellow]Instance 2[/], UID: {expected_uid_hex}) and API server...")
        runner.run()

    except ValueError as e:
         logger.critical(f"❌ Configuration Error (Instance 2): {e}")
         sys.exit(1)
    except Exception as e:
        logger.exception(f"💥 An unexpected critical error occurred (Instance 2): {e}")
        sys.exit(1)

# --- Điểm thực thi chính --- 
if __name__ == "__main__":
    main()