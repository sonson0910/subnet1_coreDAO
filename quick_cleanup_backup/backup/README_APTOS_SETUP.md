# Subnet1 Aptos Setup Guide

## Quick Start

This guide shows how to run Subnet1 (Image Generation AI) on Aptos blockchain after the migration from Cardano.

### Prerequisites

1. Python 3.8+
2. Aptos account with private key
3. Access to Aptos network (mainnet/testnet/devnet)

### Environment Configuration

Create a `.env` file in the subnet1 directory with the following variables:

```bash
# ===========================================
# ModernTensor Aptos Configuration
# ===========================================

# ----- Aptos Network Configuration -----
APTOS_NODE_URL=https://fullnode.mainnet.aptoslabs.com/v1
APTOS_CONTRACT_ADDRESS=0x1234567890abcdef1234567890abcdef12345678
APTOS_CHAIN_ID=1

# Private key for your Aptos account (64 hex characters)
# WARNING: Keep this secure and never commit to git!
APTOS_PRIVATE_KEY=your_private_key_here_64_hex_characters

# ----- Subnet1 (Image Generation) Configuration -----
SUBNET1_MINER_ID=miner_001
SUBNET1_VALIDATOR_ID=validator_001

# Miner Configuration
SUBNET1_MINER_HOST=0.0.0.0
SUBNET1_MINER_PORT=9001
SUBNET1_VALIDATOR_URL=http://localhost:8001/v1/miner/submit_result

# Validator Configuration  
SUBNET1_VALIDATOR_HOST=0.0.0.0
SUBNET1_VALIDATOR_PORT=8001
SUBNET1_VALIDATOR_API_ENDPOINT=http://localhost:8001
VALIDATOR_API_ENDPOINT=http://localhost:8001

# ----- Agent Configuration -----
MINER_AGENT_CHECK_INTERVAL=300

# ----- Logging Configuration -----
LOG_LEVEL=INFO
```

### Installation

1. **Activate conda environment (recommended):**
   ```bash
   conda activate aptos
   ```

2. **Install all dependencies (automated):**
   ```bash
   # Run the automated installation script
   ./install_dependencies.sh
   ```

   **OR install manually:**
   ```bash
   # For full development environment
   pip install -r requirements.txt
   
   # For production only
   pip install -r requirements-production.txt
   ```

3. **Verify installation:**
   ```bash
   python test_aptos_migration.py
   ```

### Dependencies Added

The migration to Aptos requires these additional packages:

#### Core Libraries
- `numpy>=1.24.0` - Numerical computations for consensus
- `pandas>=2.0.0` - Data manipulation and analysis

#### Configuration & Settings  
- `pydantic>=2.0.0` - Data validation and settings
- `pydantic-settings>=2.0.0` - Settings management

#### Logging & Monitoring
- `coloredlogs>=15.0.0` - Enhanced logging output
- `structlog>=23.0.0` - Structured logging
- `psutil>=5.9.0` - System resource monitoring  
- `prometheus_client>=0.17.0` - Metrics collection

#### Performance & Serialization
- `aiohttp>=3.8.0` - Async HTTP client
- `marshmallow>=3.19.0` - Object serialization
- `orjson>=3.9.0` - Fast JSON parsing

#### AI/ML (Production Ready)
- `clip-by-openai>=1.0.1` - CLIP model for image scoring
- `scikit-learn>=1.3.0` - Machine learning utilities

#### Development Tools (Optional)
- `pytest>=7.0.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async testing support
- `black>=23.0.0` - Code formatting
- `flake8>=6.0.0` - Code linting

### Running the Components

#### Run Validator

```