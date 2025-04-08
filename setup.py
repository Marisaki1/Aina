#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import platform
import argparse
from pathlib import Path
import time
import json

def check_dependencies():
    """Check if required dependencies are installed."""
    print("✅ Checking dependencies...")
    
    # Check Docker
    try:
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("  ✓ Docker is installed")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("❌ Docker is not installed. Please install Docker first.")
        print("   Visit https://docs.docker.com/get-docker/ for installation instructions.")
        return False
    
    # Check Docker Compose
    try:
        # Try Docker Compose V2
        subprocess.run(["docker", "compose", "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("  ✓ Docker Compose is installed (V2)")
    except subprocess.SubprocessError:
        try:
            # Try Docker Compose V1
            subprocess.run(["docker-compose", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("  ✓ Docker Compose is installed (V1)")
        except (subprocess.SubprocessError, FileNotFoundError):
            print("❌ Docker Compose is not installed. Please install Docker Compose first.")
            print("   Visit https://docs.docker.com/compose/install/ for installation instructions.")
            return False
    
    # Check Python version
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ is required. You have Python {platform.python_version()}")
        return False
    else:
        print(f"  ✓ Python {platform.python_version()} is installed")
    
    # Check for conda
    try:
        subprocess.run(["conda", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("  ✓ Conda is installed")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("⚠️ Conda is not installed. We recommend using Conda for better environment management.")
        print("   Visit https://docs.conda.io/en/latest/miniconda.html for installation instructions.")
        
    # Check for pip
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("  ✓ Pip is installed")
    except subprocess.SubprocessError:
        print("❌ Pip is not installed. Please install pip first.")
        return False
    
    return True

def setup_discord_token():
    """Set up Discord token in .env file."""
    print("\n✅ Setting up Discord token...")
    
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            content = f.read()
            if "DISCORD_TOKEN=" in content:
                token = content.split("DISCORD_TOKEN=")[1].split("\n")[0]
                if token and token != "your_discord_token_here":
                    print("  ✓ Discord token already set")
                    return True
    
    token = input("Enter your Discord Bot Token (or press Enter to skip): ").strip()
    
    if not token:
        print("⚠️ Discord token not provided. You'll need to add it to .env file later.")
        token = "your_discord_token_here"
    
    with open(".env", "w") as f:
        f.write(f"DISCORD_TOKEN={token}\n")
    
    print("  ✓ Discord token saved to .env file")
    return True

def setup_qdrant():
    """Start Qdrant database using Docker Compose."""
    print("\n✅ Setting up Qdrant database...")
    
    if not os.path.exists("docker-compose.yml"):
        print("❌ docker-compose.yml not found. Creating a new one...")
        with open("docker-compose.yml", "w") as f:
            f.write("""version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:v1.2.0
    container_name: aina-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_storage:/qdrant/storage
    environment:
      - QDRANT_ALLOW_RECOVERY_MODE=true
    restart: unless-stopped

volumes:
  qdrant_storage:
    driver: local
""")
        print("  ✓ Created docker-compose.yml")
    
    # Start Qdrant
    try:
        print("  • Starting Qdrant (this may take a moment)...")
        subprocess.run(["docker", "compose", "up", "-d", "qdrant"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("  ✓ Qdrant database started successfully")
        
        # Wait for Qdrant to be ready
        max_attempts = 10
        for i in range(max_attempts):
            try:
                subprocess.run(
                    ["curl", "-s", "http://localhost:6333/health"],
                    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                print("  ✓ Qdrant is ready")
                break
            except subprocess.SubprocessError:
                if i == max_attempts - 1:
                    print("⚠️ Qdrant might not be fully initialized yet, but we'll continue")
                else:
                    print("  • Waiting for Qdrant to initialize...")
                    time.sleep(2)
        
        return True
    except subprocess.SubprocessError as e:
        print(f"❌ Failed to start Qdrant: {e}")
        print("   Please make sure Docker is running and try again.")
        return False

def setup_config_files():
    """Set up configuration files."""
    print("\n✅ Setting up configuration files...")
    
    # Create directories
    os.makedirs("data/aina/config", exist_ok=True)
    
    # Create memory config if it doesn't exist
    memory_config_path = "data/aina/config/memory_config.json"
    if not os.path.exists(memory_config_path):
        memory_config = {
            "qdrant_url": "localhost",
            "qdrant_port": 6333,
            "embedding_model": "all-MiniLM-L6-v2",
            "importance_threshold": 0.5,
            "recency_weight": 0.3,
            "relevance_weight": 0.5,
            "importance_weight": 0.2,
            "max_results": 10
        }
        
        with open(memory_config_path, "w") as f:
            json.dump(memory_config, f, indent=2)
        
        print(f"  ✓ Created memory configuration file: {memory_config_path}")
    else:
        print(f"  ✓ Memory configuration file already exists")
    
    # Create personality config if it doesn't exist
    personality_config_path = "data/aina/config/personality.json"
    if not os.path.exists(personality_config_path):
        personality_config = {
            "traits": {
                "cheerful": 0.8,
                "helpful": 0.9,
                "curious": 0.7,
                "kind": 0.9,
                "playful": 0.6,
                "thoughtful": 0.7
            },
            "speech_patterns": {
                "use_emoji": True,
                "uses_papa_reference": True,
                "formality_level": 0.3  # 0 = very informal, 1 = very formal
            },
            "preferences": {
                "likes": ["helping people", "learning new things", "making friends", "cats"],
                "dislikes": ["being interrupted", "forgetting things"]
            }
        }
        
        with open(personality_config_path, "w") as f:
            json.dump(personality_config, f, indent=2)
        
        print(f"  ✓ Created personality configuration file: {personality_config_path}")
    else:
        print(f"  ✓ Personality configuration file already exists")
    
    return True

def setup_environment():
    """Set up Python environment."""
    print("\n✅ Setting up Python environment...")
    
    # Check if conda is available
    conda_available = False
    try:
        subprocess.run(["conda", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        conda_available = True
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    # Set up environment with Conda if available
    if conda_available:
        print("  • Using Conda to create environment...")
        
        # Check if environment already exists
        try:
            process = subprocess.run(
                ["conda", "env", "list"], 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            if "aina-env" in process.stdout:
                print("  ✓ Conda environment 'aina-env' already exists")
                update = input("  • Update environment with latest dependencies? (y/n): ").strip().lower()
                if update == 'y':
                    subprocess.run(
                        ["conda", "env", "update", "-f", "environment.yml"], 
                        check=True, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE
                    )
                    print("  ✓ Updated Conda environment")
            else:
                # Create new environment
                print("  • Creating Conda environment 'aina-env'...")
                subprocess.run(
                    ["conda", "env", "create", "-f", "environment.yml"], 
                    check=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
                print("  ✓ Created Conda environment 'aina-env'")
        except subprocess.SubprocessError as e:
            print(f"❌ Failed to set up Conda environment: {e}")
            print("   Falling back to pip...")
            conda_available = False
    
    # Use pip if Conda is not available or failed
    if not conda_available:
        print("  • Using pip to install dependencies...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            print("  ✓ Installed dependencies with pip")
        except subprocess.SubprocessError as e:
            print(f"❌ Failed to install dependencies with pip: {e}")
            return False
    
    return True

def setup_model_files():
    """Set up LLM model files."""
    print("\n✅ Setting up model files...")
    
    # Create models directory
    os.makedirs("models", exist_ok=True)
    os.makedirs("models/embeddings", exist_ok=True)
    
    # Check for any .gguf files in the models directory
    model_files = [f for f in os.listdir("models") if f.endswith(".gguf")]
    
    if model_files:
        print(f"  ✓ Found {len(model_files)} model files:")
        for model in model_files:
            model_path = os.path.join("models", model)
            size_mb = os.path.getsize(model_path) / (1024 * 1024)
            print(f"    - {model} ({size_mb:.1f} MB)")
    else:
        print("⚠️ No model files found in the 'models' directory.")
        print("   You'll need to manually add a .gguf model file to the 'models' directory.")
        print("   For better performance with the RTX 4070 Super, we recommend:")
        print("   - airoboros-mistral2.2-7b.Q4_K_S.gguf")
        print("   - or a similar Mistral-based model")
        print("   Download from: https://huggingface.co/TheBloke")
    
    return True

def main():
    """Main setup function."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Set up Aina Discord Bot")
    parser.add_argument("--skip-docker", action="store_true", help="Skip Docker and Qdrant setup")
    parser.add_argument("--skip-env", action="store_true", help="Skip environment setup")
    parser.add_argument("--skip-config", action="store_true", help="Skip config files setup")
    parser.add_argument("--skip-models", action="store_true", help="Skip model files check")
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print(" " * 20 + "AINA SETUP WIZARD")
    print("="*60 + "\n")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install the required dependencies and try again.")
        return 1
    
    # Set up Discord token
    if not setup_discord_token():
        print("\n⚠️ Failed to set up Discord token. You'll need to set it manually.")
    
    # Set up Qdrant database
    if not args.skip_docker:
        if not setup_qdrant():
            print("\n⚠️ Failed to set up Qdrant database. You'll need to set it up manually.")
    else:
        print("\n⚠️ Skipping Qdrant setup. Make sure it's running or use docker-compose.yml to start it.")
    
    # Set up config files
    if not args.skip_config:
        if not setup_config_files():
            print("\n⚠️ Failed to set up configuration files. You'll need to set them up manually.")
    else:
        print("\n⚠️ Skipping config files setup.")
    
    # Set up environment
    if not args.skip_env:
        if not setup_environment():
            print("\n⚠️ Failed to set up environment. You'll need to set it up manually.")
    else:
        print("\n⚠️ Skipping environment setup. Make sure to install dependencies.")
    
    # Set up model files
    if not args.skip_models:
        if not setup_model_files():
            print("\n⚠️ Failed to set up model files. You'll need to set them up manually.")
    else:
        print("\n⚠️ Skipping model files check. Make sure to add model files to the 'models' directory.")
    
    # Setup complete
    print("\n" + "="*60)
    print(" " * 20 + "SETUP COMPLETE")
    print("="*60)
    print("\n✅ To start the Discord bot, run:")
    
    if subprocess.run(["conda", "--version"], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
        print("   conda activate aina-env")
        print("   python aina_discord.py")
    else:
        print("   python aina_discord.py")
    
    print("\n✅ To start the terminal interface, run:")
    if subprocess.run(["conda", "--version"], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
        print("   conda activate aina-env")
        print("   python aina_terminal.py")
    else:
        print("   python aina_terminal.py")
    
    print("\n👋 Thank you for setting up Aina! Enjoy your AI assistant with memory!")
    return 0

if __name__ == "__main__":
    sys.exit(main())