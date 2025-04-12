import logging
import random
import base64
import time
import datetime
from typing import Any, Dict, List
from collections import defaultdict

# Import từ SDK Moderntensor (đã cài đặt)
try:
    from sdk.consensus.node import ValidatorNode
    from sdk.core.datatypes import TaskAssignment, MinerResult, ValidatorScore
except ImportError:
    logging.error("Could not import ValidatorNode or core datatypes from the SDK. "
                  "Ensure the 'moderntensor' SDK is installed.")
    # Lớp giả để tránh lỗi nếu import thất bại
    class ValidatorNode:
        def __init__(self, *args, **kwargs):
             self.validator_scores = {}
             self.results_received = defaultdict(list)
             self.tasks_sent = {}
             self.info = type('obj', (object,), {'uid': 'fake_validator_uid'})()
        def _create_task_data(self, miner_uid: str) -> Any: return None
        # Xóa score_miner_results giả lập
    class TaskAssignment: pass
    class MinerResult: pass
    class ValidatorScore: pass

# Import từ các module trong subnet này
try:
    from .scoring.clip_scorer import calculate_clip_score
except ImportError:
    logging.error("Could not import scoring functions from .scoring.clip_scorer.")
    def calculate_clip_score(*args, **kwargs) -> float: return 0.0

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
        logger.debug(f"Creating task for miner {miner_uid} with prompt: '{selected_prompt}'")

        # Lấy API endpoint của chính validator này từ self.info
        # Cần đảm bảo self.info và self.info.api_endpoint đã được khởi tạo đúng
        origin_validator_endpoint = getattr(self.info, 'api_endpoint', None)
        if not origin_validator_endpoint:
             # Xử lý trường hợp endpoint không có sẵn (quan trọng)
             logger.error(f"Validator {getattr(self.info, 'uid', 'UNKNOWN')} has no api_endpoint configured in self.info. Cannot create task properly.")
             # Có thể trả về None hoặc raise lỗi để ngăn gửi task không đúng
             return None # Hoặc raise ValueError("Validator endpoint missing")

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
            "description": selected_prompt, # Prompt chính là description của task
            "deadline": deadline_str,
            "priority": priority_level,
            "validator_endpoint": origin_validator_endpoint # <<<--- THÊM DÒNG NÀY
        }

    # --- 2. Override phương thức CHẤM ĐIỂM CÁ NHÂN ---
    # <<<--- THAY THẾ score_miner_results BẰNG HÀM NÀY --->>>
    def _score_individual_result(self, task_data: Any, result_data: Any) -> float:
        """
        (Override) Chấm điểm cho một kết quả cụ thể từ miner cho Subnet 1.
        Hàm này được gọi bởi _score_current_batch trong ValidatorNode base class.

        Args:
            task_data: Dữ liệu của task đã gửi (dict chứa 'description' là prompt).
            result_data: Dữ liệu kết quả miner trả về (dict chứa 'description' là ảnh base64 hoặc lỗi).

        Returns:
            Điểm số float từ 0.0 đến 1.0.
        """
        score = 0.0 # Điểm mặc định nếu lỗi
        try:
            # 1. Lấy prompt gốc từ task_data
            if not isinstance(task_data, dict) or "description" not in task_data:
                 logger.warning(f"Scoring failed: Task data is not a dict or missing 'description'. Task data: {str(task_data)[:100]}...")
                 return 0.0
            original_prompt = task_data["description"]

            # 2. Lấy ảnh base64 từ result_data
            #    result_data được cấu trúc trong add_miner_result của node base
            #    nó chứa các key như 'description', 'processing_time', 'payload_data'
            if not isinstance(result_data, dict) or "description" not in result_data:
                  logger.warning(f"Scoring failed: Result data is not a dict or missing 'description'. Result data: {str(result_data)[:100]}...")
                  return 0.0
            image_base64 = result_data["description"]

            # 3. Kiểm tra và tính điểm nếu có ảnh hợp lệ
            if image_base64 and isinstance(image_base64, str) and not image_base64.startswith("Error:"):
                logger.debug(f"Attempting to score image (base64 len: {len(image_base64)}) for prompt: '{original_prompt[:50]}...'")
                try:
                    # Decode base64 thành bytes
                    image_bytes = base64.b64decode(image_base64)

                    # Gọi hàm tính CLIP score từ scoring module của subnet
                    score = calculate_clip_score(
                        prompt=original_prompt,
                        image_bytes=image_bytes
                    )
                    score = max(0.0, min(1.0, score)) # Đảm bảo trong khoảng [0, 1]
                    logger.info(f"  Scored result for prompt '{original_prompt[:50]}...': {score:.4f}")

                except base64.binascii.Error as b64_err:
                     logger.error(f"Scoring failed: Invalid base64 data received. Error: {b64_err}")
                     score = 0.0
                except ImportError:
                     logger.error("calculate_clip_score function is not available. Assigning score 0.")
                     score = 0.0
                except Exception as clip_err:
                    logger.exception(f"Error during CLIP score calculation: {clip_err}. Assigning score 0.")
                    score = 0.0

            elif image_base64 and image_base64.startswith("Error:"):
                 logger.warning(f"Miner reported an error in result data: {image_base64}. Assigning score 0.")
                 score = 0.0
            else:
                logger.warning(f"No valid image data (base64) found in result description. Assigning score 0.")
                score = 0.0

        except Exception as e:
            logger.exception(f"Unexpected error during result scoring preparation: {e}. Assigning score 0.")
            score = 0.0

        return score

    # --- KHÔNG CÒN PHƯƠNG THỨC score_miner_results Ở ĐÂY ---

    # Các phương thức khác của ValidatorNode được kế thừa và sử dụng logic mới.