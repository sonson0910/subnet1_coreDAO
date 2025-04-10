# Moderntensor - Subnet 1: Image Generation

Đây là triển khai cụ thể cho một subnet (mạng con) hoạt động trên nền tảng Moderntensor SDK. Subnet này tập trung vào bài toán **sinh ảnh từ mô tả văn bản (text-to-image generation)**.

## Giới thiệu

Subnet này cho phép các **Validators** đưa ra yêu cầu dưới dạng mô tả văn bản (prompts) và các **Miners** sử dụng các mô hình AI để tạo ra hình ảnh tương ứng với mô tả đó. Sau đó, Validators sẽ đánh giá chất lượng của hình ảnh được tạo ra (ví dụ: dựa trên mức độ phù hợp với prompt bằng cách sử dụng CLIP score) và tham gia vào cơ chế đồng thuận của Moderntensor SDK để xác định phần thưởng và điểm tin cậy.

Subnet này được xây dựng dựa trên và yêu cầu [Moderntensor SDK](https://github.com/sonson0910/moderntensor) (thay thế bằng link repo SDK thực tế của bạn nếu có).

## Tính năng

* Sinh ảnh từ văn bản sử dụng các model AI (ví dụ: Stable Diffusion).
* Chấm điểm ảnh tự động dựa trên sự phù hợp với prompt (ví dụ: CLIP score).
* Tích hợp với cơ chế đồng thuận, khuyến khích và xử phạt của Moderntensor SDK.
* Cho phép tùy chỉnh model sinh ảnh và model chấm điểm.

## Yêu cầu hệ thống

* Đã cài đặt **Moderntensor SDK** (xem hướng dẫn cài đặt của SDK).
* **Python** (khuyến nghị 3.10+).
* Môi trường ảo Python (`venv`, `conda`).
* Các thư viện Python cho AI được liệt kê trong `requirements.txt` (ví dụ: `torch`, `diffusers`, `transformers`, `clip`).
* Truy cập vào mạng **Cardano Testnet** (hoặc Mainnet tùy cấu hình).
* Một **Ví Cardano Testnet** đã được tạo (bằng SDK hoặc công cụ khác) và có một ít **tADA** để validator trả phí giao dịch.
* **Blockfrost Project ID** cho mạng Testnet (hoặc Mainnet).
* **Phần cứng:** Khuyến nghị sử dụng máy có GPU hỗ trợ (NVIDIA CUDA hoặc Apple Silicon MPS) để tăng tốc độ xử lý model AI.

## Cài đặt và Thiết lập

1.  **Clone Repository:**
    ```bash
    git clone <URL_REPO_SUBNET1_CUA_BAN>
    cd moderntensor-subnet1
    ```
2.  **Tạo và Kích hoạt Môi trường ảo:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    # .\.venv\Scripts\activate # Windows
    ```
3.  **Cài đặt Moderntensor SDK:**
    * Nếu SDK nằm cục bộ:
        ```bash
        pip install -e /path/to/your/moderntensor/sdk
        ```
    * Nếu SDK trên Github:
        ```bash
        pip install git+[https://github.com/sonson0910/moderntensor.git](https://github.com/sonson0910/moderntensor.git) # Thay link đúng
        ```
    * Hoặc nếu SDK đã được đóng gói và publish:
        ```bash
        pip install moderntensor # Thay tên package đúng
        ```
4.  **Cài đặt Dependencies của Subnet:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Tạo và Cấu hình file `.env`:**
    * Sao chép file `.env.example` (nếu có) thành `.env` hoặc tạo file `.env` mới ở thư mục gốc `moderntensor-subnet1`.
    * Điền các giá trị cần thiết (xem phần **Cấu hình** bên dưới). **Quan trọng:** Cần có thông tin key của validator, địa chỉ API, Blockfrost ID, v.v.
6.  **(Tùy chọn nhưng khuyến nghị) Chuẩn bị Datum trên Testnet:**
    * Đảm bảo bạn có một ví funding với tADA. Cấu hình thông tin ví funding trong `.env`.
    * Chạy script để tạo UTXO chứa Datum ban đầu cho validator và miner của subnet này trên Testnet:
        ```bash
        python scripts/prepare_testnet_datums.py
        ```
    * Việc này đảm bảo validator có thể đọc được thông tin miner (đặc biệt là `api_endpoint`) từ blockchain khi bắt đầu.

## Chạy Subnet

Subnet này sử dụng mô hình tích hợp `ValidatorRunner` từ SDK, nghĩa là tiến trình validator sẽ chạy cả logic đồng thuận và API server. Bạn cần chạy 2 tiến trình chính:

1.  **Chạy Validator (Logic + API Server):**
    * Mở Terminal 1.
    * `cd` vào thư mục `moderntensor-subnet1`.
    * Kích hoạt môi trường ảo.
    * Chạy script:
        ```bash
        python scripts/run_validator.py
        ```
    * Script này sẽ sử dụng `ValidatorRunner` để khởi động Uvicorn và chạy vòng lặp đồng thuận của `Subnet1Validator` trong nền. Nó sẽ lắng nghe các kết nối API trên host và port được cấu hình trong `.env` (ví dụ: `127.0.0.1:8001`).

2.  **Chạy Miner:**
    * Mở Terminal 2.
    * `cd` vào thư mục `moderntensor-subnet1`.
    * Kích hoạt môi trường ảo.
    * Chạy script:
        ```bash
        python scripts/run_miner.py
        ```
    * Miner sẽ khởi động, lắng nghe task trên cổng của nó (ví dụ: 9001) và gửi kết quả về địa chỉ API của validator đã cấu hình trong `.env`.

## Cấu hình

Các cấu hình quan trọng được quản lý thông qua file `.env` ở thư mục gốc `moderntensor-subnet1`. Dưới đây là các biến môi trường chính:

```dotenv
# Logging
LOG_LEVEL=INFO # DEBUG, INFO, WARNING, ERROR

# Cấu hình Cardano Context (chung cho cả 2 tiến trình nếu đọc cùng file)
BLOCKFROST_PROJECT_ID=preprod...your_id...
CARDANO_NETWORK=TESTNET # hoặc MAINNET

# --- Cấu hình cho Validator (dùng bởi scripts/run_validator.py) ---
# Key của Validator Subnet 1
HOTKEY_BASE_DIR=moderntensor # Thư mục chứa coldkeys (thường lấy từ SDK settings)
SUBNET1_COLDKEY_NAME=kickoff_validator # Tên coldkey chứa hotkey validator
SUBNET1_HOTKEY_NAME=hk_validator1    # Tên hotkey validator
SUBNET1_HOTKEY_PASSWORD=your_validator_password # Mật khẩu giải mã hotkey

# Thông tin định danh và API của Validator Subnet 1
SUBNET1_VALIDATOR_UID=validator_hex_uid_001 # UID hex duy nhất cho validator này
SUBNET1_VALIDATOR_ADDRESS=addr_test1q...     # Địa chỉ Cardano của hotkey validator
SUBNET1_VALIDATOR_API_ENDPOINT=[http://127.0.0.1:8001](http://127.0.0.1:8001) # URL công khai/có thể truy cập mà validator này lắng nghe

# Cấu hình Server API (cho ValidatorRunner)
SUBNET1_API_HOST=127.0.0.1 # IP validator lắng nghe (0.0.0.0 cho mọi interface)
SUBNET1_API_PORT=8001    # Cổng validator lắng nghe

# --- Cấu hình cho Miner (dùng bởi scripts/run_miner.py) ---
# URL Validator API mà Miner cần gửi kết quả đến
SUBNET1_VALIDATOR_URL=[http://127.0.0.1:8001/v1/miner/submit_result](http://127.0.0.1:8001/v1/miner/submit_result) # Phải khớp host/port của validator API

# Thông tin Miner
SUBNET1_MINER_ID=6d795f636f6f6c... # UID Hex của miner này (phải khớp với UID on-chain)
SUBNET1_MINER_HOST=127.0.0.1 # IP miner lắng nghe (0.0.0.0 cho mọi interface)
SUBNET1_MINER_PORT=9001    # Cổng miner lắng nghe

# --- (Tùy chọn) Cấu hình Ví Funding (dùng bởi prepare_testnet_datums.py) ---
# FUNDING_COLDKEY_NAME=...
# FUNDING_HOTKEY_NAME=...
# FUNDING_PASSWORD=...

# --- (Tùy chọn) Cấu hình Model AI ---
# IMAGEGEN_MODEL_ID="segmind/tiny-sd"
# CLIP_MODEL_NAME="ViT-B/32"
