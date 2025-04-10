# File: moderntensor-subnet1/scripts/run_validator.py
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# --- Thêm đường dẫn gốc của project vào sys.path ---
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
# -------------------------------------------------

# --- Import SDK Runner và Lớp Validator của Subnet ---
try:
    from sdk.runner import ValidatorRunner # Import lớp Runner mới từ SDK
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
    """Hàm chính để cấu hình và chạy ValidatorRunner."""
    logger.info("--- Configuring Validator Runner for Subnet 1 ---")

    try:
        # --- Tập hợp cấu hình cho ValidatorRunner ---
        runner_config = {
            "validator_class": Subnet1Validator, # << Truyền lớp validator cụ thể
            "host": os.getenv("SUBNET1_API_HOST", "127.0.0.1"),
            "port": int(os.getenv("SUBNET1_API_PORT", 8001)),
            "log_level": log_level_str.lower(),

            # Cấu hình cần để khởi tạo validator bên trong Runner
            "validator_uid": os.getenv("SUBNET1_VALIDATOR_UID"),
            "validator_address": os.getenv("SUBNET1_VALIDATOR_ADDRESS"),
            "validator_api_endpoint": os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT"),
            "hotkey_base_dir": os.getenv("HOTKEY_BASE_DIR", getattr(sdk_settings, 'HOTKEY_BASE_DIR', 'moderntensor')),
            "coldkey_name": os.getenv("SUBNET1_COLDKEY_NAME"),
            "hotkey_name": os.getenv("SUBNET1_HOTKEY_NAME"),
            "password": os.getenv("SUBNET1_HOTKEY_PASSWORD"),
            "blockfrost_project_id": os.getenv("BLOCKFROST_PROJECT_ID", getattr(sdk_settings, 'BLOCKFROST_PROJECT_ID', None)),
            "network": Network.MAINNET if os.getenv("CARDANO_NETWORK", "TESTNET").upper() == "MAINNET" else Network.TESTNET,
            # Thêm các cấu hình khác nếu Subnet1Validator.__init__ cần
        }

        # Kiểm tra các giá trị config bắt buộc
        required_keys = [
            'validator_uid', 'validator_address', 'validator_api_endpoint',
            'coldkey_name', 'hotkey_name', 'password', 'blockfrost_project_id'
        ]
        if not all(runner_config.get(k) for k in required_keys):
            missing = [k for k in required_keys if not runner_config.get(k)]
            raise ValueError(f"Missing required configurations in .env: {missing}")

        logger.info("Configuration loaded. Initializing ValidatorRunner...")
        runner = ValidatorRunner(runner_config)

        logger.info("Starting validator node and API server...")
        runner.run() # Khởi chạy Uvicorn server và vòng lặp nền

    except ValueError as e:
         logger.error(f"Configuration Error: {e}")
    except ImportError:
         logger.error("Import Error: Could not find necessary modules. Is the SDK installed correctly?")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()