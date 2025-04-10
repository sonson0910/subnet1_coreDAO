import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# --- Thêm đường dẫn gốc của project vào sys.path ---
# Điều này cần thiết để import các module từ thư mục 'subnet1'
# khi chạy script từ thư mục 'scripts' hoặc thư mục gốc.
project_root = Path(__file__).parent.parent # Lấy thư mục gốc (moderntensor-subnet1)
sys.path.insert(0, str(project_root))
# -------------------------------------------------

# Import lớp Miner của subnet này
try:
    from subnet1.miner import Subnet1Miner
except ImportError as e:
    print(f"Error: Could not import Subnet1Miner. "
          f"Ensure you are in the correct directory and the SDK is installed. Details: {e}")
    sys.exit(1)

# --- Tải biến môi trường từ file .env ở thư mục gốc ---
env_path = project_root / '.env'
if env_path.exists():
    print(f"Loading environment variables from: {env_path}")
    load_dotenv(dotenv_path=env_path, override=True)
else:
    print(f"Warning: .env file not found at {env_path}. Using default values or existing environment variables.")
# ------------------------------------------------------

# --- Cấu hình Logging ---
log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(level=log_level, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)
# ------------------------

def run_miner_instance():
    """Hàm chính để cấu hình và chạy miner."""

    # --- Lấy cấu hình từ biến môi trường ---
    # **QUAN TRỌNG**: URL này phải trỏ đúng đến endpoint API của validator
    # mà miner cần gửi kết quả về (thường là /v1/miner/submit_result)
    validator_url = os.getenv("SUBNET1_VALIDATOR_URL")
    if not validator_url:
        logger.error("FATAL: Environment variable SUBNET1_VALIDATOR_URL is not set. Miner cannot report results.")
        sys.exit(1)

    miner_host = os.getenv("SUBNET1_MINER_HOST", "0.0.0.0") # Lắng nghe trên tất cả interfaces
    miner_port = int(os.getenv("SUBNET1_MINER_PORT", 9001)) # Chọn cổng cho miner subnet 1
    miner_id = os.getenv("SUBNET1_MINER_ID", f"subnet1_miner_{miner_port}") # Tạo ID mặc định

    logger.info("--- Subnet 1 Miner Configuration ---")
    logger.info(f"Miner ID          : {miner_id}")
    logger.info(f"Listening on      : {miner_host}:{miner_port}")
    logger.info(f"Validator Endpoint: {validator_url}")
    logger.info(f"Log Level         : {log_level_str}")
    logger.info("------------------------------------")

    # --- Khởi tạo và chạy Miner ---
    try:
        miner_instance = Subnet1Miner(
            validator_url=validator_url,
            host=miner_host,
            port=miner_port,
            miner_id=miner_id
        )

        # Phương thức run() được kế thừa từ BaseMiner trong SDK
        # Nó sẽ khởi động server uvicorn/FastAPI
        logger.info(f"Starting Subnet1Miner server for '{miner_id}'...")
        miner_instance.run() # Blocking call

    except ImportError as e:
         # Bắt lỗi nếu import từ SDK thất bại (do chưa cài SDK đúng cách)
         logger.error(f"ImportError: Could not run miner. Is the 'moderntensor' SDK installed correctly? Details: {e}")
    except OSError as e:
         logger.error(f"OS Error starting miner on {miner_host}:{miner_port}. Is the port already in use? Details: {e}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred while starting or running the miner: {e}")

if __name__ == "__main__":
    run_miner_instance()