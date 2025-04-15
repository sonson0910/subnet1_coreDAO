# File: moderntensor-subnet1/scripts/run_validator2.py
# Chạy Validator instance 2, tự động suy ra UID hex từ ID cấu hình.

import os
import sys
import logging
import binascii # <<<--- Import binascii
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Dict, Any # <<<--- Thêm Dict, Any

# --- Thêm đường dẫn gốc của project vào sys.path ---
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
# -------------------------------------------------

# --- Import SDK Runner và Lớp Validator của Subnet ---
try:
    from sdk.runner import ValidatorRunner # Import lớp Runner từ SDK
    from subnet1.validator import Subnet1Validator # Import lớp Validator của subnet
    from sdk.config.settings import settings as sdk_settings # Import settings SDK
    from pycardano import Network # Import Network
except ImportError as e:
    print(f"Error: Could not import required classes. "
          f"Ensure SDK and subnet modules are accessible. Details: {e}")
    sys.exit(1)
# ---------------------------------------------------

# --- Tải biến môi trường ---
env_path = project_root / '.env'
if env_path.exists():
    print(f"Loading environment variables from: {env_path}")
    load_dotenv(dotenv_path=env_path, override=True)
# --------------------------

# --- Cấu hình Logging ---
log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(level=log_level, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)
# ------------------------

def main():
    """Hàm chính để cấu hình và chạy ValidatorRunner cho Validator 2."""
    logger.info("--- Configuring Validator Runner for Subnet 1 (Instance 2) ---")

    try:
        # --- Đọc ID validator dạng chuỗi từ .env ---
        validator_readable_id = os.getenv("SUBNET1_VALIDATOR_UID2")
        if not validator_readable_id:
            logger.error("FATAL: SUBNET1_VALIDATOR_UID2 (readable validator ID) is not set in .env.")
            sys.exit(1)

        # --- Tính toán UID hex từ ID dạng chuỗi ---
        try:
            expected_uid_bytes = validator_readable_id.encode('utf-8')
            expected_uid_hex = expected_uid_bytes.hex()
            logger.info(f"Derived On-Chain UID Hex from SUBNET1_VALIDATOR_UID2 ('{validator_readable_id}'): {expected_uid_hex}")
        except Exception as e:
            logger.error(f"FATAL: Could not encode SUBNET1_VALIDATOR_UID2 ('{validator_readable_id}') to derive UID: {e}")
            sys.exit(1)
        # -----------------------------------------

        # --- Tập hợp cấu hình cho ValidatorRunner ---
        runner_config: Dict[str, Any] = {
            "validator_class": Subnet1Validator, # Lớp validator cụ thể của subnet
            "host": os.getenv("SUBNET1_API_HOST2", "127.0.0.1"),
            "port": int(os.getenv("SUBNET1_API_PORT2", 8002)),
            "log_level": log_level_str.lower(),

            # --- Cấu hình cần để khởi tạo validator bên trong Runner ---
            # >>> SỬA ĐỔI: Sử dụng UID hex đã tính toán <<<
            "validator_uid": expected_uid_hex,
            # >>> KẾT THÚC SỬA ĐỔI <<<
            "validator_address": os.getenv("SUBNET1_VALIDATOR_ADDRESS2"),
            "validator_api_endpoint": os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT2"),
            "hotkey_base_dir": os.getenv("HOTKEY_BASE_DIR2", getattr(sdk_settings, 'HOTKEY_BASE_DIR', 'moderntensor')),
            "coldkey_name": os.getenv("SUBNET1_COLDKEY_NAME2", "validator2"), # Tên coldkey riêng cho validator 2
            "hotkey_name": os.getenv("SUBNET1_HOTKEY_NAME2"), # Tên hotkey riêng cho validator 2
            "password": os.getenv("SUBNET1_HOTKEY_PASSWORD2"), # Mật khẩu riêng cho validator 2
            "blockfrost_project_id": os.getenv("BLOCKFROST_PROJECT_ID", getattr(sdk_settings, 'BLOCKFROST_PROJECT_ID', None)),
            "network": Network.MAINNET if os.getenv("CARDANO_NETWORK", "TESTNET").upper() == "MAINNET" else Network.TESTNET,
            # Thêm các cấu hình khác nếu Subnet1Validator.__init__ cần
        }

        # --- Kiểm tra các giá trị config bắt buộc ---
        # Bây giờ validator_uid được đảm bảo tồn tại nếu đọc được ID readable
        required_keys = [
            'validator_address', 'validator_api_endpoint',
            'coldkey_name', 'hotkey_name', 'password', 'blockfrost_project_id'
        ]
        # Kiểm tra các key còn lại
        if not all(runner_config.get(k) for k in required_keys):
            missing = [k for k in required_keys if not runner_config.get(k)]
            # Thêm validator_uid nếu nó không được tính toán vì lý do nào đó (dù khó xảy ra)
            if not runner_config.get('validator_uid'): missing.append('validator_uid (derived)')
            raise ValueError(f"Missing required configurations in .env for Validator 2: {missing}")

        logger.info("Configuration loaded. Initializing ValidatorRunner...")
        # Khởi tạo Runner với config đã chuẩn bị
        runner = ValidatorRunner(runner_config)

        logger.info(f"Starting validator node '{validator_readable_id}' (UID: {expected_uid_hex}) and API server...")
        # Chạy server (blocking call)
        runner.run()

    except ValueError as e:
         logger.error(f"Configuration Error: {e}")
    except ImportError:
         logger.error("Import Error: Could not find necessary modules. Is the SDK installed correctly?")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")

# --- Điểm thực thi chính ---
if __name__ == "__main__":
    main()