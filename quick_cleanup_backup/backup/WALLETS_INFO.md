# 🔐 **Subnet1 Wallets Information**

**Generated Date:** January 28, 2025  
**Network:** Core Testnet (Chain ID: 1115)  
**Contract:** `0x56C2F2d0914DF10CE048e07EF1eCbac09AF80cd2`

---

## 🔨 **MINERS (2 entities)**

### **Miner 1 - subnet1_miner_001**
- **Address:** `0xd89fBAbb72190ed22F012ADFC693ad974bAD3005`
- **Private Key:** `e9c03148c011d553d43b485d73b1407d24f1498a664f782dc0204e524855be4e`
- **Stake Required:** 150 CORE tokens
- **Compute Power:** 8000
- **API Endpoint:** http://localhost:9001
- **Subnet ID:** 1

### **Miner 2 - subnet1_miner_002**
- **Address:** `0x16102CA8BEF74fb6214AF352989b664BF0e50498`
- **Private Key:** `3ace434e2cd05cd0e614eb5d423cf04e4b925c17db9869e9c598851f88f52840`
- **Stake Required:** 150 CORE tokens
- **Compute Power:** 8000
- **API Endpoint:** http://localhost:9002
- **Subnet ID:** 1

---

## ✅ **VALIDATORS (3 entities)**

### **Validator 1 - subnet1_validator_001**
- **Address:** `0x25F3D6316017FDF7A4f4e54003b29212a198768f`
- **Private Key:** `3ac6e82cf34e51d376395af0338d0b1162c1d39b9d34614ed40186fd2367b33d`
- **Stake Required:** 1200 CORE tokens
- **Compute Power:** 12000
- **API Endpoint:** http://localhost:8001
- **Subnet ID:** 1

### **Validator 2 - subnet1_validator_002**
- **Address:** `0x352516F491DFB3E6a55bFa9c58C551Ef10267dbB`
- **Private Key:** `df51093c674459eb0a5cc8a273418061fe4d7ca189bd84b74f478271714e0920`
- **Stake Required:** 1200 CORE tokens
- **Compute Power:** 12000
- **API Endpoint:** http://localhost:8002
- **Subnet ID:** 1

### **Validator 3 - subnet1_validator_003**
- **Address:** `0x0469C6644c07F6e860Af368Af8104F8D8829a78e`
- **Private Key:** `7e2c40ab431ddf141322ed93531e8e4b2cda01bb25aa947d297b680b635b715c`
- **Stake Required:** 1200 CORE tokens
- **Compute Power:** 12000
- **API Endpoint:** http://localhost:8003
- **Subnet ID:** 1

---

## 💰 **FAUCET INFORMATION**

### **Core Testnet Faucet**
- **URL:** https://scan.test.btcs.network/faucet
- **Network:** Core Testnet
- **Chain ID:** 1115

### **Request Tokens for All Addresses:**

```
0xd89fBAbb72190ed22F012ADFC693ad974bAD3005  # Miner 1
0x16102CA8BEF74fb6214AF352989b664BF0e50498  # Miner 2
0x25F3D6316017FDF7A4f4e54003b29212a198768f  # Validator 1
0x352516F491DFB3E6a55bFa9c58C551Ef10267dbB  # Validator 2
0x0469C6644c07F6e860Af368Af8104F8D8829a78e  # Validator 3
```

### **Token Requirements:**
- **Miners:** Minimum 150 CORE each (300 CORE total)
- **Validators:** Minimum 1200 CORE each (3600 CORE total)
- **Total Needed:** ~4000 CORE tokens

---

## 🔄 **IMPORT INSTRUCTIONS**

### **MetaMask/Web3 Wallet Import:**
1. Open MetaMask
2. Click "Import Account"
3. Select "Private Key"
4. Paste private key (without 0x prefix)
5. Add Core Testnet network:
   - **Network Name:** Core Testnet
   - **RPC URL:** https://rpc.test.btcs.network
   - **Chain ID:** 1115
   - **Symbol:** CORE
   - **Explorer:** https://scan.test.btcs.network

### **Command Line Import:**
```bash
# Using eth_account in Python
from eth_account import Account

# Example for Miner 1
private_key = "e9c03148c011d553d43b485d73b1407d24f1498a664f782dc0204e524855be4e"
account = Account.from_key(private_key)
print(f"Address: {account.address}")
```

---

## 🔐 **SECURITY WARNINGS**

⚠️ **CRITICAL SECURITY NOTES:**
1. **NEVER share private keys publicly**
2. **These are testnet wallets - for testing only**
3. **Do not use these addresses on mainnet**
4. **Keep private keys secure and backed up**
5. **Delete this file after noting the information**

---

## 📊 **QUICK REFERENCE TABLE**

| Entity | Type | Address | Port | Stake |
|--------|------|---------|------|-------|
| Miner 1 | 🔨 | 0xd89fBAbb...3005 | 9001 | 150 CORE |
| Miner 2 | 🔨 | 0x16102CA8...0498 | 9002 | 150 CORE |
| Validator 1 | ✅ | 0x25F3D631...768f | 8001 | 1200 CORE |
| Validator 2 | ✅ | 0x352516F4...7dbB | 8002 | 1200 CORE |
| Validator 3 | ✅ | 0x0469C664...a78e | 8003 | 1200 CORE |

---

## 🎯 **NEXT STEPS**

1. **💸 Request testnet tokens** for all 5 addresses
2. **📋 Verify balances** using Core testnet explorer
3. **🔄 Register entities** with smart contract:
   ```bash
   python manual_registration.py
   ```
4. **🚀 Start network:**
   ```bash
   python start_network.py
   ```

---

**📍 Contract Address:** `0x56C2F2d0914DF10CE048e07EF1eCbac09AF80cd2`  
**🔗 Explorer:** [View Contract](https://scan.test.btcs.network/address/0x56C2F2d0914DF10CE048e07EF1eCbac09AF80cd2) 