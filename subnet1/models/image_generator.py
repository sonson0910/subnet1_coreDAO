import torch
from diffusers import StableDiffusionPipeline
from PIL import Image
import logging
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

# Biến global để cache pipeline (cách đơn giản, có thể dùng class nếu cần phức tạp hơn)
_pipeline_cache = {}

def _get_device():
    """Xác định device phù hợp (MPS cho M1/M2, CUDA hoặc CPU)."""
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    else:
        return torch.device("cpu")

def load_pipeline(model_id: str = "segmind/tiny-sd", revision="fp16"):
    """Tải và cache Stable Diffusion pipeline."""
    global _pipeline_cache
    device = _get_device()
    # Sử dụng tuple (model_id, revision, device) làm key cache
    cache_key = (model_id, str(device))

    if cache_key in _pipeline_cache:
        logger.debug(f"Using cached pipeline for {model_id} on {device}")
        return _pipeline_cache[cache_key]

    logger.info(f"Loading pipeline {model_id} (revision: {revision}) onto device: {device}...")
    try:
        pipeline = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if device != torch.device("cpu") else torch.float32, # float16 cho GPU/MPS
            # revision=revision,
            use_safetensors=False, # Ưu tiên safetensors
            # variant="fp16" # Một số model có variant riêng
        )
        pipeline.to(device)
        # (Tùy chọn) Tối ưu hóa nếu cần (ví dụ: attention slicing)
        # pipeline.enable_attention_slicing()

        _pipeline_cache[cache_key] = pipeline
        logger.info(f"Pipeline {model_id} loaded successfully.")
        return pipeline
    except Exception as e:
        logger.exception(f"Failed to load pipeline {model_id}: {e}")
        return None

def generate_image_from_prompt(
    prompt: str,
    model_id: str = "segmind/tiny-sd", # Model nhẹ
    num_inference_steps: int = 25,     # Số bước inference (ít hơn để nhanh hơn)
    guidance_scale: float = 7.5,
    # revision="fp16"
) -> Image.Image | None: # Trả về đối tượng PIL Image hoặc None nếu lỗi
    """
    Tạo ảnh từ prompt sử dụng Stable Diffusion pipeline đã được tải.

    Args:
        prompt: Chuỗi text mô tả ảnh cần tạo.
        model_id: Tên model trên Hugging Face.
        num_inference_steps: Số bước khuếch tán ngược.
        guidance_scale: Mức độ ảnh hưởng của prompt.
        revision: Revision của model (thường là fp16 cho bản tối ưu).

    Returns:
        Đối tượng PIL.Image chứa ảnh được tạo, hoặc None nếu có lỗi.
    """
    pipeline = load_pipeline(model_id=model_id)
    if pipeline is None:
        return None

    device = _get_device()
    logger.info(f"Generating image for prompt: '{prompt}' using {model_id} on {device}")

    try:
        # Chạy inference
        # Sử dụng torch.Generator để có thể đặt seed nếu muốn kết quả lặp lại
        generator = torch.Generator(device=str(device)) # Có thể đặt seed: .manual_seed(some_seed)
        with torch.inference_mode(): # Tối ưu bộ nhớ khi inference
             # Chuyển pipeline sang chế độ eval nếu có (một số pipeline cần)
             # if hasattr(pipeline, 'eval'): pipeline.eval()
             image = pipeline(
                 prompt,
                 num_inference_steps=num_inference_steps,
                 guidance_scale=guidance_scale,
                 generator=generator
             ).images[0] # Lấy ảnh đầu tiên từ kết quả

        logger.info("Image generated successfully.")
        return image
    except Exception as e:
        logger.exception(f"Error during image generation for prompt '{prompt}': {e}")
        return None

def image_to_base64(image: Image.Image, format="PNG") -> str | None:
    """Chuyển đổi đối tượng PIL Image sang chuỗi base64."""
    if not image:
        return None
    try:
        buffered = BytesIO()
        image.save(buffered, format=format)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str
    except Exception as e:
        logger.error(f"Failed to convert image to base64: {e}")
        return None

# --- Ví dụ sử dụng (có thể chạy file này độc lập để test) ---
if __name__ == '__main__':
    # Cấu hình logging cơ bản để xem output
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    test_prompt = "A cute robot eating ramen, cinematic lighting"
    logger.info(f"Testing image generation with prompt: '{test_prompt}'")

    generated_image = generate_image_from_prompt(test_prompt)

    if generated_image:
        logger.info("Image generation test successful.")
        # Lưu ảnh để kiểm tra (tùy chọn)
        try:
            save_path = "generated_test_image.png"
            generated_image.save(save_path)
            logger.info(f"Test image saved to {save_path}")

            # Test chuyển đổi base64
            base64_str = image_to_base64(generated_image)
            if base64_str:
                 logger.info(f"Base64 representation (first 100 chars): {base64_str[:100]}...")
            else:
                 logger.error("Failed to convert image to base64.")

        except Exception as e:
            logger.error(f"Error saving test image: {e}")
    else:
        logger.error("Image generation test failed.")