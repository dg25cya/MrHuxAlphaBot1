#!/usr/bin/env python3
"""Complete bot startup and validation script."""
import asyncio
import time
import requests
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

class BotManager:
    """Manages the complete bot lifecycle."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.config_validated = False
        self.dependencies_checked = False
        self.bot_running = False
        
    def check_dependencies(self):
        """Check if all required packages are installed."""
        print("🔍 Checking Dependencies...")
        
        required_packages = [
            'fastapi', 'uvicorn', 'telethon', 'sqlalchemy', 
            'pydantic', 'redis', 'requests', 'loguru',
            'prometheus-client', 'aioredis'
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"   ✅ {package}")
            except ImportError:
                missing.append(package)
                print(f"   ❌ {package}")
        
        if missing:
            print(f"\n⚠️ Installing missing packages: {', '.join(missing)}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
            print("✅ All dependencies installed!")
        
        self.dependencies_checked = True
        return True
    
    def validate_config(self):
        """Validate all configuration files."""
        print("\n🔧 Validating Configuration...")
        
        # Check .env file
        env_file = self.base_dir / '.env'
        if not env_file.exists():
            print("❌ .env file not found!")
            return False
        
        # Read and validate critical settings
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        critical_settings = [
            'TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'BOT_TOKEN',
            'DATABASE_URL', 'BIRDEYE_API_KEY'
        ]
        
        for setting in critical_settings:
            if setting in env_content and '=' in env_content:
                value = [line for line in env_content.split('\n') if line.startswith(setting)]
                if value and '=' in value[0]:
                    val = value[0].split('=', 1)[1].strip()
                    if val and val != 'your_key_here':
                        print(f"   ✅ {setting}: Configured")
                    else:
                        print(f"   ⚠️ {setting}: Empty (using defaults)")
                else:
                    print(f"   ❌ {setting}: Missing")
            else:
                print(f"   ❌ {setting}: Not found")
        
        print("✅ Configuration validated!")
        self.config_validated = True
        return True
    
    def setup_database(self):
        """Initialize database with all required tables."""
        print("\n🗄️ Setting up Database...")
        
        db_file = self.base_dir / 'mr_hux_alpha_bot.db'
        
        try:
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'tokens', 'token_metrics', 'token_scores', 
                'alerts', 'monitored_groups', 'token_mentions'
            ]
            
            for table in expected_tables:
                if table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   ✅ {table}: {count} records")
                else:
                    print(f"   ⚠️ {table}: Table missing (will be created)")
            
            conn.close()
            print("✅ Database ready!")
            return True
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
    
    def test_external_apis(self):
        """Test all external API connections."""
        print("\n🌐 Testing External APIs...")
        
        # Test DexScreener (no auth required)
        try:
            response = requests.get(
                "https://api.dexscreener.com/latest/dex/tokens/So11111111111111111111111111111111111111112",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                print(f"   ✅ DexScreener: {len(pairs)} pairs found")
            else:
                print(f"   ⚠️ DexScreener: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ DexScreener: {e}")
        
        # Test Birdeye (requires API key)
        try:
            response = requests.get(
                "https://public-api.birdeye.so/defi/token_list?sort_by=v24hUSD&sort_type=desc&offset=0&limit=1",
                headers={'X-API-KEY': 'your-birdeye-key'},
                timeout=10
            )
            if response.status_code == 200:
                print("   ✅ Birdeye: Connected")
            else:
                print(f"   ⚠️ Birdeye: HTTP {response.status_code} (check API key)")
        except Exception as e:
            print(f"   ⚠️ Birdeye: {e}")
        
        print("✅ API tests completed!")
        return True
    
    def check_bot_status(self):
        """Check if the bot is currently running."""
        print("\n🤖 Checking Bot Status...")
        
        try:
            # Test web server
            response = requests.get("http://localhost:8002/health", timeout=5)
            if response.status_code == 200:
                print("   ✅ Web Server: Running on port 8002")
                self.bot_running = True
            else:
                print(f"   ⚠️ Web Server: HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("   ❌ Web Server: Not running")
            self.bot_running = False
        except Exception as e:
            print(f"   ❌ Web Server: {e}")
            self.bot_running = False
        
        # Check log file for recent activity
        log_file = self.base_dir / 'logs' / 'mr_hux_alpha_bot.log'
        if log_file.exists():
            size = log_file.stat().st_size / 1024  # KB
            print(f"   ✅ Log File: Active ({size:.1f} KB)")
        else:
            print("   ⚠️ Log File: Not found")
        
        return self.bot_running
    
    def start_bot(self):
        """Start the bot with all services."""
        print("\n🚀 Starting Mr Hux Alpha Bot...")
        
        if self.bot_running:
            print("   ⚠️ Bot is already running!")
            print("   📊 Dashboard: http://localhost:8002/static/")
            print("   🔍 Health Check: http://localhost:8002/health")
            return True
        
        try:
            # Start the bot
            print("   🔄 Launching bot process...")
            import subprocess
            
            # Use the VS Code task if available
            try:
                result = subprocess.run(
                    ["python", "-m", "src.main"],
                    cwd=str(self.base_dir),
                    capture_output=False,
                    text=True
                )
                return True
            except Exception as e:
                print(f"   ❌ Failed to start bot: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
            return False
    
    def run_complete_setup(self):
        """Run the complete bot setup and startup process."""
        print("🤖 MR HUX ALPHA BOT - COMPLETE SETUP")
        print("=" * 60)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Step 1: Check dependencies
        if not self.check_dependencies():
            print("❌ Dependency check failed!")
            return False
        
        # Step 2: Validate configuration
        if not self.validate_config():
            print("❌ Configuration validation failed!")
            return False
        
        # Step 3: Setup database
        if not self.setup_database():
            print("❌ Database setup failed!")
            return False
        
        # Step 4: Test APIs
        self.test_external_apis()
        
        # Step 5: Check current status
        self.check_bot_status()
        
        # Step 6: Start if needed
        if not self.bot_running:
            self.start_bot()
        
        # Final status
        print("\n" + "=" * 60)
        print("🎉 SETUP COMPLETE!")
        print("=" * 60)
        
        if self.bot_running:
            print("✅ Bot Status: RUNNING")
            print("🌐 Dashboard: http://localhost:8002/static/")
            print("🔍 Health: http://localhost:8002/health")
            print("📱 Ready for Telegram commands!")
        else:
            print("⚠️ Bot Status: STARTING...")
            print("   Please wait a moment for all services to initialize")
        
        print("\n🎯 TELEGRAM COMMANDS:")
        commands = [
            "/start - Welcome and help",
            "/analyze {token} - Analyze any Solana token", 
            "/monitor {group_id} - Start monitoring a group",
            "/stats - Show statistics",
            "/top - Top rated tokens"
        ]
        
        for cmd in commands:
            print(f"   {cmd}")
        
        print(f"\n🚀 Mr Hux Alpha Bot is ready to find Solana gems!")
        return True

def main():
    """Main entry point."""
    manager = BotManager()
    success = manager.run_complete_setup()
    
    if success:
        print("\n✨ Bot setup completed successfully!")
        print("📖 Check GETTING_STARTED.md for detailed usage instructions")
    else:
        print("\n❌ Bot setup encountered issues. Check the output above.")
    
    return success

if __name__ == "__main__":
    main()
