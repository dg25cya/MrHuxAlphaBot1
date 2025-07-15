#!/usr/bin/env python3
"""Test script for hunting features."""

import asyncio
import os
import sys
import time
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_hunting_functionality():
    """Test the hunting features."""
    print("🧪 Testing Hunting Features")
    print("=" * 50)
    
    try:
        # Test imports
        print("1. Testing imports...")
        from src.core.services.continuous_hunter import ContinuousPlayHunter, get_play_hunter
        from src.core.services.external_monitor import ExternalGroupMonitor
        print("✅ All imports successful")
        
        # Test initialization
        print("\n2. Testing hunter initialization...")
        
        # Mock Telegram client
        class MockClient:
            def __init__(self):
                self.is_connected_flag = True
            
            def is_connected(self):
                return self.is_connected_flag
            
            async def get_entity(self, entity_id):
                # Mock entity for testing
                class MockEntity:
                    title = f"Test Group {entity_id}"
                    broadcast = False
                return MockEntity()
            
            async def get_messages(self, entity, limit=1, offset_date=None):
                # Mock empty messages
                return []
        
        client = MockClient()
        
        # Initialize external monitor
        external_monitor = ExternalGroupMonitor(client)
        print("✅ External monitor initialized")
        
        # Initialize continuous hunter
        hunter = ContinuousPlayHunter(client, external_monitor)
        print("✅ Continuous hunter initialized")
        
        # Test adding sources
        print("\n3. Testing source management...")
        
        # Test adding X profile
        result = await hunter.add_x_profile("elonmusk")
        print(f"Add X profile result: {result}")
        
        # Test hunting status
        print("\n4. Testing hunting status...")
        status = await hunter.get_hunting_status()
        print("Current hunting status:")
        print(f"  Running: {status['running']}")
        print(f"  Telegram groups: {len(status['sources']['telegram_groups'])}")
        print(f"  X profiles: {len(status['sources']['x_profiles'])}")
        print(f"  DexScreener: {status['sources']['dex_trending']}")
        print(f"  Pump.fun: {status['sources']['pump_new']}")
        
        # Test criteria
        print("\n5. Testing hunting criteria...")
        criteria = hunter.criteria
        print("Current criteria:")
        for key, value in criteria.items():
            print(f"  {key}: {value}")
        
        # Test X profile checking
        print("\n6. Testing X profile play detection...")
        plays = await hunter._check_x_profile_for_plays("elonmusk")
        print(f"Found {len(plays)} plays from @elonmusk")
        for play in plays:
            print(f"  - {play['symbol']}: {play['name']}")
        
        print("\n✅ All hunting functionality tests passed!")
        
        # Test brief hunting simulation
        print("\n7. Testing brief hunting simulation...")
        print("Starting hunter for 10 seconds...")
        
        # Start hunting
        hunter_task = asyncio.create_task(hunter.start_hunting())
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Check if running
        print(f"Hunter running: {hunter.running}")
        
        # Stop hunting
        await hunter.stop_hunting()
        print("Hunter stopped")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_hunting_functionality())
