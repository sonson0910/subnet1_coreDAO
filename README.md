# Subnet1 - Core Blockchain Image Generation

This directory contains the implementation of Subnet1 for the ModernTensor network, migrated from Aptos to Core blockchain. Subnet1 specializes in image generation tasks using AI models and distributed validation.

## 🚀 Migration Status

**✅ COMPLETED**: Full migration from Aptos to Core blockchain
- All dependencies updated to use Core blockchain
- Smart contracts migrated to Solidity
- Network configuration updated
- Scripts and examples migrated
- Documentation updated

## 🏗️ Architecture

Subnet1 implements a distributed image generation network with:
- **Validators**: Assign image generation tasks and score results
- **Miners**: Execute image generation using AI models
- **Core Blockchain**: Handles consensus and rewards distribution

## 📁 Directory Structure

```
subnet1_aptos/
├── subnet1/                    # Core subnet implementation
│   ├── validator.py           # Validator logic for image scoring
│   ├── miner.py              # Miner logic for image generation
│   ├── models/               # AI model implementations
│   └── scoring/              # Image scoring algorithms
├── scripts/                   # Execution scripts
│   ├── run_validator_core.py  # Core blockchain validator runner
│   ├── run_miner_core.py     # Core blockchain miner runner
│   └── ...
├── tests/                     # Test files
├── requirements.txt          # Core blockchain dependencies
└── setup_keys_and_tokens.py  # Core blockchain setup script
```

## 🔧 Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Keys and Configuration

Run the setup script to create keys and configure the environment:

```bash
python setup_keys_and_tokens.py
```

This will:
- Create coldkey and hotkeys for validator/miner
- Configure Core blockchain network settings
- Request test tokens from faucet
- Generate `.env` configuration file

### 3. Configure Environment

Edit `.env` file with your specific configuration:

```env
# Core Blockchain Configuration
CORE_NODE_URL=https://rpc.test.btcs.network
CORE_CHAIN_ID=1115
CORE_CONTRACT_ADDRESS=0x1234567890abcdef1234567890abcdef12345678

# Validator Configuration
SUBNET1_VALIDATOR_ID=subnet1_validator_001
VALIDATOR_API_ENDPOINT=http://localhost:8001
CORE_PRIVATE_KEY=your_private_key_here

# Miner Configuration
SUBNET1_MINER_ID=subnet1_miner_001
SUBNET1_MINER_HOST=0.0.0.0
SUBNET1_MINER_PORT=9001
```

## 🚀 Running the Network

### Start Validator

```bash
python scripts/run_validator_core.py
```

### Start Miner

```bash
python scripts/run_miner_core.py
```

### Monitor Tokens

```bash
python monitor_tokens.py
```

## 🔍 Key Features

### Image Generation
- Uses state-of-the-art AI models (Stable Diffusion, etc.)
- Supports various image generation prompts
- Configurable model parameters

### Scoring System
- CLIP-based image-text similarity scoring
- Quality assessment algorithms
- Reward distribution based on performance

### Core Blockchain Integration
- Smart contracts for task distribution
- Transparent reward mechanisms
- Decentralized consensus

## 🛠️ Development

### Adding New Models

1. Implement model in `subnet1/models/`
2. Update `subnet1/miner.py` to support new model
3. Test with validator scoring system

### Custom Scoring

1. Add scoring function to `subnet1/scoring/`
2. Update `subnet1/validator.py` to use new scoring
3. Test with various image quality metrics

## 📚 Network Configuration

### Core Blockchain Networks

- **Testnet**: `https://rpc.test.btcs.network` (Chain ID: 1115)
- **Mainnet**: `https://rpc.coredao.org` (Chain ID: 1116)

### Faucet

Request test tokens from:
- **Testnet**: `https://faucet.test.btcs.network`

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `moderntensor_aptos` is installed
2. **Key Loading**: Check private key format and permissions
3. **Network Issues**: Verify Core blockchain node connectivity
4. **Token Balance**: Ensure sufficient CORE tokens for transactions

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python scripts/run_validator_core.py
```

## 📝 Migration Notes

This subnet has been migrated from Aptos to Core blockchain:
- Dependencies updated from `aptos-sdk` to `web3` and Core blockchain libraries
- Network configuration changed from Aptos endpoints to Core blockchain RPC
- Smart contracts migrated from Move to Solidity
- Account management updated for Ethereum-compatible addresses

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Documentation

- [ModernTensor Core Documentation](../moderntensor_aptos/README.md)
- [Core Blockchain Documentation](https://docs.coredao.org/)
- [Setup Guide](SETUP_GUIDE.md)
- [Migration Guide](MIGRATION_COMPLETED.md)
