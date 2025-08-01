import sys
import os

# Add paths to find mt_core modules with absolute path
current_dir = os.path.dirname(__file__)  # subnet1_aptos/subnet1/
parent_dir = os.path.dirname(current_dir)  # subnet1_aptos/
project_root = os.path.dirname(parent_dir)  # moderntensor_core/
sdk_path = os.path.join(project_root, "moderntensor_aptos")
abs_sdk_path = os.path.abspath(sdk_path)
sys.path.insert(0, abs_sdk_path)

# SDK path configured successfully

# Also add parent for relative imports
sys.path.insert(0, parent_dir)

import logging
import random
import base64
import time
import datetime
import threading
import uvicorn
import json
from typing import Any, Dict, List, Optional
from collections import defaultdict
import os
import binascii
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import sys
import asyncio

# Import từ SDK Moderntensor (đã cài đặt)
try:
    from mt_core.consensus.validator_node_refactored import ValidatorNode
    from mt_core.core.datatypes import (
        TaskAssignment,
        TaskModel,
        MinerResult,
        ValidatorScore,
        ValidatorInfo,
        MinerInfo,
    )

    # Import successful, use real classes
    USING_MOCK_CLASSES = False
    logging.info("✅ Successfully imported ValidatorNode and core datatypes from SDK")
except ImportError as e:
    logging.error(
        f"Could not import ValidatorNode or core datatypes from the SDK: {e}. "
        "Ensure the 'moderntensor' SDK is installed."
    )

    # Create mock classes to prevent NameError
    class ValidatorNode:
        def __init__(self, *args, **kwargs):
            pass

    class TaskAssignment:
        def __init__(self, *args, **kwargs):
            pass

    class TaskModel:
        def __init__(self, *args, **kwargs):
            pass

    class MinerResult:
        def __init__(self, *args, **kwargs):
            pass

    class ValidatorScore:
        def __init__(self, *args, **kwargs):
            pass

    class ValidatorInfo:
        def __init__(self, *args, **kwargs):
            pass

    class MinerInfo:
        def __init__(self, *args, **kwargs):
            pass

    # Set flag
    USING_MOCK_CLASSES = True

# Import Flexible Consensus SDK
try:
    from .flexible_consensus_sdk import (
        FlexibleConsensusSDK,
        FlexibleConsensusConfig,
        FlexibleValidatorWrapper,
        create_flexible_validator,
        enable_flexible_consensus_for_validator,
        run_flexible_consensus_simple,
    )

    FLEXIBLE_CONSENSUS_AVAILABLE = True
    logging.info("✅ Flexible Consensus SDK imported successfully")
except ImportError as e:
    FLEXIBLE_CONSENSUS_AVAILABLE = False
    logging.warning(f"⚠️ Flexible Consensus SDK not available: {e}")

    # Create mock classes to prevent errors
    class FlexibleConsensusSDK:
        def __init__(self, *args, **kwargs):
            pass

    class FlexibleValidatorWrapper:
        def __init__(self, *args, **kwargs):
            pass

    # Lớp giả để tránh lỗi nếu import thất bại
    class ValidatorNode:
        def __init__(self, *args, **kwargs):
            self.validator_scores = {}
            self.results_received = defaultdict(list)
            self.tasks_sent = {}
            self.info = type("obj", (object,), {"uid": "fake_validator_uid"})()

        def _create_task_data(self, miner_uid: str) -> Any:
            return None

        # Xóa score_miner_results giả lập

    class TaskAssignment:
        def __init__(self, task_id, miner_uid, task_data):
            self.task_id = task_id
            self.miner_uid = miner_uid
            self.task_data = task_data

    class MinerResult:
        def __init__(self, task_id, miner_uid, result_data):
            self.task_id = task_id
            self.miner_uid = miner_uid
            self.result_data = result_data

    class ValidatorScore:
        pass

    class ValidatorInfo:
        def __init__(self, uid, **kwargs):
            self.uid = uid

    class MinerInfo:
        def __init__(self, uid, **kwargs):
            self.uid = uid

    USING_MOCK_CLASSES = True

# Import từ các module trong subnet này
try:
    from .scoring.clip_scorer import calculate_clip_score
except ImportError:
    logging.error("Could not import scoring functions from .scoring.clip_scorer.")

    def calculate_clip_score(*args, **kwargs) -> float:
        return 0.0


logger = logging.getLogger(__name__)

DEFAULT_PROMPTS = [
    "A photorealistic image of an astronaut riding a horse on the moon.",
    "A watercolor painting of a cozy bookstore cafe in autumn.",
    "A synthwave style cityscape at sunset.",
    "A macro shot of a bee collecting pollen from a sunflower.",
    "A fantasy landscape with floating islands and waterfalls.",
    "A cute dog wearing sunglasses and a party hat.",
    "Impressionist painting of a Parisian street scene.",
    "A steaming bowl of ramen noodles with detailed ingredients.",
    "Cyberpunk warrior standing in a neon-lit alley.",
    "A tranquil zen garden with raked sand and stones.",
]


class Subnet1Validator(ValidatorNode):
    """
    Validator cho Subnet 1 (Image Generation).
    Kế thừa ValidatorNode và triển khai logic tạo task, chấm điểm ảnh.
    """

    def __init__(
        self,
        validator_info,
        core_client,
        account,
        contract_address,
        api_port=8001,
        host="0.0.0.0",
        enable_flexible_consensus=True,
        flexible_mode="balanced",
        **kwargs,
    ):
        """Khởi tạo ValidatorNode và các thuộc tính riêng của Subnet 1."""

        # Store API configuration
        self.api_port = api_port
        self.host = host

        # Initialize ValidatorNode with required parameters including flexible consensus
        super().__init__(
            validator_info=validator_info,
            core_client=core_client,
            account=account,
            contract_address=contract_address,
            api_port=api_port,  # Explicitly pass api_port to parent
            enable_flexible_consensus=enable_flexible_consensus,  # Pass to SDK
            flexible_mode=flexible_mode,  # Pass to SDK
            **kwargs,
        )

        # Set reference to self in core for subnet-specific scoring access
        self.core.validator_instance = self

        # Track flexible consensus status from SDK
        self.subnet_flexible_mode = flexible_mode

        logger.info(
            f"✨ [bold]Subnet1Validator[/] initialized for UID: [cyan]{self.core.info.uid[:10]}...[/]"
            f" (Flexible Consensus: {'✅' if self.flexible_consensus_enabled else '❌'})"
        )
        # Note: FastAPI server is already handled by ValidatorNodeNetwork
        # No need to create separate app here

    # --- 1. Override phương thức tạo Task Data ---
    def _create_task_data(self, miner_uid: str) -> Any:
        """
        Tạo dữ liệu task (prompt) để gửi cho miner.
        *** Đã cập nhật để thêm validator_endpoint ***

        Args:
            miner_uid (str): UID của miner sẽ nhận task (có thể dùng để tùy biến task).

        Returns:
            Any: Dữ liệu task, trong trường hợp này là dict chứa prompt và validator_endpoint.
                 Cấu trúc này cần được miner hiểu.
        """
        selected_prompt = random.choice(DEFAULT_PROMPTS)
        logger.debug(
            f"Creating task for miner {miner_uid} with prompt: '{selected_prompt}'"
        )

        # Lấy API endpoint của chính validator này từ self.info
        # Cần đảm bảo self.info và self.info.api_endpoint đã được khởi tạo đúng
        origin_validator_endpoint = getattr(self.info, "api_endpoint", None)
        if not origin_validator_endpoint:
            # Xử lý trường hợp endpoint không có sẵn (quan trọng)
            logger.error(
                f"Validator {getattr(self.info, 'uid', 'UNKNOWN')} has no api_endpoint configured in self.info. Cannot create task properly."
            )
            # Có thể trả về None hoặc raise lỗi để ngăn gửi task không đúng
            return None  # Hoặc raise ValueError("Validator endpoint missing")

        # Tạo deadline ví dụ (ví dụ: 5 phút kể từ bây giờ)
        now = datetime.datetime.now(datetime.timezone.utc)
        deadline_dt = now + datetime.timedelta(minutes=5)
        deadline_str = deadline_dt.isoformat()

        # Đặt priority mặc định
        priority_level = random.randint(1, 5)

        # Trả về dictionary chứa các trường cần thiết CHO MINER HIỂU
        # Miner sẽ cần đọc 'description' để lấy prompt
        # Miner sẽ cần đọc 'validator_endpoint' để biết gửi kết quả về đâu
        return {
            "description": selected_prompt,  # Prompt chính là description của task
            "deadline": deadline_str,
            "priority": priority_level,
            "validator_endpoint": origin_validator_endpoint,  # <<<--- THÊM DÒNG NÀY
        }

    # --- Restore the correct override method for scoring ---
    def _score_individual_result(self, task_data: Any, result_data: Any) -> float:
        """
        (Override) Chấm điểm cho một kết quả cụ thể từ miner cho Subnet 1.
        This method is called by the base ValidatorNode class during its scoring phase.

        Args:
            task_data: Dữ liệu của task đã gửi (dict chứa 'description' là prompt).
            result_data: Dữ liệu kết quả miner trả về (dict chứa 'output_description', etc.).

        Returns:
            Điểm số float từ 0.0 đến 1.0.
        """
        logger.debug(f"💯 Scoring result via _score_individual_result...")
        score = 0.0  # Default score
        start_score_time = time.time()
        try:
            # 1. Extract prompt and base64 image
            if not isinstance(task_data, dict) or "description" not in task_data:
                logger.warning(
                    f"Scoring failed: Task data is not a dict or missing 'description'. Task data: {str(task_data)[:100]}..."
                )
                return 0.0
            original_prompt = task_data["description"]

            if not isinstance(result_data, dict):
                logger.warning(
                    f"Scoring failed: Received result_data is not a dictionary. Data: {str(result_data)[:100]}..."
                )
                return 0.0
            image_base64 = result_data.get("output_description")
            reported_error = result_data.get("error_details")
            processing_time_ms = result_data.get("processing_time_ms", 0)  # Optional

            # 2. Check for errors or missing image
            if reported_error:
                logger.warning(
                    f"Miner reported an error: '{reported_error}'. Assigning score 0."
                )
                return 0.0
            if not image_base64 or not isinstance(image_base64, str):
                logger.warning(
                    f"No valid image data (base64 string) found in result_data. Assigning score 0. Data: {str(result_data)[:100]}..."
                )
                return 0.0

            # Log base64 string length for debugging
            logger.debug(f"Received base64 image data: {len(image_base64)} characters")

            # 3. Decode image and Save it
            try:
                # Import the safe base64 decoder from clip_scorer
                from .scoring.clip_scorer import _safe_base64_decode

                image_bytes = _safe_base64_decode(image_base64)

                # --- Start: Save Image Logic ---
                output_dir = "result_image"
                try:
                    os.makedirs(output_dir, exist_ok=True)
                    # Using placeholder name for now, ideally pass task_id here.
                    miner_uid = result_data.get("miner_uid", "unknown_miner")
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    # Need task_id for a truly unique name. Placeholder:
                    filename = f"{output_dir}/result_{miner_uid[:8]}_{timestamp}.png"
                    with open(filename, "wb") as f:
                        f.write(image_bytes)
                    logger.info(f"   Saved image result to: {filename}")
                except OSError as file_err:
                    logger.error(
                        f"   Error saving image file to {filename}: {file_err}"
                    )
                except Exception as e:
                    logger.exception(f"   Unexpected error saving image: {e}")
                # --- End: Save Image Logic ---

            except (binascii.Error, ValueError, TypeError) as decode_err:
                logger.error(
                    f"Scoring failed: Invalid base64 data received. Error: {decode_err}. Assigning score 0."
                )
                return 0.0  # Return 0 if decode fails

            # 4. Calculate CLIP Score
            score = calculate_clip_score(
                prompt=original_prompt, image_bytes=image_bytes
            )
            # Ensure score is within valid range
            score = max(0.0, min(1.0, score))

            logger.info(
                f"   📊 CLIP Score: {score:.4f} for prompt: '{original_prompt[:50]}...'"
            )

        except Exception as e:
            logger.exception(f"Scoring failed with exception: {e}")
            score = 0.0

        scoring_duration = time.time() - start_score_time
        logger.debug(
            f"💯 Scoring completed in {scoring_duration:.3f}s, score: {score:.4f}"
        )
        return score

    # --- 2. Override phương thức xử lý kết quả ---
    def _should_process_result(self, result: MinerResult) -> bool:
        """
        (Override) Xác định có nên xử lý kết quả này không.
        """
        # Implement any custom logic here
        # For now, process all results
        return True

    # --- 3. Override phương thức tạo Task Assignment ---
    def _generate_task_assignment(
        self, miner: "MinerInfo"
    ) -> Optional["TaskAssignment"]:
        """
        (Override) Tạo task assignment cho miner.
        """
        task_id = self._generate_unique_task_id(miner.uid)
        task_data = self._create_task_data(miner.uid)

        if task_data is None:
            logger.warning(f"Could not create task data for miner {miner.uid}")
            return None

        return TaskAssignment(task_id=task_id, miner_uid=miner.uid, task_data=task_data)

    # --- 4. Helper methods ---
    def _generate_unique_task_id(self, miner_uid: str) -> str:
        """Generate a unique task ID."""
        timestamp = int(time.time() * 1000)
        return f"task_{miner_uid[:8]}_{timestamp}"

    def _generate_random_prompt(self) -> str:
        """Generate a random prompt for testing."""
        return random.choice(DEFAULT_PROMPTS)

    # --- 5. Use parent ValidatorNode run method ---
    # Note: ValidatorNodeNetwork already provides FastAPI server with:
    # - /health endpoint
    # - /api/v1/consensus/result/{cycle_num} endpoint
    # - /api/v1/validator/status endpoint
    # No need to override run() method

    # === FLEXIBLE CONSENSUS METHODS (Delegated to SDK) ===

    def get_flexible_consensus_status(self) -> Dict[str, Any]:
        """Get flexible consensus status and metrics from SDK"""
        # Delegate to SDK's implementation
        if hasattr(super(), "get_flexible_consensus_status"):
            status = super().get_flexible_consensus_status()
            status["subnet"] = "subnet1"
            status["subnet_mode"] = self.subnet_flexible_mode
            return status
        else:
            return {
                "validator_uid": self.core.info.uid,
                "flexible_consensus_enabled": getattr(
                    self, "flexible_consensus_enabled", False
                ),
                "subnet": "subnet1",
                "subnet_mode": self.subnet_flexible_mode,
                "message": "SDK flexible consensus not available",
            }

    async def run_consensus_cycle_flexible(self, slot: Optional[int] = None) -> bool:
        """
        Run a consensus cycle using SDK's flexible consensus.

        Args:
            slot: Optional slot number (auto-detected if None)

        Returns:
            True if successful, False otherwise
        """
        # Use SDK's flexible consensus implementation
        if hasattr(super(), "run_consensus_cycle_flexible"):
            logger.info(
                f"🚀 Running SDK flexible consensus cycle for Subnet1 validator"
            )
            return await super().run_consensus_cycle_flexible(slot)
        else:
            logger.warning("⚠️ SDK flexible consensus not available")
            return False

    # --- 6. Additional methods for subnet-specific functionality ---
    def get_validator_stats(self) -> Dict[str, Any]:
        """
        Lấy thống kê của validator.
        """
        return {
            "uid": self.info.uid,
            "tasks_sent": len(self.tasks_sent),
            "results_received": sum(
                len(results) for results in self.results_received.values()
            ),
            "validator_scores": len(self.validator_scores),
            "api_port": self.api_port,
            "using_mock_classes": USING_MOCK_CLASSES,
        }

    async def stop(self):
        """
        Stop the validator gracefully.
        Delegates to parent ValidatorNode's shutdown method.
        """
        logger.info(f"🛑 Stopping Subnet1Validator on port {self.api_port}")
        try:
            if hasattr(super(), "shutdown"):
                await super().shutdown()
            else:
                logger.warning("⚠️ Parent ValidatorNode has no shutdown method")
        except Exception as e:
            logger.error(f"❌ Error during validator shutdown: {e}")
        logger.info("✅ Subnet1Validator stopped successfully")
