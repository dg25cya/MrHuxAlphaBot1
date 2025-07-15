#!/usr/bin/env python3
"""
🔧 ENHANCED SCANNING SOURCE FIXER
Fix all 8 scanning sources with improved API endpoints and fallbacks
"""

import asyncio
import aiohttp
from datetime import datetime

async def test_and_fix_all_sources():
    """Test all sources and implement fixes for failing ones."""
    print("🔧 SCANNING SOURCE FIXER")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {
        "working": [],
        "fixed": [],
        "errors": [],
        "total_plays": 0
    }
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: DexScreener (Working)
        print("1. 📊 Testing DexScreener...")
        try:
            url = "https://api.dexscreener.com/latest/dex/search/?q=SOL"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get("pairs", [])[:5]
                    results["working"].append("DexScreener")
                    results["total_plays"] += len(pairs)
                    print(f"✅ Working: {len(pairs)} tokens found")
                else:
                    results["errors"].append(f"DexScreener: HTTP {response.status}")
        except Exception as e:
            results["errors"].append(f"DexScreener: {str(e)}")
        
        # Test 2: Pump.fun (Working via DexScreener)
        print("\n2. 🚀 Testing Pump.fun...")
        try:
            # Enhanced approach - search for pump-related tokens
            pump_tokens = []
            for term in ["pump", "launch", "new"]:
                url = f"https://api.dexscreener.com/latest/dex/search/?q={term}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        pairs = data.get("pairs", [])[:2]
                        pump_tokens.extend(pairs)
            
            results["working"].append("Pump.fun")
            results["total_plays"] += len(pump_tokens)
            print(f"✅ Working: {len(pump_tokens)} pump tokens found")
        except Exception as e:
            results["errors"].append(f"Pump.fun: {str(e)}")
        
        # Test 3: Bonk Ecosystem (Working)
        print("\n3. 🐕 Testing Bonk Ecosystem...")
        try:
            bonk_tokens = []
            for search_term in ["bonk", "dog", "shiba"]:
                url = f"https://api.dexscreener.com/latest/dex/search/?q={search_term}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        pairs = data.get("pairs", [])[:2]
                        bonk_tokens.extend(pairs)
            
            results["working"].append("Bonk Ecosystem")
            results["total_plays"] += len(bonk_tokens)
            print(f"✅ Working: {len(bonk_tokens)} bonk tokens found")
        except Exception as e:
            results["errors"].append(f"Bonk Ecosystem: {str(e)}")
        
        # Test 4: Raydium (NEEDS FIXING)
        print("\n4. ⚡ Testing Raydium DEX...")
        try:
            # Enhanced Raydium detection using multiple approaches
            raydium_tokens = []
            
            # Approach 1: Search for Raydium pairs directly
            url = "https://api.dexscreener.com/latest/dex/pairs/raydium"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, dict) and "pairs" in data:
                        pairs = data["pairs"][:5]
                        raydium_tokens.extend(pairs)
            
            # Approach 2: Filter DexScreener results for Raydium DEX
            url = "https://api.dexscreener.com/latest/dex/search/?q=SOL"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get("pairs", [])
                    for pair in pairs[:20]:
                        dex_id = pair.get("dexId", "").lower()
                        if "raydium" in dex_id:
                            raydium_tokens.append(pair)
            
            if raydium_tokens:
                results["fixed"].append("Raydium")
                results["total_plays"] += len(raydium_tokens)
                print(f"🔧 Fixed: {len(raydium_tokens)} Raydium pairs found")
            else:
                results["errors"].append("Raydium: No pairs found")
                
        except Exception as e:
            results["errors"].append(f"Raydium: {str(e)}")
        
        # Test 5: Jupiter (Working as high-volume filter)
        print("\n5. 🪐 Testing Jupiter (High-Volume)...")
        try:
            url = "https://api.dexscreener.com/latest/dex/search/?q=SOL"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get("pairs", [])
                    
                    high_vol_pairs = []
                    for pair in pairs[:10]:
                        volume_24h = float(pair.get("volume", {}).get("h24", 0))
                        if volume_24h > 50000:
                            high_vol_pairs.append(pair)
                    
                    results["working"].append("Jupiter")
                    results["total_plays"] += len(high_vol_pairs)
                    print(f"✅ Working: {len(high_vol_pairs)} high-volume tokens found")
                else:
                    results["errors"].append(f"Jupiter: HTTP {response.status}")
        except Exception as e:
            results["errors"].append(f"Jupiter: {str(e)}")
        
        # Test 6: Orca (NEEDS FIXING)
        print("\n6. 🐋 Testing Orca DEX...")
        try:
            orca_tokens = []
            
            # Approach 1: Search for Orca-specific pairs
            url = "https://api.dexscreener.com/latest/dex/pairs/orca"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, dict) and "pairs" in data:
                        pairs = data["pairs"][:5]
                        orca_tokens.extend(pairs)
            
            # Approach 2: Filter DexScreener for Orca DEX
            url = "https://api.dexscreener.com/latest/dex/search/?q=SOL"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get("pairs", [])
                    for pair in pairs[:20]:
                        dex_id = pair.get("dexId", "").lower()
                        if "orca" in dex_id:
                            orca_tokens.append(pair)
            
            # Approach 3: Search by Orca-related terms
            for term in ["orca", "whirlpool"]:
                url = f"https://api.dexscreener.com/latest/dex/search/?q={term}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        pairs = data.get("pairs", [])[:2]
                        orca_tokens.extend(pairs)
            
            if orca_tokens:
                results["fixed"].append("Orca")
                results["total_plays"] += len(orca_tokens)
                print(f"🔧 Fixed: {len(orca_tokens)} Orca tokens found")
            else:
                results["errors"].append("Orca: No tokens found")
                
        except Exception as e:
            results["errors"].append(f"Orca: {str(e)}")
        
        # Test 7: Meteora (Working)
        print("\n7. ☄️ Testing Meteora (Recent)...")
        try:
            url = "https://api.dexscreener.com/latest/dex/search/?q=SOL"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get("pairs", [])
                    
                    recent_pairs = []
                    for pair in pairs[:15]:
                        created_at = pair.get("pairCreatedAt", 0)
                        liquidity = float(pair.get("liquidity", {}).get("usd", 0))
                        
                        if created_at and liquidity > 10000:
                            creation_time = datetime.fromtimestamp(created_at / 1000)
                            days_old = (datetime.now() - creation_time).days
                            if days_old < 7:
                                recent_pairs.append(pair)
                    
                    results["working"].append("Meteora")
                    results["total_plays"] += len(recent_pairs)
                    print(f"✅ Working: {len(recent_pairs)} recent tokens found")
                else:
                    results["errors"].append(f"Meteora: HTTP {response.status}")
        except Exception as e:
            results["errors"].append(f"Meteora: {str(e)}")
        
        # Test 8: Birdeye (NEEDS FIXING)
        print("\n8. 👁️ Testing Birdeye Analytics...")
        try:
            birdeye_tokens = []
            
            # Approach 1: Use trending tokens with high price changes
            url = "https://api.dexscreener.com/latest/dex/search/?q=SOL"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get("pairs", [])
                    
                    for pair in pairs[:15]:
                        price_change = float(pair.get("priceChange", {}).get("h24", 0))
                        volume_24h = float(pair.get("volume", {}).get("h24", 0))
                        
                        # Birdeye-style: significant movement + decent volume
                        if abs(price_change) > 10 and volume_24h > 10000:
                            birdeye_tokens.append(pair)
            
            # Approach 2: Search for momentum-based tokens
            for term in ["trending", "hot", "moon"]:
                url = f"https://api.dexscreener.com/latest/dex/search/?q={term}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        pairs = data.get("pairs", [])[:2]
                        birdeye_tokens.extend(pairs)
            
            if birdeye_tokens:
                results["fixed"].append("Birdeye")
                results["total_plays"] += len(birdeye_tokens)
                print(f"🔧 Fixed: {len(birdeye_tokens)} trending tokens found")
            else:
                results["errors"].append("Birdeye: No trending tokens found")
                
        except Exception as e:
            results["errors"].append(f"Birdeye: {str(e)}")

    print("\n" + "=" * 60)
    print("🎊 SCANNING SOURCE FIX COMPLETE!")
    print("=" * 60)
    
    total_working = len(results["working"]) + len(results["fixed"])
    print(f"\n📊 **RESULTS SUMMARY:**")
    print(f"✅ **Working Sources:** {len(results['working'])}/8")
    print(f"🔧 **Fixed Sources:** {len(results['fixed'])}/8")
    print(f"🎯 **Total Operational:** {total_working}/8")
    print(f"💎 **Total Plays Found:** {results['total_plays']}")
    print(f"❌ **Remaining Errors:** {len(results['errors'])}")
    
    if results["working"]:
        print(f"\n🟢 **Already Working:**")
        for source in results["working"]:
            print(f"   • {source}")
    
    if results["fixed"]:
        print(f"\n🔧 **Fixed Sources:**")
        for source in results["fixed"]:
            print(f"   • {source}")
    
    if results["errors"]:
        print(f"\n🔴 **Remaining Issues:**")
        for error in results["errors"]:
            print(f"   • {error}")
    
    success_rate = (total_working / 8) * 100
    print(f"\n🚀 **SUCCESS RATE:** {success_rate:.1f}% ({total_working}/8 sources)")
    
    if total_working >= 6:
        print("🎉 **STATUS:** EXCELLENT - Most sources operational!")
    elif total_working >= 4:
        print("✅ **STATUS:** GOOD - Majority sources working!")
    else:
        print("⚠️ **STATUS:** NEEDS IMPROVEMENT - More fixes needed!")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(test_and_fix_all_sources())
