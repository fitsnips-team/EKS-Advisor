#!/usr/bin/env python3
"""
Ollama Setup Helper
Helps users set up Ollama for local LLM processing
"""

import os
import subprocess
import time
import platform
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def check_ollama_installed():
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def install_ollama():
    """Install Ollama based on the operating system"""
    
    system = platform.system().lower()
    
    console.print(Panel("[bold blue]Installing Ollama for Local LLM Processing[/bold blue]"))
    
    if system == "darwin":  # macOS
        console.print("🍎 Detected macOS")
        console.print("Please install Ollama manually:")
        console.print("1. Visit: https://ollama.ai/download")
        console.print("2. Download the macOS installer")
        console.print("3. Install and run Ollama")
        return False
        
    elif system == "linux":
        console.print("🐧 Detected Linux - Installing Ollama...")
        try:
            # Download and run install script
            install_cmd = "curl -fsSL https://ollama.ai/install.sh | sh"
            result = subprocess.run(install_cmd, shell=True, check=True)
            console.print("✅ Ollama installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"❌ Failed to install Ollama: {e}")
            return False
            
    elif system == "windows":
        console.print("🪟 Detected Windows")
        console.print("Please install Ollama manually:")
        console.print("1. Visit: https://ollama.ai/download")
        console.print("2. Download the Windows installer")
        console.print("3. Install and run Ollama")
        return False
    
    else:
        console.print(f"❓ Unsupported system: {system}")
        return False

def start_ollama_service():
    """Start the Ollama service"""
    
    console.print("🚀 Starting Ollama service...")
    
    try:
        # Start Ollama in background
        if platform.system().lower() == "linux":
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        else:
            console.print("Please start Ollama manually:")
            console.print("Run: ollama serve")
            return False
        
        # Wait for service to start
        time.sleep(3)
        
        # Test connection
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            console.print("✅ Ollama service is running")
            return True
        else:
            console.print("❌ Failed to start Ollama service")
            return False
            
    except Exception as e:
        console.print(f"❌ Error starting Ollama: {e}")
        return False

def pull_recommended_models():
    """Pull recommended models for EKS analysis"""
    
    recommended_models = [
        {
            'name': 'llama3.1:8b',
            'size': '4.7GB',
            'description': 'Fast analysis, good for alerts and quick recommendations',
            'recommended': True
        },
        {
            'name': 'llama3.1:70b', 
            'size': '40GB',
            'description': 'Deep analysis, best quality but requires more resources',
            'recommended': False
        },
        {
            'name': 'mistral:7b',
            'size': '4.1GB', 
            'description': 'Alternative fast model, good performance',
            'recommended': False
        }
    ]
    
    console.print("\n📦 Available Models for EKS Analysis:")
    
    for model in recommended_models:
        status = "🌟 RECOMMENDED" if model['recommended'] else "⭐ Optional"
        console.print(f"{status} {model['name']} ({model['size']}) - {model['description']}")
    
    # Ask user which models to install
    console.print("\n🤔 Which model would you like to install?")
    console.print("1. llama3.1:8b (Recommended - fast and efficient)")
    console.print("2. llama3.1:70b (Best quality - requires 80GB+ RAM)")
    console.print("3. mistral:7b (Alternative fast model)")
    console.print("4. All models")
    console.print("5. Skip model installation")
    
    try:
        choice = input("\nEnter your choice (1-5): ").strip()
        
        models_to_pull = []
        if choice == "1":
            models_to_pull = ["llama3.1:8b"]
        elif choice == "2":
            models_to_pull = ["llama3.1:70b"]
        elif choice == "3":
            models_to_pull = ["mistral:7b"]
        elif choice == "4":
            models_to_pull = ["llama3.1:8b", "llama3.1:70b", "mistral:7b"]
        elif choice == "5":
            console.print("⏭️  Skipping model installation")
            return True
        else:
            console.print("❌ Invalid choice, using default (llama3.1:8b)")
            models_to_pull = ["llama3.1:8b"]
        
        # Pull selected models
        for model in models_to_pull:
            console.print(f"\n📥 Pulling {model}...")
            
            with Progress(
                SpinnerColumn(),
                TextColumn(f"Downloading {model}..."),
                console=console
            ) as progress:
                task = progress.add_task("Downloading...", total=None)
                
                try:
                    result = subprocess.run(['ollama', 'pull', model], 
                                          capture_output=True, text=True, timeout=1800)  # 30 min timeout
                    
                    if result.returncode == 0:
                        progress.update(task, description=f"✅ {model} installed successfully")
                        console.print(f"✅ {model} is ready for use")  
                    else:
                        console.print(f"❌ Failed to pull {model}: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    console.print(f"⏰ Timeout pulling {model} - you can continue the download later")
                except Exception as e:
                    console.print(f"❌ Error pulling {model}: {e}")
        
        return True
        
    except KeyboardInterrupt:
        console.print("\n⏹️  Installation cancelled by user")
        return False

def verify_setup():
    """Verify that Ollama is properly set up"""
    
    console.print("\n🔍 Verifying Ollama setup...")
    
    # Check if service is running
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode != 0:
            console.print("❌ Ollama service is not running")
            return False
    except Exception as e:
        console.print(f"❌ Cannot connect to Ollama: {e}")
        return False
    
    # List available models
    models = result.stdout.strip().split('\n')[1:]  # Skip header
    if not models or (len(models) == 1 and models[0] == ''):
        console.print("⚠️  No models installed. Run 'ollama pull llama3.1:8b' to install a model")
        return False
    
    console.print("✅ Ollama is properly configured!")
    console.print("📋 Installed models:")
    for model in models:
        if model.strip():
            console.print(f"   • {model.split()[0]}")
    
    return True

def create_env_file():
    """Create or update .env file with Ollama configuration"""
    
    env_path = ".env"
    
    # Read existing .env if it exists
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    
    # Set Ollama configuration
    env_vars['LLM_PROVIDER'] = 'ollama'
    env_vars['OLLAMA_BASE_URL'] = 'http://localhost:11434'
    env_vars['OLLAMA_MODEL'] = 'llama3.1:8b'
    env_vars['LOCAL_PROCESSING_ONLY'] = 'true'
    env_vars['ENABLE_DATA_REDACTION'] = 'true'
    env_vars['AUDIT_LOGGING'] = 'true'
    
    # Write updated .env file
    with open(env_path, 'w') as f:
        f.write("# EKS Advisor Configuration - Local Processing with Ollama\n\n")
        f.write("# LLM Configuration\n")
        f.write(f"LLM_PROVIDER={env_vars['LLM_PROVIDER']}\n")
        f.write(f"OLLAMA_BASE_URL={env_vars['OLLAMA_BASE_URL']}\n") 
        f.write(f"OLLAMA_MODEL={env_vars['OLLAMA_MODEL']}\n\n")
        f.write("# Security Settings\n")
        f.write(f"LOCAL_PROCESSING_ONLY={env_vars['LOCAL_PROCESSING_ONLY']}\n")
        f.write(f"ENABLE_DATA_REDACTION={env_vars['ENABLE_DATA_REDACTION']}\n")
        f.write(f"AUDIT_LOGGING={env_vars['AUDIT_LOGGING']}\n\n")
        f.write("# Kubernetes Configuration\n")
        f.write(f"KUBECONFIG={env_vars.get('KUBECONFIG', '~/.kube/config')}\n")
        f.write(f"CLUSTER_NAME={env_vars.get('CLUSTER_NAME', 'my-eks-cluster')}\n")
    
    console.print(f"✅ Created {env_path} with Ollama configuration")

def main():
    """Main setup function"""
    
    console.print(Panel("[bold green]EKS Advisor - Ollama Setup for Maximum Privacy[/bold green]"))
    console.print("This setup will configure local LLM processing with Ollama")
    console.print("🔒 Benefits: Complete privacy, no data leaves your machine, no API costs\n")
    
    # Check if already installed
    if check_ollama_installed():
        console.print("✅ Ollama is already installed")
        
        if verify_setup():
            console.print("\n🎉 Ollama is ready to use!")
            create_env_file()
            console.print("\n🚀 You can now run: python run_demo.py")
            return
        else:
            console.print("🔧 Ollama needs configuration...")
    else:
        console.print("📦 Ollama not found - installing...")
        if not install_ollama():
            console.print("❌ Manual installation required")
            return
    
    # Start service
    if not start_ollama_service():
        console.print("❌ Please start Ollama manually: ollama serve")
        return
    
    # Pull models
    pull_recommended_models()
    
    # Verify setup
    if verify_setup():
        create_env_file()
        console.print("\n🎉 Setup complete!")
        console.print("🚀 You can now run: python run_demo.py")
        console.print("🔒 All processing will be done locally for maximum privacy")
    else:
        console.print("❌ Setup incomplete - please check the errors above")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n⏹️  Setup cancelled by user")
    except Exception as e:
        console.print(f"\n❌ Setup error: {e}")
        console.print("Please try manual installation: https://ollama.ai/download")