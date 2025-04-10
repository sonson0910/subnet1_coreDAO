import time
import logging
import traceback # Để ghi log lỗi chi tiết hơn

# Import từ SDK Moderntensor (đã được cài đặt)
# Đường dẫn import có thể cần điều chỉnh tùy thuộc vào cách bạn đóng gói SDK
try:
    from sdk.network.server import BaseMiner, TaskModel
except ImportError:
    logging.error("Could not import BaseMiner or TaskModel from sdk.network.server. "
                  "Make sure the moderntensor SDK is installed correctly.")
    # Định nghĩa lớp giả để tránh lỗi nếu import thất bại, nhưng miner sẽ không hoạt động
    class TaskModel: pass
    class BaseMiner:
        def __init__(self, *args, **kwargs): pass
        def process_task(self, task: TaskModel) -> dict: return {}

# Import từ các module khác trong subnet này
try:
    from .models.image_generator import generate_image_from_prompt, image_to_base64
except ImportError:
    logging.error("Could not import image generation functions from .models.image_generator.")
    # Hàm giả lập nếu import lỗi
    def generate_image_from_prompt(*args, **kwargs): return None
    def image_to_base64(*args, **kwargs): return None

logger = logging.getLogger(__name__)

class Subnet1Miner(BaseMiner):
    """
    Miner chuyên thực hiện nhiệm vụ sinh ảnh cho Subnet 1.
    Kế thừa BaseMiner từ SDK Moderntensor.
    """
    def __init__(self, validator_url, host="0.0.0.0", port=8000, miner_id="subnet1_miner_default"):
        """
        Khởi tạo Miner.

        Args:
            validator_url (str): URL của Validator API endpoint để gửi kết quả.
                                (Ví dụ: "http://validator_ip:port/v1/miner/submit_result")
            host (str): Địa chỉ IP để miner lắng nghe.
            port (int): Cổng để miner lắng nghe.
            miner_id (str): Định danh duy nhất cho miner này.
        """
        # Gọi __init__ của lớp cha (BaseMiner từ SDK)
        super().__init__(validator_url=validator_url, host=host, port=port)
        self.miner_id = miner_id # Lưu lại ID của miner này
        logger.info(f"Subnet1Miner '{self.miner_id}' initialized. Sending results to: {self.validator_url}")
        # Có thể thêm các khởi tạo khác ở đây, ví dụ tải trước model nếu cần
        # (Hiện tại logic tải model nằm trong image_generator.py)

    def process_task(self, task: TaskModel) -> dict:
        """
        Override phương thức xử lý task từ BaseMiner.
        Nhận task sinh ảnh, thực hiện và trả về kết quả.

        Args:
            task (TaskModel): Đối tượng task nhận từ validator.
                               Giả định task.description chứa prompt.

        Returns:
            dict: Dictionary chứa kết quả theo cấu trúc ResultModel của SDK,
                  sẵn sàng để gửi lại cho validator.
        """
        logger.info(f"Miner '{self.miner_id}' processing task: {task.task_id}")
        start_time = time.time()

        # --- 1. Lấy prompt từ task ---
        # Giả định validator gửi prompt trong trường 'description' của TaskModel
        # Bạn có thể thay đổi nếu validator gửi cấu trúc khác
        prompt = getattr(task, 'description', None)

        if not prompt:
            logger.warning(f"Task {task.task_id} received without a valid prompt in description.")
            duration = time.time() - start_time
            return {
                "result_id": f"result_{task.task_id}_error", # Thêm hậu tố lỗi
                "description": "Error: No prompt provided in task description.",
                "processing_time": duration,
                "miner_id": self.miner_id
            }

        logger.debug(f"Task {task.task_id} - Prompt: '{prompt}'")

        # --- 2. Gọi hàm sinh ảnh ---
        generated_image = None
        error_message = None
        try:
            # Gọi hàm từ image_generator.py
            # Có thể truyền thêm cấu hình model nếu cần
            generated_image = generate_image_from_prompt(prompt=prompt)
        except Exception as e:
            logger.exception(f"Exception during image generation for task {task.task_id}: {e}")
            error_message = f"Generation Error: {type(e).__name__}"
            # Ghi lại traceback để debug chi tiết hơn
            traceback.print_exc()

        # --- 3. Xử lý kết quả và định dạng output ---
        duration = time.time() - start_time
        image_base64_string = None

        if generated_image:
            logger.info(f"Task {task.task_id} - Image generated successfully in {duration:.2f}s.")
            # Chuyển ảnh thành base64 để gửi đi
            image_base64_string = image_to_base64(generated_image, format="PNG")
            if not image_base64_string:
                logger.error(f"Task {task.task_id} - Failed to convert generated image to base64.")
                error_message = "Error: Failed to encode image result."

        elif not error_message:
            # Hàm generate trả về None nhưng không có exception
            logger.warning(f"Task {task.task_id} - Image generation returned None without error.")
            error_message = "Error: Image generation failed silently."

        # --- 4. Tạo payload trả về ---
        # Cấu trúc này cần khớp với ResultModel trong sdk/network/server.py
        # và endpoint /v1/miner/submit_result
        result_payload = {
            "result_id": task.task_id, 
            # Trường 'description' sẽ chứa ảnh base64 hoặc thông báo lỗi
            "description": image_base64_string if image_base64_string else error_message,
            "processing_time": duration,
            "miner_id": self.miner_id
            # Bạn có thể thêm các trường metadata khác vào description nếu muốn, ví dụ:
            # "description": json.dumps({"image_base64": ..., "model_used": ...})
        }

        logger.debug(f"Task {task.task_id} - Prepared result payload (desc length: {len(result_payload.get('description', '')) if result_payload.get('description') else 0})")
        return result_payload

# --- (Tùy chọn) Thêm logic chạy miner trực tiếp từ file này để test ---
# if __name__ == '__main__':
#     import uvicorn
#     # Cấu hình logging cơ bản
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

#     # Lấy URL validator từ biến môi trường hoặc đặt giá trị mặc định
#     validator_api_url = os.getenv("VALIDATOR_URL", "http://127.0.0.1:8001/v1/miner/submit_result")
#     miner_host = os.getenv("MINER_HOST", "0.0.0.0")
#     miner_port = int(os.getenv("MINER_PORT", 9000)) # Dùng cổng khác validator
#     my_miner_id = os.getenv("MINER_ID", "subnet1_miner_test_01")

#     if not validator_api_url:
#         logger.error("VALIDATOR_URL environment variable is not set. Exiting.")
#     else:
#         logger.info(f"Starting Subnet1Miner '{my_miner_id}'...")
#         logger.info(f"Listening on: {miner_host}:{miner_port}")
#         logger.info(f"Reporting results to: {validator_api_url}")

#         # Khởi tạo miner của subnet này
#         miner_instance = Subnet1Miner(
#             validator_url=validator_api_url,
#             host=miner_host,
#             port=miner_port,
#             miner_id=my_miner_id
#         )

#         # Chạy FastAPI app bên trong BaseMiner
#         # BaseMiner.run() sẽ gọi uvicorn.run(self.app, ...)
#         # Lưu ý: BaseMiner.run() là blocking, nên nếu bạn cần chạy thêm logic
#         # trong script này, bạn cần chạy uvicorn trong một thread riêng.
#         # Tuy nhiên, cấu trúc BaseMiner đã xử lý việc nhận task trong thread riêng.
#         try:
#              miner_instance.run() # Gọi phương thức run của BaseMiner kế thừa
#         except ImportError as e:
#              logger.error(f"Could not run miner due to import error: {e}")
#         except Exception as e:
#              logger.exception(f"An error occurred while running the miner: {e}")