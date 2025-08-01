import torch
import clip  # Import thư viện CLIP đã cài từ git
from PIL import Image
import base64
from io import BytesIO
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Cache cho model và processor
_clip_model_cache = {}
_clip_preprocess_cache = {}
_clip_device_cache = None


def _safe_base64_decode(base64_string: str) -> bytes:
    """
    Safely decode base64 string with proper validation and padding.

    Args:
        base64_string: The base64 encoded string

    Returns:
        Decoded bytes

    Raises:
        ValueError: If the string is not valid base64
    """
    if not base64_string:
        raise ValueError("Empty base64 string")

    # Remove whitespace and newlines
    base64_string = re.sub(r"\s+", "", base64_string)

    # Check if string contains only valid base64 characters
    if not re.match(r"^[A-Za-z0-9+/]*={0,2}$", base64_string):

        raise ValueError(
            f"Invalid base64 characters in string (length: {len(base64_string)})"
        )

    # Check minimum length
    if len(base64_string) < 4:
        raise ValueError(f"Base64 string too short: {len(base64_string)} characters")

    # Add padding if necessary
    missing_padding = len(base64_string) % 4
    if missing_padding:
        base64_string += "=" * (4 - missing_padding)
        logger.debug(f"Added {4 - missing_padding} padding characters to base64 string")

    try:
        return base64.b64decode(base64_string)
    except Exception as e:
        raise ValueError(f"Failed to decode base64 string: {e}")


def _get_clip_device():
    """Xác định device phù hợp cho CLIP."""
    global _clip_device_cache
    if _clip_device_cache:
        return _clip_device_cache

    if torch.backends.mps.is_available():
        _clip_device_cache = torch.device("mps")
    elif torch.cuda.is_available():
        _clip_device_cache = torch.device("cuda")
    else:
        _clip_device_cache = torch.device("cpu")
    logger.info(f"CLIP using device: {_clip_device_cache}")
    return _clip_device_cache


def load_clip_model(model_name: str = "ViT-B/32"):
    """Tải và cache model CLIP và preprocessor."""
    global _clip_model_cache, _clip_preprocess_cache
    device = _get_clip_device()
    cache_key = (model_name, str(device))

    if cache_key in _clip_model_cache:
        logger.debug(f"Using cached CLIP model/preprocess for {model_name} on {device}")
        return _clip_model_cache[cache_key], _clip_preprocess_cache[cache_key]

    logger.info(f"Loading CLIP model: {model_name} onto device: {device}...")
    try:
        # Sử dụng thư viện `clip` đã cài từ OpenAI repo
        model, preprocess = clip.load(model_name, device=device)
        _clip_model_cache[cache_key] = model
        _clip_preprocess_cache[cache_key] = preprocess
        logger.info(f"CLIP model {model_name} loaded successfully.")
        return model, preprocess
    except Exception as e:
        logger.exception(f"Failed to load CLIP model {model_name}: {e}")
        return None, None


def calculate_clip_score(
    prompt: str,
    image_base64: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
    model_name: str = "ViT-B/32",  # Model CLIP tiêu chuẩn
) -> float:
    """
    Tính điểm tương đồng CLIP giữa prompt và ảnh.

    Args:
        prompt: Chuỗi text mô tả.
        image_base64: Chuỗi base64 của ảnh (ưu tiên nếu có).
        image_bytes: Dữ liệu bytes của ảnh (dùng nếu base64 là None).
        model_name: Tên model CLIP (ví dụ: "ViT-B/32", "ViT-L/14").

    Returns:
        Điểm số float trong khoảng [0.0, 1.0], hoặc 0.0 nếu có lỗi.
    """
    if not prompt or (not image_base64 and not image_bytes):
        logger.warning("CLIP scoring skipped: Missing prompt or image data.")
        return 0.0

    model, preprocess = load_clip_model(model_name)
    if model is None or preprocess is None:
        logger.error("CLIP model/preprocess not loaded. Cannot calculate score.")
        return 0.0

    device = _get_clip_device()
    image = None
    try:
        # --- Xử lý ảnh đầu vào ---
        if image_base64:
            try:
                # Use safe base64 decoding with validation and padding
                image_bytes_decoded = _safe_base64_decode(image_base64)
                image = Image.open(BytesIO(image_bytes_decoded)).convert("RGB")
                logger.debug(
                    f"Successfully decoded base64 image ({len(image_bytes_decoded)} bytes)"
                )
            except ValueError as e:
                logger.error(f"Invalid base64 image data: {e}")
                return 0.0
            except Exception as e:
                logger.error(f"Failed to process base64 image: {e}")
                return 0.0
        elif image_bytes:
            try:
                image = Image.open(BytesIO(image_bytes)).convert("RGB")
            except Exception as e:
                logger.error(f"Failed to open image from bytes: {e}")
                return 0.0
        else:
            # Trường hợp này đã kiểm tra ở đầu nhưng thêm để rõ ràng
            logger.error("No image data provided to calculate_clip_score")
            return 0.0

        if image is None:
            logger.error("Image could not be processed.")
            return 0.0

        # --- Chuẩn bị input cho CLIP ---
        image_input = preprocess(image).unsqueeze(0).to(device)
        text_input = clip.tokenize([prompt]).to(device)

        # --- Tính toán embeddings và similarity ---
        with torch.no_grad():  # Không cần tính gradient
            image_features = model.encode_image(image_input)
            text_features = model.encode_text(text_input)

            # Chuẩn hóa features (quan trọng cho cosine similarity)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)

            # Tính cosine similarity
            # similarity = (image_features @ text_features.T).squeeze(0).item() # Chỉ lấy giá trị đầu tiên

            # Hoặc tính logit scale (theo cách làm của CLIP gốc) và chuẩn hóa
            logit_scale = model.logit_scale.exp()
            logits_per_image = logit_scale * image_features @ text_features.t()
            # logits_per_text = logits_per_image.t() # Không cần cái này

            # Lấy giá trị tương đồng (logit) - giá trị này không nằm trong [-1,1]
            similarity_logit = logits_per_image.squeeze().item()  # Lấy giá trị float

            # **Chuẩn hóa điểm số về [0, 1]**
            # Cách 1: Dùng Cosine Similarity trực tiếp
            cosine_sim = (image_features * text_features).sum(dim=-1).squeeze().item()
            normalized_score = (cosine_sim + 1.0) / 2.0

            # Cách 2: Chuẩn hóa logit (cần xem xét thang đo phù hợp)
            # Ví dụ đơn giản: dùng hàm sigmoid hoặc scale dựa trên khoảng giá trị thực tế
            # normalized_score_logit = 1 / (1 + math.exp(-similarity_logit / 10)) # Ví dụ scale factor 10

            # Chọn cách chuẩn hóa (dùng cosine sim cho đơn giản)
            final_score = max(0.0, min(1.0, normalized_score))

            logger.debug(
                f"CLIP score calculated for prompt '{prompt[:30]}...': {final_score:.4f} (Cosine Sim: {cosine_sim:.4f})"
            )
            return final_score

    except Exception as e:
        logger.exception(f"Error during CLIP score calculation: {e}")
        return 0.0  # Trả về 0 nếu có lỗi


# --- Ví dụ sử dụng (có thể chạy file này độc lập để test) ---
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    logger.info("Testing CLIP scorer...")
    # Tạo ảnh trắng giả lập để test (cần cài Pillow: pip install Pillow)
    try:
        img = Image.new("RGB", (224, 224), color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

        test_prompt1 = "a white square"
        test_prompt2 = "a black cat"

        score1 = calculate_clip_score(prompt=test_prompt1, image_base64=img_base64)
        logger.info(
            f"Score for prompt '{test_prompt1}' (should be relatively high): {score1:.4f}"
        )

        score2 = calculate_clip_score(prompt=test_prompt2, image_bytes=img_bytes)
        logger.info(
            f"Score for prompt '{test_prompt2}' (should be relatively low): {score2:.4f}"
        )

        # Test trường hợp lỗi
        score_error = calculate_clip_score(prompt="test", image_base64="invalid base64")
        logger.info(f"Score for invalid data (should be 0.0): {score_error:.4f}")

    except Exception as e:
        logger.error(f"Error in test execution: {e}")
