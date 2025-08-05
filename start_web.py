#!/usr/bin/env python3
"""
EKS Advisor Web Dashboard Startup Script
Quick launcher for the web interface
"""

import sys
import subprocess
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    """Start the EKS Advisor web dashboard"""
    
    console.print(Panel("[bold blue]🚀 EKS Advisor Web Dashboard[/bold blue]", expand=False))
    console.print("Starting web server...")
    console.print("Dashboard will be available at: [bold blue]http://localhost:8000[/bold blue]")
    console.print("Press [bold red]Ctrl+C[/bold red] to stop\n")
    
    try:
        # Start the web application
        subprocess.run([
            sys.executable, "web_app.py"
        ], check=True)
    except KeyboardInterrupt:
        console.print("\n👋 Web dashboard stopped by user")
    except subprocess.CalledProcessError as e:
        console.print(f"\n❌ Error starting web dashboard: {e}")
        console.print("\n💡 Troubleshooting:")
        console.print("1. Make sure web dependencies are installed: [code]uv sync --extra web[/code]")
        console.print("2. Check if port 8000 is available")
        console.print("3. Verify cluster and Ollama connectivity")
    except Exception as e:
        console.print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()