#!/bin/bash

echo "🔧 Installing ModernTensor Aptos Dependencies..."
echo "================================================"

# Check if we're in a conda environment
if [[ "$CONDA_DEFAULT_ENV" != "" ]]; then
    echo "✅ Conda environment detected: $CONDA_DEFAULT_ENV"
else
    echo "⚠️  Warning: No conda environment detected. Consider activating 'aptos' environment:"
    echo "   conda activate aptos"
fi

echo ""
echo "📦 Installing core dependencies..."

# Core Python libraries
pip install numpy>=1.24.0 pandas>=2.0.0

echo "🖼️  Installing image processing and AI libraries..."

# Image processing and AI  
pip install Pillow>=10.0.0 diffusers>=0.21.0 transformers>=4.30.0
pip install torch>=2.0.0 accelerate>=0.20.0 sentencepiece>=0.1.99

echo "🌐 Installing web framework..."

# Web framework
pip install fastapi>=0.100.0 uvicorn>=0.23.0 aiohttp>=3.8.0

echo "🛠️  Installing utilities..."

# Utilities
pip install python-dotenv>=1.0.0 cryptography>=41.0.0 httpx>=0.24.0 rich>=13.0.0

echo "⚙️  Installing configuration and settings..."

# Configuration
pip install pydantic>=2.0.0 pydantic-settings>=2.0.0

echo "📝 Installing logging libraries..."

# Logging
pip install coloredlogs>=15.0.0 structlog>=23.0.0

echo "📊 Installing monitoring tools..."

# System monitoring
pip install psutil>=5.9.0 prometheus_client>=0.17.0

echo "🔗 Installing blockchain SDK..."

# Blockchain - Aptos
pip install aptos-sdk>=0.10.0

echo "🤖 Installing AI/ML dependencies..."

# AI/ML for scoring
pip install clip-by-openai>=1.0.1 scikit-learn>=1.3.0

echo "📋 Installing data serialization..."

# Data validation
pip install marshmallow>=3.19.0

echo "🚀 Installing performance optimization..."

# Performance
pip install orjson>=3.9.0

echo "🧪 Installing development tools (optional)..."

# Development tools
pip install pytest>=7.0.0 pytest-asyncio>=0.21.0 black>=23.0.0 flake8>=6.0.0

echo ""
echo "✅ All dependencies installed successfully!"
echo ""
echo "🧪 Running verification test..."
python test_aptos_migration.py

echo ""
echo "🎉 Setup complete! You can now run:"
echo "   python scripts/run_miner_aptos.py"
echo "   python scripts/run_validator_aptos.py" 