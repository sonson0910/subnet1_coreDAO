# Subnet1 Setup Guide - Tạo Key và Xin Token

Hướng dẫn đầy đủ để setup key và token cho Subnet1 trên Aptos blockchain.

## 📋 Prerequisites

1. **Python 3.8+** đã cài đặt
2. **ModernTensor Aptos SDK** đã cài đặt:
   ```bash
   cd /path/to/moderntensor_aptos
   pip install -e .
   ```
3. **Internet connection** để kết nối Aptos network và faucet

## 🚀 Quick Start (Khuyến nghị)

### Option 1: Script Tự Động Đơn Giản

```bash
cd subnet1
python quick_keygen.py
```

Script này sẽ:
- ✅ Tạo validator và miner accounts
- ✅ Xin token từ testnet faucet
- ✅ Lưu config vào file `.env`
- ✅ Backup keys vào `keys_backup.txt`

### Option 2: Setup Chi Tiết Với Rich UI

```bash
cd subnet1  
python setup_keys_and_tokens.py
```

Script này cung cấp:
- 🌐 Lựa chọn network (Testnet/Devnet/Mainnet)
- 🔑 Quản lý key theo wallet system (coldkey/hotkey)
- 💰 Request tokens với validation
- 📊 Balance checking và monitoring

## 🔍 Kiểm Tra Setup

Sau khi setup xong, kiểm tra configuration:

```bash
cd subnet1
python check_setup.py
```

Script này sẽ validate:
- ✅ Configuration files
- ✅ Private key integrity  
- ✅ Network connectivity
- ✅ Account balances
- ✅ Required file structure

## 📁 File Structure Sau Setup

```
subnet1/
├── .env                    # Configuration file
├── keys_backup.txt         # Key backup (keep safe!)
├── wallets/               # Wallet storage (nếu dùng setup_keys_and_tokens.py)
├── scripts/
│   ├── run_validator_aptos.py
│   └── run_miner_aptos.py
└── subnet1/
    ├── validator.py
    └── miner.py
```

## ⚙️ Configuration Variables

Các biến trong file `.env`:

### Network Configuration
```bash
APTOS_NODE_URL=https://fullnode.testnet.aptoslabs.com/v1
APTOS_CHAIN_ID=2
APTOS_CONTRACT_ADDRESS=0x1234567890abcdef1234567890abcdef12345678
```

### Validator Configuration  
```bash
SUBNET1_VALIDATOR_ID=subnet1_validator_001
SUBNET1_VALIDATOR_HOST=0.0.0.0
SUBNET1_VALIDATOR_PORT=8001
VALIDATOR_API_ENDPOINT=http://localhost:8001
APTOS_PRIVATE_KEY=your_validator_private_key_hex
VALIDATOR_ADDRESS=your_validator_address
```

### Miner Configuration
```bash
SUBNET1_MINER_ID=subnet1_miner_001
SUBNET1_MINER_HOST=0.0.0.0
SUBNET1_MINER_PORT=9001
SUBNET1_VALIDATOR_URL=http://localhost:8001/v1/miner/submit_result
SUBNET1_VALIDATOR_API_ENDPOINT=http://localhost:8001
MINER_PRIVATE_KEY=your_miner_private_key_hex
MINER_ADDRESS=your_miner_address
```

## 🚦 Chạy Subnet1

### 1. Chạy Validator

```bash
cd subnet1
python scripts/run_validator_aptos.py
```

### 2. Chạy Miner (Terminal mới)

```bash  
cd subnet1
python scripts/run_miner_aptos.py
```

## 🔧 Troubleshooting

### Lỗi Import
```bash
❌ Import Error: No module named 'mt_aptos'
```
**Giải pháp:**
```bash
cd /path/to/moderntensor_aptos
pip install -e .
```

### Lỗi Network Connection
```bash
❌ Network connection failed
```
**Kiểm tra:**
- Internet connection
- APTOS_NODE_URL trong .env
- Firewall settings

### Lỗi Insufficient Funds
```bash
❌ Insufficient funds for transaction
```
**Giải pháp:**
1. Kiểm tra balance: `python check_setup.py`
2. Request thêm token từ faucet:
   ```bash
   # Testnet faucet
   curl -X POST https://faucet.testnet.aptoslabs.com/mint \
        -H "Content-Type: application/json" \
        -d '{"address": "YOUR_ADDRESS", "amount": 100000000}'
   ```

### Contract Address Chưa Cập Nhật
```bash
⚠️ Update APTOS_CONTRACT_ADDRESS with real contract address
```
**Giải pháp:** Cập nhật `APTOS_CONTRACT_ADDRESS` trong `.env` với địa chỉ contract thực tế.

## 💡 Best Practices

### 🔐 Security
- ✅ **Backup keys** vào nơi an toàn
- ✅ **Không commit** `.env` và `keys_backup.txt` 
- ✅ **Sử dụng strong passwords** cho coldkey encryption
- ✅ **Rotate keys** định kỳ cho production

### 🚀 Performance  
- ✅ **Monitor balances** thường xuyên
- ✅ **Use testnet** cho development
- ✅ **Set appropriate intervals** cho agent checking
- ✅ **Monitor logs** để debug issues

### 📊 Monitoring
```bash
# Check setup
python check_setup.py

# Monitor logs
tail -f /path/to/logs/subnet1.log

# Check processes
ps aux | grep "subnet1"
```

## 🌐 Network Information

### Testnet (Recommended for Development)
- **Node URL:** https://fullnode.testnet.aptoslabs.com/v1
- **Faucet:** https://faucet.testnet.aptoslabs.com
- **Chain ID:** 2
- **Explorer:** https://explorer.aptoslabs.com/?network=testnet

### Devnet (Cho Testing Mới Nhất)
- **Node URL:** https://fullnode.devnet.aptoslabs.com/v1  
- **Faucet:** https://faucet.devnet.aptoslabs.com
- **Chain ID:** 42
- **Explorer:** https://explorer.aptoslabs.com/?network=devnet

### Mainnet (Production)
- **Node URL:** https://fullnode.mainnet.aptoslabs.com/v1
- **Faucet:** Không có (cần mua APT)
- **Chain ID:** 1
- **Explorer:** https://explorer.aptoslabs.com/?network=mainnet

## 📞 Support

Nếu gặp vấn đề:
1. Chạy `python check_setup.py` để kiểm tra
2. Xem logs trong terminal
3. Kiểm tra file `.env` configuration
4. Ensure all dependencies installed correctly

## 🔄 Migration Notes

Subnet1 đã được migrate từ Cardano sang Aptos:
- ✅ Validator logic đã được port
- ✅ Miner functionality đã được update  
- ✅ Consensus mechanism đã được adapt
- ✅ Key management đã được modernize

Tham khảo `MIGRATION_COMPLETED.md` để biết chi tiết migration process. 