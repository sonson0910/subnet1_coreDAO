# File: subnet1/miner.py
# Triển khai cụ thể cho Miner trong Subnet 1 (Image Generation)

import time
import logging
import traceback
import requests
import binascii # Thêm import nếu chưa có (dù không dùng trực tiếp ở đây)
from typing import Optional
import base64
from io import BytesIO
import os
from fastapi.responses import JSONResponse
import uvicorn
from PIL import Image
import httpx
import random

# Import từ SDK Moderntensor
try:
    # TaskModel và ResultModel định nghĩa cấu trúc dữ liệu API
    # BaseMiner cung cấp khung cơ bản cho server miner
    from mt_aptos.network.server import BaseMiner, TaskModel, ResultModel
except ImportError:
    logging.error("Could not import BaseMiner, TaskModel, or ResultModel from mt_aptos.network.server. "
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

# --- Constants/Config (Có thể chuyển ra file config riêng) ---
# Thay thế bằng model ID bạn muốn dùng
DEFAULT_MODEL_ID = "segmind/tiny-sd" 
# Có thể đọc từ env var nếu muốn linh hoạt hơn
MODEL_ID = os.getenv("IMAGEGEN_MODEL_ID", DEFAULT_MODEL_ID)

# --- 1. Task Processing Logic ---
def generate_image(prompt: str, seed: int = 42) -> bytes:
    """
    Placeholder for actual image generation logic using a model.
    Simulates generation and returns dummy image bytes.
    """
    logger.info(f"🎨 Simulating image generation for prompt: '{prompt[:50]}...'")
    # Simulate some processing time
    time.sleep(random.uniform(0.5, 2.0))
    # Create a dummy image representation (e.g., simple text as bytes)
    dummy_image_content = f"Image for '{prompt}' with seed {seed}".encode('utf-8')
    logger.info(f"🖼️ Simulated image generated (size: {len(dummy_image_content)} bytes).")
    return dummy_image_content


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
        miner_id: str = "subnet1_miner_default", # ID dễ đọc để nhận diện/logging
        model_id: str = MODEL_ID,
    ):
        """
        Khởi tạo Subnet1Miner.

        Args:
            validator_url: URL của validator mặc định (dùng nếu task không có validator_endpoint).
            on_chain_uid_hex: UID hex on-chain của miner này (dùng trong payload kết quả).
            host: Địa chỉ host server miner.
            port: Cổng server miner.
            miner_id: Tên định danh dễ đọc cho miner này (dùng cho logging).
            model_id: ID của model sinh ảnh (ví dụ: từ Hugging Face).
        """
        # Gọi __init__ của lớp cha (BaseMiner)
        # Pass miner_uid to BaseMiner's __init__ as well
        super().__init__(validator_url=validator_url, host=host, port=port, miner_uid=on_chain_uid_hex)

        # Lưu trữ các thông tin cấu hình
        self.miner_id_readable = miner_id or on_chain_uid_hex
        self.on_chain_uid_hex = on_chain_uid_hex # Đã được gán bởi super() nếu dùng miner_uid
        self.model_id = model_id

        # Kiểm tra định dạng UID hex (tùy chọn nhưng nên có)
        try:
            bytes.fromhex(self.on_chain_uid_hex)
        except (ValueError, TypeError):
             logger.error(f"Invalid on_chain_uid_hex provided to Subnet1Miner: '{self.on_chain_uid_hex}'. It must be a valid hex string.")
             # Có thể raise lỗi ở đây để dừng khởi tạo nếu UID sai
             # raise ValueError("Invalid on_chain_uid_hex format.")

        logger.info(f"✨ [bold]Subnet1Miner[/] initializing for ID: [cyan]'{self.miner_id_readable}'[/] (UID: [yellow]{self.on_chain_uid_hex[:10]}...[/])")
        logger.info(f"   👂 Listening on: [bold blue]{self.host}:{self.port}[/]")
        logger.info(f"   ➡️ Validator Submit URL: [link={self.validator_url}]{self.validator_url}[/link]")
        logger.info(f"   🧠 Using Image Gen Model: [magenta]{self.model_id}[/]")

        # Tải model AI (có thể mất thời gian)
        self.pipe = self._load_model()

    def _load_model(self):
        """Tải model sinh ảnh (ví dụ: Stable Diffusion)."""
        logger.info(f"⏳ [bold]Loading image generation model[/] ([magenta]{self.model_id}[/])... This may take a while.")
        start_load_time = time.time()
        try:
            # --- Logic tải model thực tế --- 
            logger.debug("   Attempting to load model pipeline...")
            # pipe = StableDiffusionPipeline.from_pretrained(self.model_id)
            # # Tối ưu hóa nếu có GPU
            # if torch.cuda.is_available():
            #     logger.info("   🚀 CUDA detected. Moving model to GPU.")
            #     pipe = pipe.to("cuda")
            # elif torch.backends.mps.is_available(): # Cho Apple Silicon
            #     logger.info("   🍏 MPS detected. Moving model to MPS.")
            #     pipe = pipe.to("mps")
            # else:
            #     logger.info("   🐌 No GPU acceleration detected (CUDA/MPS). Running on CPU.")
            
            # >>> Thay bằng logic tải model của bạn <<<
            # Giả lập việc tải model
            time.sleep(2) 
            pipe = "FAKE_MODEL_PIPELINE" # Placeholder
            # --------------------------------
            load_duration = time.time() - start_load_time
            logger.info(f"✅🧠 [bold]Image generation model[/] ([magenta]{self.model_id}[/]) [bold green]loaded successfully[/] in {load_duration:.2f}s.")
            return pipe
        except Exception as e:
            load_duration = time.time() - start_load_time
            logger.exception(f"💥❌ [bold red]Failed[/] to load image generation model '{self.model_id}' after {load_duration:.2f}s: {e}")
            # Có thể raise lỗi hoặc thoát nếu không load được model
            raise RuntimeError(f"Could not load model: {self.model_id}") from e

    def process_task(self, task: TaskModel) -> dict:
        """
        Thực hiện task và trả về dictionary chứa chi tiết kết quả.
        Dict này sẽ được đặt vào trường 'result_data' của ResultModel.
        """
        # Sử dụng ID dễ đọc cho logging
        logger.info(f"⛏️ [bold]Processing task[/] [yellow]{task.task_id}[/yellow] for miner '{self.miner_id_readable}'")
        start_time = time.time()

        # Lấy prompt từ task.task_data (theo định nghĩa TaskModel mới)
        prompt = task.description

        if not prompt:
            logger.warning(f"Task {task.task_id} received without a valid 'description' in task_data.")
            duration = time.time() - start_time
            return {
                "error": "No prompt provided in task_data.description",
                "processing_time_ms": int(duration * 1000),
            }

        logger.debug(f"Task {task.task_id} - Prompt: '{prompt}'")

        # --- Thực hiện sinh ảnh --- 
        generated_image = None
        error_message = None
        image_base64_string = None
        generation_start_time = time.time()
        logger.info(f"   ⏳ [italic]Starting image generation...[/] (Task: {task.task_id}) ")
        try:
            generated_image = generate_image_from_prompt(prompt=prompt)
            generation_duration = time.time() - generation_start_time
            if generated_image:
                 logger.info(f"   ✅🖼️ [italic]Image generated successfully[/] in {generation_duration:.2f}s. (Task: {task.task_id}) ")
            else:
                 logger.warning(f"   ⚠️ [italic]Image generation returned None[/] after {generation_duration:.2f}s. (Task: {task.task_id}) ")
        except Exception as e:
            generation_duration = time.time() - generation_start_time
            logger.exception(f"   💥 [italic red]Exception during image generation[/] after {generation_duration:.2f}s: {e} (Task: {task.task_id}) ")
            error_message = f"Generation Error: {type(e).__name__}"
            traceback.print_exc()

        total_duration = time.time() - start_time

        # --- Xử lý kết quả sinh ảnh --- 
        if generated_image:
            #logger.info(f"Task {task.task_id} - Image generated successfully in {duration:.2f}s.")
            image_base64_string = image_to_base64(generated_image, format="PNG")
            if not image_base64_string:
                logger.error(f"Task {task.task_id} - Failed to convert generated image to base64.")
                error_message = "Error: Failed to encode image result."
        elif not error_message:
            logger.warning(f"Task {task.task_id} - Image generation returned None without specific error.")
            error_message = "Error: Image generation failed silently."
        
        # --- Tạo dictionary chứa chi tiết kết quả --- 
        result_details = {
            "output_description": image_base64_string if image_base64_string else (error_message or "Error: Unknown processing error"),
            "processing_time_ms": int(total_duration * 1000),
            "generation_time_ms": int(generation_duration * 1000), # Add generation time
            "model_id_used": self.model_id,
            "error_details": error_message
        }
        logger.debug(f"Task {task.task_id} - Prepared result details dict: {str(result_details)[:150]}...")
        logger.info(f"✅ [bold]Finished processing task[/] [yellow]{task.task_id}[/yellow] in {total_duration:.2f}s.")
        return result_details

    def handle_task(self, task: TaskModel):
        """
        (Override) Xử lý task nhận được từ validator.
        Hàm này được gọi (thường trong thread riêng) khi có task mới đến endpoint /receive-task.
        Nó sẽ gọi process_task để thực hiện công việc, sau đó gửi kết quả về validator gốc.
        """
        # 1. Thực hiện task để lấy dict kết quả chi tiết
        # process_task giờ trả về dict chứa chi tiết kết quả (ảnh base64/lỗi)
        result_details = self.process_task(task)

        # 2. Tạo đối tượng ResultModel theo định nghĩa mới
        # Decode hex UID back to string for validator compatibility
        try:
            miner_uid_string = bytes.fromhex(self.on_chain_uid_hex).decode('utf-8')
        except (ValueError, UnicodeDecodeError):
            # Fallback to hex if decode fails
            miner_uid_string = self.on_chain_uid_hex
            
        result_to_send = ResultModel(
            task_id=task.task_id,
            miner_uid=miner_uid_string, # Use decoded string UID
            result_data=result_details, # Đặt dict kết quả chi tiết vào đây
        )

        # 3. Xác định URL validator gốc để gửi kết quả về
        target_validator_endpoint = getattr(task, 'validator_endpoint', None)
        submit_url = None

        if target_validator_endpoint and isinstance(target_validator_endpoint, str) and target_validator_endpoint.startswith(("http://", "https://")):
            submit_url = target_validator_endpoint.rstrip('/') + "/v1/miner/submit_result"
        elif self.validator_url:
             submit_url = self.validator_url.rstrip('/') + "/v1/miner/submit_result"
             logger.warning(f"Miner '{self.miner_id_readable}' - No valid validator_endpoint in task {task.task_id}. Using default fallback: {submit_url}")
        else:
             logger.error(f"Miner '{self.miner_id_readable}' - Cannot send result for task {task.task_id}. No validator_endpoint in task and no fallback URL configured.")
             return

        # 4. Gửi đối tượng ResultModel đã được serialize
        if submit_url:
            logger.info(f"📤 Sending result for task '{task.task_id}' (MinerUID: {result_to_send.miner_uid}) to validator: [link={submit_url}]{submit_url}[/link] ...")
            logger.debug(f"   Payload: {str(result_to_send.dict())[:150]}...") # Log payload gửi đi
            try:
                # Dùng requests (đồng bộ)
                response = requests.post(submit_url, json=result_to_send.dict(), timeout=30)

                if 200 <= response.status_code < 300:
                    logger.info(f"✅ Result for task '{task.task_id}' sent successfully (Status: {response.status_code}).")
                else:
                    logger.error(
                        f"❌ Failed to send result for task '{task.task_id}'. Validator responded with status {response.status_code}. Response: {response.text[:200]}..."
                    )
            except requests.exceptions.RequestException as req_err:
                 logger.error(f"❌ Network error sending result for task '{task.task_id}' to {submit_url}: {req_err}")
            except Exception as send_err:
                 logger.exception(f"💥 Unexpected error sending result for task '{task.task_id}': {send_err}")

    def run(self):
        """Khởi chạy Uvicorn server để chạy API."""
        logger.info(f"▶️ Starting Uvicorn server for Miner '{self.miner_id_readable}' on {self.host}:{self.port}...")
        try:
            uvicorn.run(
                self.app,
                host=self.host,
                port=self.port,
            )
        except Exception as e:
             logger.exception(f"💥 Failed to run Uvicorn server: {e}")

    def _encode_image(self, image: Image.Image) -> str:
        """Mã hóa đối tượng ảnh PIL thành chuỗi base64."""
        # ... rest of the file