# File: moderntensor-subnet1/scripts/run_validator3.py
# Chạy Validator instance 3, tự động suy ra UID hex từ ID cấu hình.

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
    from mt_aptos.runner import ValidatorRunner
    from subnet1.validator import Subnet1Validator
    from mt_aptos.config.settings import settings as sdk_settings
    from pycardano import Network
except ImportError as e:
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
    """Hàm chính để cấu hình và chạy ValidatorRunner cho Validator 3."""
    logger.info("🚀 --- Starting Validator Configuration ([bold green]Instance 3[/]) --- 🚀")

    try:
        # --- Đọc ID validator 3 dạng chuỗi từ .env --- 
        validator_readable_id = os.getenv("SUBNET1_VALIDATOR_UID3")
        if not validator_readable_id:
            logger.critical("❌ FATAL: SUBNET1_VALIDATOR_UID3 is not set in .env.")
            sys.exit(1)
        logger.info(f"🆔 Read Validator ID (Instance 3) from .env: '{validator_readable_id}'")

        # --- Tính toán UID hex từ ID dạng chuỗi --- 
        try:
            expected_uid_bytes = validator_readable_id.encode('utf-8')
            expected_uid_hex = expected_uid_bytes.hex()
            logger.info(f"🔑 Derived On-Chain UID (Hex): {expected_uid_hex}")
        except Exception as e:
            logger.critical(f"❌ FATAL: Could not encode SUBNET1_VALIDATOR_UID3 ('{validator_readable_id}') to derive UID: {e}")
            sys.exit(1)
        # -----------------------------------------

        # --- Tập hợp cấu hình cho ValidatorRunner (Instance 3) --- 
        logger.info("⚙️ Gathering configuration for ValidatorRunner (Instance 3)...")
        runner_config: Dict[str, Any] = {
            "validator_class": Subnet1Validator,
            # Sử dụng các biến môi trường có hậu tố 3
            "host": os.getenv("SUBNET1_API_HOST3") or getattr(sdk_settings, 'DEFAULT_API_HOST', "127.0.0.1"),
            "port": int(os.getenv("SUBNET1_API_PORT3") or getattr(sdk_settings, 'DEFAULT_API_PORT', 8003)), # Port mặc định khác
            "log_level": log_level_str.lower(),
            "validator_uid": expected_uid_hex,
            "validator_address": os.getenv("SUBNET1_VALIDATOR_ADDRESS3"),
            "validator_api_endpoint": os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT3"),
            "hotkey_base_dir": os.getenv("HOTKEY_BASE_DIR3") or getattr(sdk_settings, 'HOTKEY_BASE_DIR', 'moderntensor'),
            "coldkey_name": os.getenv("SUBNET1_COLDKEY_NAME3") or getattr(sdk_settings, 'DEFAULT_COLDKEY_NAME', "validator3"),
            "hotkey_name": os.getenv("SUBNET1_HOTKEY_NAME3"),
            "password": os.getenv("SUBNET1_HOTKEY_PASSWORD3"),
            "blockfrost_project_id": os.getenv("BLOCKFROST_PROJECT_ID") or getattr(sdk_settings, 'BLOCKFROST_PROJECT_ID', None),
            "network": Network.MAINNET if (os.getenv("CARDANO_NETWORK") or getattr(sdk_settings, 'CARDANO_NETWORK', 'TESTNET')).upper() == "MAINNET" else Network.TESTNET,
        }
        logger.debug(f"⚙️ Runner Config (Instance 3) assembled: {runner_config}")

        # --- Kiểm tra các giá trị config bắt buộc --- 
        required_keys = [
            'validator_address', 'validator_api_endpoint',
            'coldkey_name', 'hotkey_name', 'password', 'blockfrost_project_id',
            'validator_uid'
        ]
        missing = [k for k in required_keys if not runner_config.get(k)]
        if missing:
            logger.critical(f"❌ FATAL: Missing required configurations in .env for Validator 3: {missing}.")
            sys.exit(1)

        logger.info("✅ Configuration validated. Initializing ValidatorRunner (Instance 3)...")
        runner = ValidatorRunner(runner_config)

        logger.info(f"🚀 Starting Validator Node '{validator_readable_id}' ([bold green]Instance 3[/], UID: {expected_uid_hex}) and API server...")
        runner.run()

    except ValueError as e:
         logger.critical(f"❌ Configuration Error (Instance 3): {e}")
         sys.exit(1)
    except Exception as e:
        logger.exception(f"💥 An unexpected critical error occurred (Instance 3): {e}")
        sys.exit(1)

# --- Điểm thực thi chính --- 
if __name__ == "__main__":
    main()