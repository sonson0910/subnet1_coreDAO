# Subnet1 - Migration từ Cardano sang Aptos

## 🚀 Tổng quan

Subnet1 đã được chuyển đổi hoàn toàn từ **Cardano** sang **Aptos blockchain**. Đây là subnet chuyên về **Image Generation** sử dụng AI models.

## 📋 Những thay đổi chính

### 1. **Blockchain Platform**
- ❌ **Trước**: Cardano + PyCardano + Blockfrost
- ✅ **Sau**: Aptos + Aptos SDK + Rest API

### 2. **SDK Package Structure**
- ❌ **Trước**: `from sdk.consensus.node import ValidatorNode`
- ✅ **Sau**: `from mt_aptos.consensus.node import ValidatorNode`

### 3. **Account & Keys Management**
- ❌ **Trước**: ExtendedSigningKey (Cardano)
- ✅ **Sau**: Account (Aptos)

### 4. **Configuration**
- ❌ **Trước**: BLOCKFROST_PROJECT_ID, CARDANO_NETWORK
- ✅ **Sau**: APTOS_NODE_URL, APTOS_CONTRACT_ADDRESS

## 🛠️ Cài đặt

### 1. Cài đặt ModernTensor Aptos SDK

```bash
cd /path/to/moderntensor_aptos/moderntensor
pip install -e .
```

### 2. Cài đặt dependencies cho Subnet1

```bash
cd /path/to/subnet1
pip install -r requirements.txt
```

### 3. Cấu hình Environment

Sao chép file cấu hình mẫu:
```bash
cp .env.aptos.example .env
```

Chỉnh sửa `.env` với thông tin của bạn:

```bash
# === APTOS CONFIGURATION ===
APTOS_NODE_URL=https://fullnode.testnet.aptoslabs.com/v1
APTOS_FAUCET_URL=https://faucet.testnet.aptoslabs.com
APTOS_CONTRACT_ADDRESS=0x123...your_contract_address

# === VALIDATOR CONFIG ===
SUBNET1_VALIDATOR_UID=validator_001_subnet1_hex
SUBNET1_VALIDATOR_ADDRESS=0xabc...your_validator_aptos_address
SUBNET1_VALIDATOR_API_ENDPOINT=http://127.0.0.1:8001

# === MINER CONFIG ===
SUBNET1_MINER_ID=my_cool_image_miner_01
SUBNET1_MINER_APTOS_ADDRESS=0x123...your_miner_aptos_address

# === KEYS ===
MINER_COLDKEY_NAME=miner1
MINER_HOTKEY_NAME=hk1
MINER_HOTKEY_PASSWORD=your_password_here
```

## 🏃‍♂️ Chạy Subnet1

### 1. Chạy Validator

```bash
cd scripts
python run_validator.py
```

### 2. Chạy Miner

```bash
cd scripts  
python run_miner.py
```

## 🔧 Kiến trúc hệ thống

### Validator Node
- **Base Class**: `mt_aptos.consensus.node.ValidatorNode`
- **Subnet Class**: `subnet1.validator.Subnet1Validator`
- **Chức năng**: Tạo tasks (image prompts), nhận kết quả từ miners, chấm điểm bằng CLIP

### Miner Node
- **Base Class**: `mt_aptos.network.server.BaseMiner`
- **Subnet Class**: `subnet1.miner.Subnet1Miner`
- **Chức năng**: Nhận prompts, generate images, gửi kết quả về validator

### Task Flow
1. **Validator** tạo random prompt từ `DEFAULT_PROMPTS`
2. **Validator** gửi task đến **Miner** qua HTTP API
3. **Miner** nhận task, generate image từ prompt
4. **Miner** encode image thành base64, gửi về **Validator**
5. **Validator** chấm điểm bằng CLIP score
6. **Validator** cập nhật scores lên Aptos blockchain

## 🔑 Key Management

### Tạo Coldkey & Hotkey

```bash
# Sử dụng moderntensor CLI
moderntensor coldkey create --name miner1
moderntensor hotkey create --name hk1 --coldkey miner1
```

### Lấy Aptos Address

```bash
# Lấy address từ hotkey
moderntensor address --hotkey hk1 --coldkey miner1
```

## 🧪 Testing

```bash
# Test import
python -c "
import mt_aptos
from subnet1.validator import Subnet1Validator
from subnet1.miner import Subnet1Miner
print('✅ All imports successful!')
"

# Test validator script
python scripts/run_validator.py --help

# Test miner script  
python scripts/run_miner.py --help
```

## 🚨 Troubleshooting

### Import Errors
```bash
# Nếu gặp lỗi import mt_aptos
pip uninstall moderntensor
cd /path/to/moderntensor_aptos/moderntensor
pip install -e .
```

### Key Errors
```bash
# Kiểm tra thư mục keys
ls -la moderntensor/  # Should show coldkeys

# Kiểm tra hotkey
ls -la moderntensor/your_coldkey_name/hotkeys/
```

### Missing Dependencies
```bash
# Cài đặt đầy đủ
pip install aptos-sdk torch transformers pillow clip-by-openai
```

## 📝 Các thay đổi code quan trọng

### 1. Validator Changes
```python
# OLD (Cardano)
from sdk.consensus.node import ValidatorNode
from pycardano import ExtendedSigningKey

# NEW (Aptos) 
from mt_aptos.consensus.node import ValidatorNode
from mt_aptos.account import Account
```

### 2. Miner Changes
```python
# OLD (Cardano)
from sdk.network.server import BaseMiner
miner_skey = decode_hotkey_skey(...)

# NEW (Aptos)
from mt_aptos.network.server import BaseMiner  
miner_account = decode_hotkey_account(...)
```

### 3. Configuration Changes
```python
# OLD (Cardano)
"blockfrost_project_id": settings.BLOCKFROST_PROJECT_ID,
"network": Network.TESTNET,

# NEW (Aptos)
"aptos_node_url": settings.APTOS_TESTNET_URL,
"contract_address": settings.CONTRACT_ADDRESS,
```

## 🎯 Kết quả

✅ **Hoàn tất migration từ Cardano → Aptos**
✅ **Package structure**: `sdk.` → `mt_aptos.`
✅ **Scripts updated**: `run_validator.py`, `run_miner.py`
✅ **Configuration**: `.env` với Aptos settings
✅ **Key management**: Aptos Account thay vì Cardano keys
✅ **Backward compatible**: Subnet logic không đổi

Subnet1 giờ đây đã sẵn sàng chạy trên Aptos blockchain! 🚀 