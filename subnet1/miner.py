# Thêm/Sửa trong file subnet1/miner.py

import time
import logging
import traceback
import requests # <<<--- Đảm bảo import requests
from typing import Optional # <<<--- Thêm Optional nếu chưa có

# Import từ SDK Moderntensor
try:
    # <<<--- Giờ cần thêm TaskModel vì handle_task dùng nó --->>>
    from sdk.network.server import BaseMiner, TaskModel, ResultModel
except ImportError:
    logging.error("Could not import BaseMiner or TaskModel from sdk.network.server. "
                  "Make sure the moderntensor SDK is installed correctly.")
    # Lớp giả để tránh lỗi nếu import thất bại
    class TaskModel:
         task_id: str = "dummy_task"
         description: Optional[str] = None
         deadline: Optional[str] = None
         priority: Optional[int] = None
         validator_endpoint: Optional[str] = None # Thêm vào lớp giả
    class ResultModel: pass
    class BaseMiner:
        def __init__(self, *args, **kwargs):
             self.validator_url = kwargs.get('validator_url') # Giữ lại để fallback
        def process_task(self, task: TaskModel) -> dict: return {}
        # Không cần handle_task trong base giả nữa

# Import từ các module khác trong subnet này
try:
    from .models.image_generator import generate_image_from_prompt, image_to_base64
except ImportError:
    logging.error("Could not import image generation functions from .models.image_generator.")
    def generate_image_from_prompt(*args, **kwargs): return None
    def image_to_base64(*args, **kwargs): return None

logger = logging.getLogger(__name__)

class Subnet1Miner(BaseMiner):
    """
    Miner chuyên thực hiện nhiệm vụ sinh ảnh cho Subnet 1.
    Kế thừa BaseMiner từ SDK Moderntensor.
    """
    def __init__(self, validator_url, host="0.0.0.0", port=8000, miner_id="subnet1_miner_default"):
        # Gọi __init__ của lớp cha, vẫn truyền validator_url làm fallback
        super().__init__(validator_url=validator_url, host=host, port=port)
        self.miner_id = miner_id
        logger.info(f"Subnet1Miner '{self.miner_id}' initialized. Default validator URL (fallback): {self.validator_url}")

    def process_task(self, task: TaskModel) -> dict:
        """
        Override phương thức xử lý task từ BaseMiner.
        Nhận task sinh ảnh, thực hiện và trả về kết quả.

        Args:
            task (TaskModel): Đối tượng task nhận từ validator.
                               Giả định task.description chứa prompt.
                               *** Giả định task.validator_endpoint chứa URL validator gốc ***

        Returns:
            dict: Dictionary chứa kết quả theo cấu trúc ResultModel của SDK,
                  sẵn sàng để gửi lại cho validator.
        """
        logger.info(f"Miner '{self.miner_id}' processing task: {task.task_id}")
        start_time = time.time()

        # Lấy prompt và endpoint gốc từ task
        prompt = getattr(task, 'description', None)
        # origin_validator_endpoint = getattr(task, 'validator_endpoint', None) # Lấy từ task
        miner_id=self.miner_id.encode('utf-8').hex()

        if not prompt:
            logger.warning(f"Task {task.task_id} received without a valid prompt in description.")
            duration = time.time() - start_time
            return {
                "result_id": task.task_id, # Sử dụng task_id làm result_id để validator dễ map
                "description": "Error: No prompt provided in task description.",
                "processing_time": duration,
                "miner_id": miner_id
                # Không cần gửi lại endpoint validator
            }

        logger.debug(f"Task {task.task_id} - Prompt: '{prompt}'") # Bỏ log endpoint ở đây

        # --- Phần sinh ảnh giữ nguyên ---
        generated_image = None
        error_message = None
        try:
            generated_image = generate_image_from_prompt(prompt=prompt)
        except Exception as e:
            logger.exception(f"Exception during image generation for task {task.task_id}: {e}")
            error_message = f"Generation Error: {type(e).__name__}"
            traceback.print_exc()

        duration = time.time() - start_time
        image_base64_string = None

        if generated_image:
            logger.info(f"Task {task.task_id} - Image generated successfully in {duration:.2f}s.")
            image_base64_string = image_to_base64(generated_image, format="PNG")
            if not image_base64_string:
                logger.error(f"Task {task.task_id} - Failed to convert generated image to base64.")
                error_message = "Error: Failed to encode image result."
        elif not error_message:
            logger.warning(f"Task {task.task_id} - Image generation returned None without error.")
            error_message = "Error: Image generation failed silently."
        # ------------------------------

        # Tạo payload kết quả (khớp ResultModel)
        result_payload = {
            "result_id": task.task_id, # Nên dùng task_id để validator dễ map lại
            "description": image_base64_string if image_base64_string else error_message,
            "processing_time": duration,
            "miner_id": miner_id
        }
        logger.debug(f"Task {task.task_id} - Prepared result payload (desc length: {len(result_payload.get('description', '')) if result_payload.get('description') else 0})")
        return result_payload

    # <<<--- THÊM PHƯƠNG THỨC OVERRIDE NÀY --->>>
    def handle_task(self, task: TaskModel):
        """
        (Override) Xử lý task, lấy endpoint validator gốc từ task, và gửi kết quả về đó.
        """
        # 1. Gọi process_task của chính lớp này để lấy dict kết quả
        result_payload = self.process_task(task)

        # 2. Xác định URL đích để gửi kết quả
        target_url = getattr(task, 'validator_endpoint', None) # Lấy từ đối tượng task

        # 3. Kiểm tra và gửi kết quả
        if target_url and isinstance(target_url, str) and target_url.startswith(("http://", "https://")):
            # Thêm đường dẫn endpoint cụ thể của validator để nhận kết quả
            submit_url = target_url.rstrip('/') + "/v1/miner/submit_result"
            logger.info(f"Miner '{self.miner_id}' sending result for task {task.task_id} to originating validator: {submit_url}")
            try:
                # Sử dụng submit_url đã có path đầy đủ
                response = requests.post(submit_url, json=result_payload, timeout=10) # Tăng timeout
                response.raise_for_status() # Kiểm tra lỗi HTTP >= 400
                try:
                     logger.info(f"Miner '{self.miner_id}' - Validator response ({response.status_code}) from {submit_url}: {response.json()}")
                except requests.exceptions.JSONDecodeError:
                     logger.info(f"Miner '{self.miner_id}' - Validator response ({response.status_code}) from {submit_url}: {response.text[:200]} (Non-JSON)")

            except requests.exceptions.Timeout:
                 logger.error(f"Miner '{self.miner_id}' - Timeout sending result for task {task.task_id} to {submit_url}")
            except requests.exceptions.RequestException as e:
                 logger.error(f"Miner '{self.miner_id}' - Error sending result for task {task.task_id} to {submit_url}: {e}")
            except Exception as e:
                 logger.exception(f"Miner '{self.miner_id}' - Unexpected error sending result for task {task.task_id} to {submit_url}: {e}")
        else:
            # Ghi log lỗi nếu không tìm thấy endpoint hợp lệ trong task
            logger.error(f"Miner '{self.miner_id}' - Could not find valid 'validator_endpoint' in task {task.task_id}. Cannot send result back to originator.")
            # Fallback về URL cấu hình mặc định nếu có
            if self.validator_url:
                 fallback_url = self.validator_url.rstrip('/') + "/v1/miner/submit_result"
                 logger.warning(f"Miner '{self.miner_id}' - Falling back to default validator URL: {fallback_url}")
                 try:
                      response = requests.post(fallback_url, json=result_payload, timeout=10)
                      response.raise_for_status()
                      logger.info(f"Fallback send to {fallback_url} successful (Status: {response.status_code}).")
                 except Exception as fb_e:
                      logger.error(f"Fallback send to {fallback_url} also failed: {fb_e}")
            else:
                 logger.error("No fallback validator URL configured either.")

    # run() được kế thừa từ BaseMiner