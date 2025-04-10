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
             # Giả lập self.info nếu cần
             self.info = type('obj', (object,), {'uid': 'fake_validator_uid'})()
        def _create_task_data(self, miner_uid: str) -> Any: return None
        def score_miner_results(self): pass
    class TaskAssignment: pass
    class MinerResult: pass
    class ValidatorScore: pass


# Import từ các module trong subnet này
try:
    from .scoring.clip_scorer import calculate_clip_score
    # Import thêm datatypes nếu bạn có định nghĩa riêng
    # from .datatypes import ImageTaskData, ImageResultData
except ImportError:
    logging.error("Could not import scoring functions from .scoring.clip_scorer.")
    # Hàm giả nếu import lỗi
    def calculate_clip_score(*args, **kwargs) -> float: return 0.0

logger = logging.getLogger(__name__)

# --- Danh sách prompt ví dụ ---
# Bạn nên quản lý danh sách này tốt hơn (ví dụ: đọc từ file, database)
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
# -----------------------------


class Subnet1Validator(ValidatorNode):
    """
    Validator cho Subnet 1 (Image Generation).
    Kế thừa ValidatorNode và triển khai logic tạo task, chấm điểm ảnh.
    """

    # --- 1. Override phương thức tạo Task Data ---
    def _create_task_data(self, miner_uid: str) -> Any:
        """
        Tạo dữ liệu task (prompt) để gửi cho miner.

        Args:
            miner_uid (str): UID của miner sẽ nhận task (có thể dùng để tùy biến task).

        Returns:
            Any: Dữ liệu task, trong trường hợp này là dict chứa prompt.
                 Cấu trúc này cần được miner hiểu.
        """
        selected_prompt = random.choice(DEFAULT_PROMPTS)
        logger.debug(f"Creating task for miner {miner_uid} with prompt: '{selected_prompt}'")

        # Tạo deadline ví dụ (ví dụ: 5 phút kể từ bây giờ)
        # Bạn có thể đặt deadline cố định hoặc phức tạp hơn
        now = datetime.datetime.now(datetime.timezone.utc)
        deadline_dt = now + datetime.timedelta(minutes=5)
        deadline_str = deadline_dt.isoformat() # Chuyển thành chuỗi ISO 8601

        # Đặt priority mặc định
        priority_level = random.randint(1, 5) # Hoặc đặt cố định

        # Trả về dictionary chứa các trường description, deadline, priority
        # **QUAN TRỌNG**: Đặt prompt vào trường 'description'
        return {
            "description": selected_prompt, # Prompt chính là description của task
            "deadline": deadline_str,
            "priority": priority_level
        }

    # --- 2. Override phương thức chấm điểm ---
    # Chúng ta override toàn bộ `score_miner_results` để kiểm soát hoàn toàn
    # việc gọi hàm chấm điểm `calculate_clip_score` của subnet này.
    def score_miner_results(self):
        """
        Override phương thức chấm điểm từ ValidatorNode.
        Lấy kết quả ảnh từ miner, gọi hàm tính CLIP score và lưu điểm.
        """
        logger.info(f"[V:{self.info.uid}] Starting custom scoring for image generation...")
        self.validator_scores = {}  # Xóa điểm của chu kỳ trước

        # Lấy bản sao các kết quả đã nhận để xử lý
        # Sử dụng self.results_received được cập nhật bởi endpoint API
        # (Giả định endpoint `/v1/miner/submit_result` gọi `self.add_miner_result`
        #  và `self.add_miner_result` lưu vào `self.results_received`)
        # Cần đảm bảo luồng này hoạt động đúng trong SDK của bạn.
        # => Trong ví dụ trước, self.add_miner_result lưu vào self.results_received
        # => Nên lock khi truy cập nếu có khả năng ghi/đọc đồng thời
        # Tuy nhiên, trong luồng run_cycle, score_miner_results thường được gọi
        # sau khi đã chờ nhận kết quả xong, nên có thể không cần lock ở đây.
        results_to_score = self.results_received.copy()
        # Reset lại dict nhận kết quả cho chu kỳ sau (quan trọng)
        self.results_received = defaultdict(list)

        scored_tasks = 0
        for task_id, results_list in results_to_score.items():
            assignment = self.tasks_sent.get(task_id)

            # Kiểm tra xem có task tương ứng và task đó có prompt không
            if not assignment:
                logger.warning(f"Scoring skipped: Task assignment not found for task_id {task_id}.")
                continue
            # Giả định task_data là dict chứa "prompt" như đã tạo ở _create_task_data
            if not isinstance(assignment.task_data, dict) or "prompt" not in assignment.task_data:
                 logger.warning(f"Scoring skipped: Task data for {task_id} does not contain 'prompt'. Data: {assignment.task_data}")
                 continue

            original_prompt = assignment.task_data["prompt"]
            miner_assigned = assignment.miner_uid
            if task_id not in self.validator_scores:
                self.validator_scores[task_id] = []

            # Chỉ chấm điểm kết quả đầu tiên hợp lệ từ đúng miner được giao
            processed_task_for_miner = False
            for result in results_list:
                if result.miner_uid == miner_assigned:
                    score = 0.0 # Điểm mặc định nếu lỗi
                    try:
                        # Lấy ảnh base64 từ trường 'description' của result payload
                        # Đây là giả định dựa trên cách Subnet1Miner định dạng kết quả
                        image_base64 = result.result_data.get("description") if isinstance(result.result_data, dict) else None

                        if image_base64 and isinstance(image_base64, str) and not image_base64.startswith("Error:"):
                            logger.debug(f"Attempting to score image (base64 len: {len(image_base64)}) for task {task_id}...")
                            # Decode base64 thành bytes
                            image_bytes = base64.b64decode(image_base64)

                            # Gọi hàm tính CLIP score từ scoring module của subnet
                            score = calculate_clip_score(
                                prompt=original_prompt,
                                image_bytes=image_bytes
                                # Có thể truyền model_name từ config nếu muốn
                            )
                            # Đảm bảo điểm nằm trong khoảng [0, 1]
                            score = max(0.0, min(1.0, score))
                            logger.info(f"  Scored Miner {result.miner_uid} for task {task_id}: {score:.4f}")

                        elif image_base64 and image_base64.startswith("Error:"):
                             logger.warning(f"Miner {result.miner_uid} reported an error for task {task_id}: {image_base64}. Assigning score 0.")
                             score = 0.0
                        else:
                            logger.warning(f"No valid image data (base64) found in result for task {task_id} from miner {result.miner_uid}. Assigning score 0.")
                            score = 0.0

                    except Exception as e:
                        logger.exception(f"Error during scoring task {task_id} for miner {result.miner_uid}: {e}. Assigning score 0.")
                        score = 0.0 # Gán điểm 0 nếu có lỗi xảy ra

                    # Tạo đối tượng ValidatorScore
                    val_score = ValidatorScore(
                        task_id=task_id,
                        miner_uid=result.miner_uid,
                        validator_uid=self.info.uid, # UID của validator này
                        score=score
                        # timestamp được tự động gán
                    )
                    self.validator_scores[task_id].append(val_score)
                    processed_task_for_miner = True
                    scored_tasks += 1
                    break # Chỉ chấm điểm kết quả đầu tiên từ đúng miner

            if not processed_task_for_miner:
                 logger.warning(f"No valid result found from assigned miner {miner_assigned} for task {task_id}. Assigning score 0.")
                 # Tạo điểm 0.0 nếu không có kết quả hợp lệ từ miner được giao
                 val_score = ValidatorScore(
                      task_id=task_id, miner_uid=miner_assigned,
                      validator_uid=self.info.uid, score=0.0
                 )
                 self.validator_scores[task_id].append(val_score)


        logger.info(f"Custom scoring finished. Generated scores for {len(self.validator_scores)} tasks (total score entries: {scored_tasks}).")

    # Các phương thức khác của ValidatorNode (ví dụ: select_miners, send_task_and_track,
    # broadcast_scores, run_consensus_and_penalties, commit_updates...)
    # sẽ được kế thừa từ lớp cha trong SDK và hoạt động dựa trên
    # kết quả của _create_task_data và score_miner_results đã override ở đây.

# --- (Tùy chọn) Thêm logic chạy validator trực tiếp từ file này để test ---
# if __name__ == '__main__':
#     import asyncio
#     # ... (logic tương tự như trong sdk/consensus/node.py/main_validator_loop)
#     # 1. Load config (UID, keys, context...)
#     # 2. Tạo ValidatorInfo
#     # 3. Khởi tạo validator_node = Subnet1Validator(...)
#     # 4. Chạy asyncio.run(validator_node.run_cycle()) hoặc vòng lặp tương tự