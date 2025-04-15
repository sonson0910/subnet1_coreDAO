# File: subnet1/miner.py
# Triển khai cụ thể cho Miner trong Subnet 1 (Image Generation)

import time
import logging
import traceback
import requests
import binascii # Thêm import nếu chưa có (dù không dùng trực tiếp ở đây)
from typing import Optional

# Import từ SDK Moderntensor
try:
    # TaskModel và ResultModel định nghĩa cấu trúc dữ liệu API
    # BaseMiner cung cấp khung cơ bản cho server miner
    from sdk.network.server import BaseMiner, TaskModel, ResultModel
except ImportError:
    logging.error("Could not import BaseMiner, TaskModel, or ResultModel from sdk.network.server. "
                  "Make sure the moderntensor SDK is installed correctly.")
    # Lớp giả để tránh lỗi nếu import thất bại
    class TaskModel:
         task_id: str = "dummy_task"
         description: Optional[str] = None
         deadline: Optional[str] = None
         priority: Optional[int] = None
         validator_endpoint: Optional[str] = None
    class ResultModel: pass
    class BaseMiner:
        def __init__(self, *args, **kwargs):
             self.validator_url = kwargs.get('validator_url') # URL validator mặc định (fallback)
        def process_task(self, task: TaskModel) -> dict: return {}
        def handle_task(self, task: TaskModel): pass # Thêm handle_task giả
        def run(self): pass # Thêm run giả


# Import từ các module khác trong subnet này
try:
    # Các hàm để sinh ảnh và chuyển đổi sang base64
    from .models.image_generator import generate_image_from_prompt, image_to_base64
except ImportError:
    logging.error("Could not import image generation functions from .models.image_generator.")
    # Hàm giả để code chạy được nếu import lỗi
    def generate_image_from_prompt(*args, **kwargs): return None
    def image_to_base64(*args, **kwargs): return None

# Lấy logger
logger = logging.getLogger(__name__)

class Subnet1Miner(BaseMiner):
    """
    Miner chuyên thực hiện nhiệm vụ sinh ảnh cho Subnet 1.
    Kế thừa BaseMiner từ SDK Moderntensor và tùy chỉnh logic xử lý task.
    """
    def __init__(
        self,
        validator_url: str,         # URL Validator mặc định để gửi kết quả (fallback)
        on_chain_uid_hex: str,    # UID hex on-chain *thực tế* của miner này
        host: str = "0.0.0.0",      # Host IP để server miner lắng nghe
        port: int = 8000,         # Cổng server miner lắng nghe
        miner_id: str = "subnet1_miner_default" # ID dễ đọc để nhận diện/logging
    ):
        """
        Khởi tạo Subnet1Miner.

        Args:
            validator_url: URL của validator mặc định (dùng nếu task không có validator_endpoint).
            on_chain_uid_hex: UID hex on-chain của miner này (dùng trong payload kết quả).
            host: Địa chỉ host server miner.
            port: Cổng server miner.
            miner_id: Tên định danh dễ đọc cho miner này (dùng cho logging).
        """
        # Gọi __init__ của lớp cha (BaseMiner)
        super().__init__(validator_url=validator_url, host=host, port=port)

        # Lưu trữ các thông tin cấu hình
        self.miner_id_readable = miner_id
        self.on_chain_uid_hex = on_chain_uid_hex

        # Kiểm tra định dạng UID hex (tùy chọn nhưng nên có)
        try:
            bytes.fromhex(self.on_chain_uid_hex)
        except (ValueError, TypeError):
             logger.error(f"Invalid on_chain_uid_hex provided to Subnet1Miner: '{self.on_chain_uid_hex}'. It must be a valid hex string.")
             # Có thể raise lỗi ở đây để dừng khởi tạo nếu UID sai
             # raise ValueError("Invalid on_chain_uid_hex format.")

        logger.info(f"Subnet1Miner '{self.miner_id_readable}' initialized.")
        logger.info(f" - On-Chain UID Hex: {self.on_chain_uid_hex}")
        logger.info(f" - Listening on: http://{self.host}:{self.port}")
        logger.info(f" - Default Validator URL (fallback): {self.validator_url}")

    def process_task(self, task: TaskModel) -> dict:
        """
        Override phương thức xử lý task từ BaseMiner.
        Nhận task sinh ảnh, thực hiện và trả về kết quả dưới dạng dictionary.

        Args:
            task (TaskModel): Đối tượng task nhận từ validator.
                               task.description chứa prompt.
                               task.validator_endpoint chứa URL validator gốc.

        Returns:
            dict: Dictionary chứa kết quả theo cấu trúc ResultModel của SDK,
                  sẵn sàng để gửi lại cho validator. Trường 'miner_id' sẽ
                  chứa on_chain_uid_hex.
        """
        # Sử dụng ID dễ đọc cho logging
        logger.info(f"Miner '{self.miner_id_readable}' processing task: {task.task_id}")
        start_time = time.time()

        # Lấy prompt từ task description
        prompt = getattr(task, 'description', None)

        # Xử lý trường hợp không có prompt
        if not prompt:
            logger.warning(f"Task {task.task_id} received without a valid prompt in description.")
            duration = time.time() - start_time
            return {
                "result_id": task.task_id, # Sử dụng task_id làm result_id để validator dễ map
                "description": "Error: No prompt provided in task description.",
                "processing_time": duration,
                "miner_id": self.on_chain_uid_hex # <<<--- Luôn dùng UID hex thật
            }

        logger.debug(f"Task {task.task_id} - Prompt: '{prompt}'")

        # --- Thực hiện sinh ảnh ---
        generated_image = None
        error_message = None
        try:
            # Gọi hàm sinh ảnh từ module models
            generated_image = generate_image_from_prompt(prompt=prompt)
        except Exception as e:
            # Ghi lại lỗi nếu quá trình sinh ảnh thất bại
            logger.exception(f"Exception during image generation for task {task.task_id}: {e}")
            error_message = f"Generation Error: {type(e).__name__}"
            traceback.print_exc() # In traceback chi tiết để debug

        duration = time.time() - start_time
        image_base64_string = None

        # --- Xử lý kết quả sinh ảnh ---
        if generated_image:
            # Nếu có ảnh, chuyển sang base64
            logger.info(f"Task {task.task_id} - Image generated successfully in {duration:.2f}s.")
            image_base64_string = image_to_base64(generated_image, format="PNG")
            if not image_base64_string:
                # Ghi lỗi nếu không chuyển được sang base64
                logger.error(f"Task {task.task_id} - Failed to convert generated image to base64.")
                error_message = "Error: Failed to encode image result."
        elif not error_message:
            # Trường hợp không có ảnh và cũng không có lỗi rõ ràng
            logger.warning(f"Task {task.task_id} - Image generation returned None without specific error.")
            error_message = "Error: Image generation failed silently."
        # Nếu có error_message từ trước thì giữ nguyên

        # --- Tạo payload kết quả cuối cùng ---
        result_payload = {
            "result_id": task.task_id, # Nên dùng task_id để validator dễ map lại
            # Mô tả chứa ảnh base64 hoặc thông báo lỗi
            "description": image_base64_string if image_base64_string else error_message,
            "processing_time": duration,
            "miner_id": self.on_chain_uid_hex # <<<--- Đảm bảo dùng UID hex thật ở đây
        }
        desc_len = len(result_payload.get('description') or '')
        logger.debug(f"Task {task.task_id} - Prepared result payload (miner_id: {result_payload['miner_id']}, desc_len: {desc_len})")
        return result_payload

    def handle_task(self, task: TaskModel):
        """
        (Override) Xử lý task nhận được từ validator.
        Hàm này được gọi (thường trong thread riêng) khi có task mới đến endpoint /receive-task.
        Nó sẽ gọi process_task để thực hiện công việc, sau đó gửi kết quả về validator gốc.
        """
        # 1. Thực hiện task để lấy dict kết quả
        result_payload = self.process_task(task)

        # 2. Xác định URL validator gốc để gửi kết quả về
        # URL này được validator gửi kèm trong đối tượng TaskModel
        target_validator_endpoint = getattr(task, 'validator_endpoint', None)

        # 3. Kiểm tra và gửi kết quả
        if target_validator_endpoint and isinstance(target_validator_endpoint, str) and target_validator_endpoint.startswith(("http://", "https://")):
            # Endpoint cụ thể trên validator để nhận kết quả (theo thiết kế API của validator)
            submit_url = target_validator_endpoint.rstrip('/') + "/v1/miner/submit_result"

            # Sử dụng ID dễ đọc cho logging
            logger.info(f"Miner '{self.miner_id_readable}' sending result for task {task.task_id} to originating validator: {submit_url}")
            try:
                # Gửi kết quả bằng HTTP POST request
                response = requests.post(submit_url, json=result_payload, timeout=15) # Tăng nhẹ timeout
                response.raise_for_status() # Kiểm tra lỗi HTTP (>= 400)

                # Log phản hồi từ validator
                try:
                     logger.info(f"Miner '{self.miner_id_readable}' - Validator response ({response.status_code}) from {submit_url}: {response.json()}")
                except requests.exceptions.JSONDecodeError:
                     logger.info(f"Miner '{self.miner_id_readable}' - Validator response ({response.status_code}) from {submit_url}: {response.text[:200]} (Non-JSON)")

            except requests.exceptions.Timeout:
                 logger.error(f"Miner '{self.miner_id_readable}' - Timeout sending result for task {task.task_id} to {submit_url}")
            except requests.exceptions.RequestException as e:
                 logger.error(f"Miner '{self.miner_id_readable}' - Error sending result for task {task.task_id} to {submit_url}: {e}")
            except Exception as e:
                 # Bắt các lỗi không mong muốn khác
                 logger.exception(f"Miner '{self.miner_id_readable}' - Unexpected error sending result for task {task.task_id} to {submit_url}: {e}")
        else:
            # Nếu không có endpoint hợp lệ trong task, ghi log lỗi
            logger.error(f"Miner '{self.miner_id_readable}' - Could not find valid 'validator_endpoint' in task {task.task_id}. Cannot send result back to originator.")
            # Cố gắng gửi về URL validator mặc định nếu được cấu hình
            if self.validator_url:
                 fallback_submit_url = self.validator_url.rstrip('/') + "/v1/miner/submit_result" # Giả định endpoint fallback
                 logger.warning(f"Miner '{self.miner_id_readable}' - Attempting to send result to default fallback validator URL: {fallback_submit_url}")
                 try:
                      response = requests.post(fallback_submit_url, json=result_payload, timeout=15)
                      response.raise_for_status()
                      logger.info(f"Fallback send to {fallback_submit_url} successful (Status: {response.status_code}).")
                 except Exception as fb_e:
                      logger.error(f"Fallback send to {fallback_submit_url} also failed: {fb_e}")
            else:
                 logger.error("No fallback validator URL configured either. Result not sent.")

    # Phương thức run() được kế thừa từ BaseMiner (trong sdk/network/server.py)
    # Nó sẽ khởi động server FastAPI/uvicorn để lắng nghe task trên host/port đã cấu hình.
    # def run(self):
    #     print(f"[Miner '{self.miner_id_readable}'] Starting server at http://{self.host}:{self.port}")
    #     uvicorn.run(self.app, host=self.host, port=self.port, log_level=logging.INFO) # Có thể cấu hình log level uvicorn