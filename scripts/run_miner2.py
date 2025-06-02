# File: scripts/run_miner2.py
# Chạy cả Miner Server (xử lý task AI) và Miner Agent (cập nhật blockchain) for Instance 2
# Sử dụng SUBNET1_MINER_ID2 để tự động suy ra UID hex on-chain.

import os
import sys
import logging
import asyncio
import threading
import binascii
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from rich.logging import RichHandler # <<< Import RichHandler

# --- Thêm đường dẫn gốc của project vào sys.path ---
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
# -------------------------------------------------

# --- Import các lớp cần thiết --- 
try:
    from subnet1.miner import Subnet1Miner
    from mt_aptos.agent.miner_agent import MinerAgent
    from mt_aptos.config.settings import settings as sdk_settings
    from mt_aptos.keymanager.decryption_utils import decode_hotkey_skey
    from pycardano import ExtendedSigningKey, Network
    # Giả sử không cần MinerRunner riêng cho script này?
except ImportError as e:
    print(f"❌ FATAL: Import Error: {e}")
    sys.exit(1)
# ---------------------------------------------------

# --- Tải biến môi trường (.env) ---
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

async def run_miner_processes():
    """Hàm async để cấu hình và chạy cả Miner Server và Miner Agent cho Instance 2."""
    logger.info("⛏️ --- Starting Miner Configuration & Processes ([bold yellow]Instance 2[/]) --- ⛏️")

    # === Cấu hình chung cho Miner (Instance 2) ===
    miner_readable_id = os.getenv("SUBNET1_MINER_ID2")
    if not miner_readable_id:
        logger.critical("❌ FATAL: SUBNET1_MINER_ID2 is not set in .env.")
        return
    logger.info(f"🆔 Read Miner ID (Instance 2) from .env: '{miner_readable_id}'")

    # --- Tính toán UID hex ---
    try:
        expected_uid_bytes = miner_readable_id.encode('utf-8')
        expected_uid_hex = expected_uid_bytes.hex()
        logger.info(f"🔑 Derived On-Chain UID (Hex): {expected_uid_hex}")
    except Exception as e:
        logger.critical(f"❌ FATAL: Could not encode SUBNET1_MINER_ID2 ('{miner_readable_id}') to derive UID: {e}")
        return
    # -------------------------

    # === Cấu hình cho Subnet1Miner (Instance 2) ===
    validator_result_submit_url = os.getenv("SUBNET1_VALIDATOR_URL2") # URL Validator 2
    if not validator_result_submit_url:
        logger.critical("❌ FATAL: SUBNET1_VALIDATOR_URL2 (for AI results submission) is not set.")
        return
    miner_host = os.getenv("SUBNET1_MINER_HOST2") or getattr(sdk_settings, 'DEFAULT_MINER_HOST', "0.0.0.0")
    miner_port = int(os.getenv("SUBNET1_MINER_PORT2") or getattr(sdk_settings, 'DEFAULT_MINER_PORT', 9002))

    logger.info("🖥️ --- Subnet 1 Miner AI Task Server Configuration ([bold yellow]Instance 2[/]) --- 🖥️")
    logger.info(f"🆔 Miner Readable ID     : [cyan]'{miner_readable_id}'[/]")
    logger.info(f"👂 Listening on          : [bold blue]{miner_host}:{miner_port}[/]")
    logger.info(f"➡️ Validator Submit URL  : [link={validator_result_submit_url}]{validator_result_submit_url}[/link]")
    logger.info("-------------------------------------------------------------")

    # === Cấu hình cho MinerAgent (Instance 2) ===
    miner_coldkey_name = os.getenv("MINER_COLDKEY_NAME2")
    miner_hotkey_name = os.getenv("MINER_HOTKEY_NAME2")
    miner_password = os.getenv("MINER_HOTKEY_PASSWORD2")
    validator_consensus_api_url = os.getenv("SUBNET1_VALIDATOR_API_ENDPOINT2") # API Validator 2
    miner_check_interval = int(os.getenv("MINER_AGENT_CHECK_INTERVAL") or getattr(sdk_settings, 'MINER_AGENT_CHECK_INTERVAL', 300))

    agent_required_keys = {
        "MINER_COLDKEY_NAME2": miner_coldkey_name,
        "MINER_HOTKEY_NAME2": miner_hotkey_name,
        "MINER_HOTKEY_PASSWORD2": miner_password,
        "SUBNET1_VALIDATOR_API_ENDPOINT2": validator_consensus_api_url
    }
    missing_agent_configs = [k for k, v in agent_required_keys.items() if not v]
    if missing_agent_configs:
        logger.critical(f"❌ FATAL: Missing Miner Agent configurations in .env for Instance 2: {missing_agent_configs}")
        return

    logger.info("🔗 --- Miner Agent (Blockchain Interaction) Configuration ([bold yellow]Instance 2[/]) --- 🔗")
    logger.info(f"🔑 Agent On-Chain UID    : [yellow]{expected_uid_hex}[/]")
    logger.info(f"🧊 Coldkey Name          : [cyan]{miner_coldkey_name}[/]")
    logger.info(f"🔥 Hotkey Name           : [cyan]{miner_hotkey_name}[/]")
    logger.info(f"🔎 Validator API (Fetch) : [link={validator_consensus_api_url}]{validator_consensus_api_url}[/link]")
    logger.info(f"⏱️ Check Interval (s)    : {miner_check_interval}")
    logger.info("----------------------------------------------------------------------")

    # Load khóa ký cho Miner Agent (Instance 2)
    miner_payment_skey: Optional[ExtendedSigningKey] = None
    miner_stake_skey: Optional[ExtendedSigningKey] = None
    try:
        logger.info(f"🔑 Loading signing keys for Miner Agent (Instance 2, Hotkey: '{miner_hotkey_name}')...")
        base_dir_agent = os.getenv("HOTKEY_BASE_DIR") or getattr(sdk_settings, 'HOTKEY_BASE_DIR', 'moderntensor') # Giả sử base dir chung
        miner_payment_skey, miner_stake_skey = decode_hotkey_skey(
            base_dir=base_dir_agent,
            coldkey_name=miner_coldkey_name, # type: ignore
            hotkey_name=miner_hotkey_name,   # type: ignore
            password=miner_password         # type: ignore
        )
        if not miner_payment_skey:
            raise ValueError("Failed to decode miner payment signing key (check logs).")
        logger.info("✅ Miner Agent (Instance 2) signing keys loaded successfully.")
    except FileNotFoundError as fnf_err:
         logger.critical(f"❌ FATAL: Could not find key files for Miner Agent (Instance 2): {fnf_err}. Check base_dir, MINER_COLDKEY_NAME2, MINER_HOTKEY_NAME2.")
         return
    except Exception as key_err:
        logger.exception(f"💥 FATAL: Failed to load/decode keys for Miner Agent (Instance 2): {key_err}")
        return

    # --- Khởi tạo các tiến trình (Instance 2) --- 
    miner_agent_instance: Optional[MinerAgent] = None
    try:
        logger.info("🛠️ Initializing Miner Agent instance (Instance 2)...")
        miner_agent_instance = MinerAgent(
            miner_uid_hex=expected_uid_hex,
            config=sdk_settings,
            miner_skey=miner_payment_skey, # type: ignore
            miner_stake_skey=miner_stake_skey # type: ignore
        )
        logger.info("✅ Miner Agent instance (Instance 2) initialized.")

        logger.info(f"🛠️ Initializing Subnet1Miner Server ('{miner_readable_id}' - Instance 2)...")
        miner_server_instance = Subnet1Miner(
            validator_url=validator_result_submit_url,
            on_chain_uid_hex=expected_uid_hex,
            host=miner_host,
            port=miner_port,
            miner_id=miner_readable_id
        )
        logger.info("✅ Subnet1Miner Server instance (Instance 2) initialized.")

        # Chạy Miner Server
        miner_server_thread = threading.Thread(target=miner_server_instance.run, daemon=True)
        miner_server_thread.start()
        logger.info(f"🧵 Started Subnet1Miner server (Instance 2) in background thread for '{miner_readable_id}' (UID: {expected_uid_hex})...")

        await asyncio.sleep(5)

        # Chạy Miner Agent
        logger.info(f"▶️ Starting Miner Agent main loop (Instance 2) for UID {expected_uid_hex}...")
        await miner_agent_instance.run(
            validator_api_url=validator_consensus_api_url, # type: ignore
            check_interval_seconds=miner_check_interval
        )
        logger.info("⏹️ Miner Agent main loop (Instance 2) finished.")

    except Exception as e:
        logger.exception(f"💥 An unexpected error occurred during miner process (Instance 2) startup or execution: {e}")
    finally:
        if miner_agent_instance:
            await miner_agent_instance.close()
        logger.info("🛑 Miner processes (Instance 2) cleanup finished.")

# --- Điểm thực thi chính --- 
if __name__ == "__main__":
    try:
        logger.info("🚦 Starting main asynchronous execution (Instance 2)...")
        asyncio.run(run_miner_processes())
    except KeyboardInterrupt:
        logger.info("👋 Miner processes (Instance 2) interrupted by user (Ctrl+C).")
    except Exception as main_err:
        logger.exception(f"💥 Critical error in main execution block (Instance 2): {main_err}")
    finally:
        logger.info("🏁 Miner script (Instance 2) finished.")