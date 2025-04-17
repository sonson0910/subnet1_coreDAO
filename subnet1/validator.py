import logging
import random
import base64
import time
import datetime
from typing import Any, Dict, List, Optional
from collections import defaultdict

# Import từ SDK Moderntensor (đã cài đặt)
try:
    from sdk.consensus.node import ValidatorNode
    from sdk.core.datatypes import TaskAssignment, MinerResult, ValidatorScore, ValidatorInfo, MinerInfo
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

    def __init__(self, *args, **kwargs):
        """Khởi tạo ValidatorNode và các thuộc tính riêng của Subnet 1."""
        super().__init__(*args, **kwargs)
        logger.info(f"✨ [bold]Subnet1Validator[/] initialized for UID: [cyan]{self.info.uid[:10]}...[/]")
        # Thêm các khởi tạo khác nếu cần, ví dụ:
        # self.image_generation_model = self._load_model()
        # self.clip_scorer = self._load_clip_scorer()

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
            # result_data giờ là dict chứa chi tiết kết quả từ miner
            # (ví dụ: { 'output_description': 'base64...', 'processing_time_ms': 123, ...})
            result_data: Dict[str, Any]

        Returns:
            Điểm số float từ 0.0 đến 1.0.
        """
        logger.debug(f"💯 [bold]Starting scoring process[/] for task result...")
        score = 0.0 # Điểm mặc định nếu lỗi
        start_score_time = time.time()
        try:
            # 1. Lấy prompt gốc từ task_data
            # task_data vẫn giữ cấu trúc cũ với prompt trong 'description'
            if not isinstance(task_data, dict) or "description" not in task_data:
                 logger.warning(f"Scoring failed: Task data is not a dict or missing 'description'. Task data: {str(task_data)[:100]}...")
                 return 0.0
            original_prompt = task_data["description"]

            # 2. Lấy ảnh base64 hoặc lỗi từ result_data (dictionary mới)
            if not isinstance(result_data, dict):
                logger.warning(f"Scoring failed: Received result_data is not a dictionary. Data: {str(result_data)[:100]}...")
                return 0.0

            image_base64 = result_data.get("output_description") # Key mới chứa ảnh/lỗi
            reported_error = result_data.get("error_details") # Key mới chứa lỗi chi tiết (nếu có)
            processing_time_ms = result_data.get("processing_time_ms", 0)

            # 3. Kiểm tra và tính điểm
            if reported_error:
                # Nếu miner báo lỗi rõ ràng
                logger.warning(f"Miner reported an error: '{reported_error}'. Assigning score 0.")
                score = 0.0
            elif image_base64 and isinstance(image_base64, str):
                # Nếu có ảnh base64 hợp lệ
                logger.debug(f"Attempting to score image (base64 len: {len(image_base64)}) for prompt: '{original_prompt[:50]}...'")
                try:
                    image_bytes = base64.b64decode(image_base64)
                    score = calculate_clip_score(
                        prompt=original_prompt,
                        image_bytes=image_bytes
                    )
                    score = max(0.0, min(1.0, score))
                    logger.info(f"  [bold blue]Scored result[/] for prompt '{original_prompt[:50]}...': [bold yellow]{score:.4f}[/] (Processing: {processing_time_ms}ms)")
                except base64.binascii.Error as b64_err:
                     logger.error(f"Scoring failed: Invalid base64 data received. Error: {b64_err}")
                     score = 0.0
                except ImportError:
                     logger.error("calculate_clip_score function is not available. Assigning score 0.")
                     score = 0.0
                except Exception as clip_err:
                    logger.exception(f"Error during CLIP score calculation: {clip_err}. Assigning score 0.")
                    score = 0.0
            else:
                # Trường hợp không có lỗi báo cáo và cũng không có ảnh base64 hợp lệ
                logger.warning(f"No valid image data (base64) or reported error found in result data. Assigning score 0. Data: {str(result_data)[:100]}...")
                score = 0.0

        except Exception as e:
            logger.exception(f"💥 Unexpected error during result scoring preparation: {e}. Assigning score 0.")
            score = 0.0
        
        scoring_duration = time.time() - start_score_time
        logger.debug(f"🏁 [bold]Finished scoring process[/] in {scoring_duration:.4f}s. Final score: [bold yellow]{score:.4f}[/]")
        return score

    # --- KHÔNG CÒN PHƯƠNG THỨC score_miner_results Ở ĐÂY ---

    # Các phương thức khác của ValidatorNode được kế thừa và sử dụng logic mới.

    def _should_process_result(self, result: MinerResult) -> bool:
        """Kiểm tra xem kết quả từ miner có hợp lệ để xử lý không."""
        logger.debug(f"🕵️ Checking validity of result for task '{result.task_id}' from miner '{result.miner_uid[:10]}...'")
        # Kiểm tra cấu trúc result_data mới
        if not isinstance(result.result_data, dict) or "output_description" not in result.result_data:
            logger.warning(f"⚠️ Invalid result format for task '{result.task_id}' from miner '{result.miner_uid[:10]}...'. Missing 'output_description' in result_data.")
            return False
        logger.debug(f"✅ Result for task '{result.task_id}' seems valid structure-wise.")
        return True

    def _generate_task_assignment(self, miner: MinerInfo) -> Optional[TaskAssignment]:
        """Tạo nhiệm vụ cụ thể cho miner (ví dụ: tạo prompt sinh ảnh)."""
        # Tạo một task_id duy nhất
        task_id = self._generate_unique_task_id(miner.uid)
        logger.info(f"📝 Generating task '{task_id}' for miner '{miner.uid[:10]}...'")

        # Tạo task_data cụ thể cho Subnet 1 (ví dụ: prompt)
        try:
            prompt = self._generate_random_prompt()
            # Create task_data dict with 'description' key for the prompt
            # to match what the miner expects inside task_data
            task_data = {"description": prompt}
            logger.info(f"   Generated prompt: [italic green]'{prompt}'[/] for task '{task_id}'")

            assignment = TaskAssignment(
                task_id=task_id,
                miner_uid=miner.uid,
                task_data=task_data, # Assign the dict with 'description' key
                # Ensure TaskModel used by validator logic populates correctly
            )
            return assignment
        except Exception as e:
            logger.exception(f"💥 Error generating task data for miner '{miner.uid[:10]}...': {e}")
            return None

    def _calculate_score_from_result(self, task_data: Any, result_data: Any) -> float:
        """
        (Override) Tính điểm P_miner,v dựa trên task và kết quả.

        Đây là logic chấm điểm cốt lõi của Subnet 1.
        Ví dụ: Sử dụng CLIP score để đo độ tương đồng giữa prompt và ảnh.
        """
        logger.debug(f"💯 Calculating score for result...")
        try:
            prompt = task_data.get("description")
            image_base64 = result_data.get("image_base64")

            if not prompt or not image_base64:
                logger.warning("⚠️ Cannot calculate score: Missing prompt or image_base64 in data.")
                return 0.0 # Điểm 0 nếu thiếu dữ liệu

            # --- Logic chấm điểm cụ thể của Subnet 1 --- 
            # Ví dụ giả định: Dùng CLIP score (cần import và load model)
            # image = self._decode_image(image_base64)
            # score = self.clip_scorer.calculate_score(prompt, image)

            # >>> Thay thế bằng logic chấm điểm thực tế của bạn <<<
            # Giả lập điểm số dựa trên độ dài prompt cho ví dụ:
            score = min(1.0, len(prompt) / 100.0) 
            logger.info(f"   Calculated score: [bold yellow]{score:.4f}[/]")
            # -------------------------------------------

            # Đảm bảo điểm nằm trong khoảng [0, 1]
            score = max(0.0, min(1.0, score))
            return score

        except Exception as e:
            logger.exception(f"💥 Error during score calculation: {e}")
            return 0.0 # Trả về 0 nếu có lỗi

    # --- Các hàm helper tùy chọn cho Subnet 1 --- 

    def _generate_random_prompt(self) -> str:
        """Tạo prompt ngẫu nhiên cho nhiệm vụ sinh ảnh."""
        prompts = [
            "A photorealistic image of a cat wearing a wizard hat",
            "A watercolor painting of a futuristic city skyline at sunset",
            "A cute robot reading a book in a cozy library, digital art",
            "Impressionist painting of a sunflower field under a stormy sky",
            "A steaming cup of coffee on a wooden table, macro shot",
            "Pencil sketch of an ancient dragon sleeping on a pile of gold",
        ]
        return random.choice(prompts)

    # def _load_model(self):
    #     """Tải model sinh ảnh (ví dụ: Stable Diffusion)."""
    #     logger.info("Loading image generation model...")
    #     # ... logic tải model ...
    #     logger.info("Image generation model loaded.")
    #     # return model

    # def _load_clip_scorer(self):
    #     """Tải model chấm điểm CLIP."""
    #     logger.info("Loading CLIP scorer...")
    #     # ... logic tải clip ...
    #     logger.info("CLIP scorer loaded.")
    #     # return scorer

    # def _decode_image(self, base64_string):
    #     """Giải mã ảnh từ chuỗi base64."""
    #     # ... logic giải mã ...
    #     # return image_object