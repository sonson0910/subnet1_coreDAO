# File: scripts/run_miner.py
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
from typing import Optional, Dict, Any
from rich.logging import RichHandler # <<<--- Import RichHandler

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
    from pycardano import ExtendedSigningKey, Network
    from sdk.runner import MinerRunner # <<<--- Assuming MinerRunner exists
except ImportError as e:
    print(f"Error: Could not import required classes. Details: {e}")
    print("Ensure the moderntensor SDK is installed correctly and accessible.")
    sys.exit(1)
# ---------------------------------------------------

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
env_path = project_root / '.env'
if env_path.exists():
    logger.info(f"📄 Loading environment variables from: {env_path}")
    load_dotenv(dotenv_path=env_path, override=True)
else:
    logger.warning(f"📄 Environment file (.env) not found at {env_path}.")
# --------------------------

async def run_miner_processes():
    """Hàm async để cấu hình và chạy cả Miner Server và Miner Agent."""
    logger.info("⛏️ --- Starting Miner Configuration & Processes (Instance 1) --- ⛏️")

    # === Cấu hình chung cho Miner ===
    miner_readable_id = os.getenv("SUBNET1_MINER_ID")
    if not miner_readable_id:
        logger.critical("❌ FATAL: SUBNET1_MINER_ID is not set in .env.") # Use critical
        return
    logger.info(f"🆔 Read Miner ID from .env: '{miner_readable_id}'")

    # --- Tính toán UID hex dự kiến từ ID cấu hình ---
    try:
        expected_uid_bytes = miner_readable_id.encode('utf-8')
        expected_uid_hex = expected_uid_bytes.hex()
        logger.info(f"🔑 Derived On-Chain UID (Hex): {expected_uid_hex}")
    except Exception as e:
        logger.critical(f"❌ FATAL: Could not encode SUBNET1_MINER_ID ('{miner_readable_id}') to derive UID: {e}")
        return
    # --------------------------------------------------

    # === Cấu hình cho Subnet1Miner (Xử lý Task AI) ===
    validator_result_submit_url = os.getenv("SUBNET1_VALIDATOR_URL")
    if not validator_result_submit_url:
        logger.critical("❌ FATAL: SUBNET1_VALIDATOR_URL (for AI results submission) is not set.")
        return
    miner_host = os.getenv("SUBNET1_MINER_HOST") or getattr(sdk_settings, 'DEFAULT_MINER_HOST', "0.0.0.0")
    miner_port = int(os.getenv("SUBNET1_MINER_PORT") or getattr(sdk_settings, 'DEFAULT_MINER_PORT', 9001))

    logger.info("🖥️ --- Subnet 1 Miner AI Task Server Configuration --- 🖥️")
    logger.info(f"🆔 Miner Readable ID     : [cyan]'{miner_readable_id}'[/]")
    logger.info(f"👂 Listening on          : [bold blue]{miner_host}:{miner_port}[/]")
    logger.info(f"➡️ Validator Submit URL  : [link={validator_result_submit_url}]{validator_result_submit_url}[/link]")
    logger.info("-------------------------------------------------------")

    # === Cấu hình cho MinerAgent (Cập nhật Blockchain) ===
    miner_coldkey_name = os.getenv("MINER_COLDKEY_NAME")
    miner_hotkey_name = os.getenv("MINER_HOTKEY_NAME")
    miner_password = os.getenv("MINER_HOTKEY_PASSWORD")
    validator_consensus_api_url = os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT")
    miner_check_interval = int(os.getenv("MINER_AGENT_CHECK_INTERVAL") or getattr(sdk_settings, 'MINER_AGENT_CHECK_INTERVAL', 300))

    agent_required_keys = {
        "MINER_COLDKEY_NAME": miner_coldkey_name,
        "MINER_HOTKEY_NAME": miner_hotkey_name,
        "MINER_HOTKEY_PASSWORD": miner_password,
        "SUBNET1_VALIDATOR_API_ENDPOINT": validator_consensus_api_url
    }
    missing_agent_configs = [k for k, v in agent_required_keys.items() if not v]
    if missing_agent_configs:
        logger.critical(f"❌ FATAL: Missing Miner Agent configurations in .env: {missing_agent_configs}")
        return

    logger.info("🔗 --- Miner Agent (Blockchain Interaction) Configuration --- 🔗")
    logger.info(f"🔑 Agent On-Chain UID    : [yellow]{expected_uid_hex}[/]")
    logger.info(f"🧊 Coldkey Name          : [cyan]{miner_coldkey_name}[/]")
    logger.info(f"🔥 Hotkey Name           : [cyan]{miner_hotkey_name}[/]")
    logger.info(f"🔎 Validator API (Fetch) : [link={validator_consensus_api_url}]{validator_consensus_api_url}[/link]")
    logger.info(f"⏱️ Check Interval (s)    : {miner_check_interval}")
    logger.info("------------------------------------------------------------")

    # Load khóa ký cho Miner Agent
    miner_payment_skey: Optional[ExtendedSigningKey] = None
    miner_stake_skey: Optional[ExtendedSigningKey] = None
    try:
        logger.info(f"🔑 Loading signing keys for Miner Agent (Hotkey: '{miner_hotkey_name}')...")
        base_dir_agent = os.getenv("HOTKEY_BASE_DIR") or getattr(sdk_settings, 'HOTKEY_BASE_DIR', 'moderntensor')
        miner_payment_skey, miner_stake_skey = decode_hotkey_skey(
            base_dir=base_dir_agent,
            coldkey_name=miner_coldkey_name, # type: ignore
            hotkey_name=miner_hotkey_name,   # type: ignore
            password=miner_password         # type: ignore
        )
        if not miner_payment_skey:
            # decode_hotkey_skey logs details, just raise here
            raise ValueError("Failed to decode miner payment signing key (check logs from decode_hotkey_skey).")
        logger.info("✅ Miner Agent signing keys loaded successfully.")
    except FileNotFoundError as fnf_err:
         logger.critical(f"❌ FATAL: Could not find key files for Miner Agent: {fnf_err}. Check HOTKEY_BASE_DIR, MINER_COLDKEY_NAME, MINER_HOTKEY_NAME.")
         return
    except Exception as key_err:
        logger.exception(f"💥 FATAL: Failed to load/decode keys for Miner Agent: {key_err}")
        return

    # --- Khởi tạo các tiến trình --- 
    miner_agent_instance: Optional[MinerAgent] = None
    try:
        logger.info("🛠️ Initializing Miner Agent instance...")
        miner_agent_instance = MinerAgent(
            miner_uid_hex=expected_uid_hex,
            config=sdk_settings,
            miner_skey=miner_payment_skey, # type: ignore
            miner_stake_skey=miner_stake_skey # type: ignore
        )
        logger.info("✅ Miner Agent instance initialized.")

        logger.info(f"🛠️ Initializing Subnet1Miner Server ('{miner_readable_id}')...")
        miner_server_instance = Subnet1Miner(
            validator_url=validator_result_submit_url,
            on_chain_uid_hex=expected_uid_hex,
            host=miner_host,
            port=miner_port,
            miner_id=miner_readable_id
        )
        logger.info("✅ Subnet1Miner Server instance initialized.")

        # Chạy Miner Server trong thread riêng
        miner_server_thread = threading.Thread(target=miner_server_instance.run, daemon=True)
        miner_server_thread.start()
        logger.info(f"🧵 Started Subnet1Miner server in background thread for '{miner_readable_id}' (UID: {expected_uid_hex})...")

        await asyncio.sleep(5) # Chờ server khởi động

        # Chạy Miner Agent loop
        logger.info(f"▶️ Starting Miner Agent main loop for UID {expected_uid_hex}...")
        await miner_agent_instance.run(
            validator_api_url=validator_consensus_api_url, # type: ignore
            check_interval_seconds=miner_check_interval
        )
        # Agent run loop finished (normally doesn't unless error or stopped)
        logger.info("⏹️ Miner Agent main loop finished.")

    except Exception as e:
        logger.exception(f"💥 An unexpected error occurred during miner process startup or execution: {e}")
    finally:
        # Dọn dẹp
        if miner_agent_instance:
            await miner_agent_instance.close()
        logger.info("🛑 Miner processes cleanup finished.")

# --- Điểm thực thi chính --- 
if __name__ == "__main__":
    try:
        logger.info("🚦 Starting main asynchronous execution...")
        asyncio.run(run_miner_processes())
    except KeyboardInterrupt:
        logger.info("👋 Miner processes interrupted by user (Ctrl+C).")
    except Exception as main_err:
        logger.exception(f"💥 Critical error in main execution block: {main_err}")
    finally:
        logger.info("🏁 Miner script finished.")