#!/bin/bash

echo "🚀 Setting up Pathfinding Comparison Project with Poetry"

# Check if pyenv is installed
if ! command -v pyenv &> /dev/null; then
    echo "📦 Installing pyenv..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux installation
        curl https://pyenv.run | bash
        export PATH="$HOME/.pyenv/bin:$PATH"
        eval "$(pyenv init -)"
        eval "$(pyenv init --path)"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS installation
        brew install pyenv
        echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bash_profile
        echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bash_profile
        echo 'eval "$(pyenv init --path)"' >> ~/.bash_profile
        echo 'eval "$(pyenv init -)"' >> ~/.bash_profile
        source ~/.bash_profile
    else
        echo "❌ Unsupported OS. Please install pyenv manually."
        exit 1
    fi
else
    echo "✅ pyenv already installed"
fi

# Ensure pyenv is in PATH for this session
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv init --path)"

# Install Python 3.11.5 if not available
REQUIRED_PYTHON="3.11.5"
if ! pyenv versions | grep -q "3.11.5"; then
    echo "🐍 Installing Python $REQUIRED_PYTHON..."
    pyenv install $REQUIRED_PYTHON
else
    echo "✅ Python 3.11.5 already available"
fi

# Set local Python version for this project
pyenv local 3.11.5

# Verify Python version
echo "🐍 Checking Python version..."
python --version

# Install Poetry if not already installed
if ! command -v poetry &> /dev/null; then
    echo "📦 Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "✅ Poetry already installed"
fi

# Install dependencies
echo "📦 Installing project dependencies..."
poetry install

# Verify installation
echo "✅ Setup complete!"
echo "🚀 You can now run:"
echo "   poetry run python main.py help"
echo "   poetry run python main.py demo"
echo "   poetry run python main.py test"
