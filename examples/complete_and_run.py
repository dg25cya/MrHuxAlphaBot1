#!/usr/bin/env python3
"""Complete and run Mr Hux Alpha Bot - Production Ready Version."""
import time
import requests
import sqlite3
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

def check_bot_running():
    """Check if bot is currently running."""
    try:
        response = requests.get("http://localhost:8002/health", timeout=3)
        return response.status_code == 200
    except:
        return False

def validate_environment():
    """Validate critical environment settings."""
    print("🔧 Validating Environment...")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    # Check database file
    db_file = Path('mr_hux_alpha_bot.db')
    if db_file.exists():
        print(f"✅ Database: Found ({db_file.stat().st_size // 1024} KB)")
    else:
        print("⚠️ Database: Will be created on startup")
    
    # Check logs
    log_dir = Path('logs')
    if log_dir.exists():
        log_files = list(log_dir.glob('*.log'))
        if log_files:
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            size = latest_log.stat().st_size // 1024
            print(f"✅ Logs: Active ({size} KB)")
        else:
            print("⚠️ Logs: Directory exists but no log files")
    else:
        print("⚠️ Logs: Directory will be created")
    
    return True

def test_external_apis():
    """Test critical external APIs."""
    print("\n🌐 Testing External APIs...")
    
    # Test DexScreener (most critical for token data)
    try:
        response = requests.get(
            "https://api.dexscreener.com/latest/dex/tokens/So11111111111111111111111111111111111111112",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            pairs = len(data.get('pairs', []))
            print(f"✅ DexScreener: Connected ({pairs} pairs)")
        else:
            print(f"⚠️ DexScreener: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ DexScreener: {e}")
    
    print("✅ API validation complete!")

def show_bot_status():
    """Show comprehensive bot status."""
    print("\n📊 BOT STATUS SUMMARY")
    print("=" * 50)
    
    # Web server status
    if check_bot_running():
        print("✅ Web Server: RUNNING (http://localhost:8002)")
        print("✅ Health Check: PASSED")
    else:
        print("❌ Web Server: NOT RUNNING")
    
    # Database status
    db_file = Path('mr_hux_alpha_bot.db')
    if db_file.exists():
        try:
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"✅ Database: Connected ({len(tables)} tables)")
            
            # Quick data check
            for table_name in ['tokens', 'monitored_groups', 'alerts']:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"   • {table_name}: {count} records")
                except:
                    print(f"   • {table_name}: Table not ready")
            
            conn.close()
        except Exception as e:
            print(f"⚠️ Database: Error - {e}")
    else:
        print("⚠️ Database: Not initialized")
    
    # Log status
    log_file = Path('logs/mr_hux_alpha_bot.log')
    if log_file.exists():
        size = log_file.stat().st_size // 1024
        print(f"✅ Logging: Active ({size} KB)")
    else:
        print("⚠️ Logging: No log file found")

def start_bot():
    """Start the bot using the proper method."""
    print("\n🚀 Starting Mr Hux Alpha Bot...")
    
    if check_bot_running():
        print("⚠️ Bot is already running!")
        return True
    
    print("🔄 Launching bot process...")
    
    # Try to start using python module method
    try:
        # Start in background
        if os.name == 'nt':  # Windows
            subprocess.Popen(
                [sys.executable, '-m', 'src.main'],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:  # Unix/Linux/Mac
            subprocess.Popen([sys.executable, '-m', 'src.main'])
        
        # Wait for startup
        print("⏳ Waiting for bot to initialize...")
        for i in range(10):
            time.sleep(2)
            if check_bot_running():
                print("✅ Bot started successfully!")
                return True
            print(f"   Checking... ({i+1}/10)")
        
        print("⚠️ Bot may still be starting. Check manually.")
        return True
        
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        return False

def show_usage_guide():
    """Show quick usage guide."""
    print("\n" + "=" * 60)
    print("🎉 MR HUX ALPHA BOT - READY FOR ACTION!")
    print("=" * 60)
    
    print("\n🌐 ACCESS POINTS:")
    print("   📊 Dashboard: http://localhost:8002/static/")
    print("   🔍 Health Check: http://localhost:8002/health")
    print("   📱 Telegram: Add bot to groups and use commands")
    
    print("\n📱 KEY TELEGRAM COMMANDS:")
    commands = [
        ("/start", "Welcome message and help"),
        ("/analyze {token}", "Deep analysis of any Solana token"),
        ("/monitor {group_id}", "Start monitoring a Telegram group"),
        ("/stats", "Show monitoring statistics"),
        ("/top", "Show top-rated tokens by score"),
        ("/alerts", "View recent alerts")
    ]
    
    for cmd, desc in commands:
        print(f"   {cmd:<20} - {desc}")
    
    print("\n🎯 QUICK START:")
    print("   1. Add your bot to crypto Telegram groups")
    print("   2. Use: /monitor {group_id} to start monitoring")
    print("   3. Try: /analyze DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263")
    print("   4. Visit the dashboard for real-time data")
    
    print("\n🔥 FEATURES ACTIVE:")
    features = [
        "✅ Real-time token detection in Telegram groups",
        "✅ Automatic safety and hype scoring",
        "✅ Price tracking via DexScreener API",
        "✅ Smart alert system for promising tokens",
        "✅ Web dashboard for monitoring",
        "✅ Comprehensive token analysis"
    ]
    
    for feature in features:
        print(f"   {feature}")
    
    print(f"\n🚀 Ready to discover the next Solana gem!")

def main():
    """Main execution function."""
    print("🤖 MR HUX ALPHA BOT - COMPLETE SETUP & RUN")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Validate environment
    if not validate_environment():
        print("❌ Environment validation failed!")
        return False
    
    # Step 2: Test external APIs
    test_external_apis()
    
    # Step 3: Check current status
    show_bot_status()
    
    # Step 4: Start bot if needed
    bot_was_running = check_bot_running()
    if not bot_was_running:
        if not start_bot():
            print("❌ Failed to start bot!")
            return False
    
    # Step 5: Final validation
    time.sleep(2)  # Give it a moment
    final_status = check_bot_running()
    
    if final_status:
        show_usage_guide()
        return True
    else:
        print("⚠️ Bot startup may still be in progress...")
        print("   Check http://localhost:8002/health in a few moments")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✨ Setup completed successfully!")
    else:
        print("\n⚠️ Setup completed with warnings. Bot may still be starting.")
    
    print("\n📖 For detailed instructions, see: GETTING_STARTED.md")
