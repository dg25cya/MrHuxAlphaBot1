#!/usr/bin/env python3
"""
Hux Alpha Bot - Automated Deployment Script
The best alpha bot deployment system
"""

import os
import sys
import subprocess
import time
import signal
import json
from pathlib import Path
from typing import Optional, Union

class HuxAlphaBotDeployer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.processes = []
        self.is_running = False
        
    def log(self, message: str):
        """Log with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def run_command(self, command: str, cwd: Optional[str] = None, check: bool = True) -> Union[subprocess.CompletedProcess, subprocess.CalledProcessError]:
        """Run a shell command with proper error handling"""
        self.log(f"Running: {command}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or str(self.project_root),
                capture_output=True,
                text=True,
                check=check
            )
            if result.stdout:
                print(result.stdout)
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {e}")
            if e.stderr:
                print(f"Error: {e.stderr}")
            if check:
                raise
            return e
            
    def check_python_version(self):
        """Check Python version compatibility"""
        self.log("Checking Python version...")
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            raise RuntimeError("Python 3.9+ is required")
        self.log(f"Python {version.major}.{version.minor}.{version.micro} ✓")
        
    def install_dependencies(self):
        """Install Python dependencies"""
        self.log("Installing dependencies...")
        
        # Upgrade pip
        self.run_command("python -m pip install --upgrade pip")
        
        # Install requirements
        if (self.project_root / "requirements.txt").exists():
            self.run_command("pip install -r requirements.txt")
        else:
            self.log("No requirements.txt found, installing common dependencies...")
            common_deps = [
                "fastapi",
                "uvicorn[standard]",
                "sqlalchemy",
                "alembic",
                "prometheus-client",
                "loguru",
                "httpx",
                "bcrypt",
                "python-multipart",
                "websockets",
                "asyncio-mqtt",
                "psutil"
            ]
            for dep in common_deps:
                self.run_command(f"pip install {dep}")
                
    def setup_database(self):
        """Setup and migrate database"""
        self.log("Setting up database...")
        
        # Run database migrations
        try:
            self.run_command("python migrate_database.py")
        except subprocess.CalledProcessError:
            self.log("Database migration failed, attempting to create fresh database...")
            self.run_command("python scripts/setup_database.py")
            
    def check_environment(self):
        """Check environment variables and configuration"""
        self.log("Checking environment configuration...")
        
        # Check for .env file
        env_file = self.project_root / ".env"
        if not env_file.exists():
            self.log("Creating default .env file...")
            default_env = """
# Hux Alpha Bot Configuration
DATABASE_URL=sqlite:///./hux_alpha_bot.db
LOG_LEVEL=INFO
ENVIRONMENT=development
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
            """.strip()
            env_file.write_text(default_env)
            self.log("Created .env file with default values. Please update with your actual credentials.")
            
    def start_application(self):
        """Start the FastAPI application"""
        self.log("Starting Hux Alpha Bot...")
        
        # Start the application
        cmd = [
            "uvicorn",
            "src.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ]
        
        self.log(f"Starting with command: {' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes.append(process)
            self.is_running = True
            
            # Monitor the process
            while self.is_running and process.poll() is None:
                if process.stdout is not None:
                    output = process.stdout.readline()
                    if output:
                        print(output.strip())
                    
            if process.returncode != 0:
                self.log(f"Application exited with code {process.returncode}")
                
        except KeyboardInterrupt:
            self.log("Received interrupt signal, shutting down...")
            self.stop_application()
            
    def stop_application(self):
        """Stop all running processes"""
        self.log("Stopping application...")
        self.is_running = False
        
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                self.log(f"Error stopping process: {e}")
                
        self.processes.clear()
        
    def health_check(self):
        """Perform health check on the application"""
        self.log("Performing health check...")
        
        import requests
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                self.log("Health check passed ✓")
                return True
            else:
                self.log(f"Health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"Health check failed: {e}")
            return False
            
    def deploy(self):
        """Main deployment process"""
        try:
            self.log("🚀 Starting Hux Alpha Bot Deployment")
            self.log("=" * 50)
            
            # Check Python version
            self.check_python_version()
            
            # Check environment
            self.check_environment()
            
            # Install dependencies
            self.install_dependencies()
            
            # Setup database
            self.setup_database()
            
            # Start application
            self.start_application()
            
        except KeyboardInterrupt:
            self.log("Deployment interrupted by user")
        except Exception as e:
            self.log(f"Deployment failed: {e}")
            raise
        finally:
            self.stop_application()
            
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.log(f"Received signal {signum}, shutting down gracefully...")
        self.stop_application()
        sys.exit(0)

def main():
    """Main entry point"""
    deployer = HuxAlphaBotDeployer()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, deployer.signal_handler)
    signal.signal(signal.SIGTERM, deployer.signal_handler)
    
    # Run deployment
    deployer.deploy()

if __name__ == "__main__":
    main()
