"""Bot command handlers with enhanced UI and features."""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from telethon import events, TelegramClient, Button
from telethon.tl.custom import Message
from loguru import logger
import emoji
import threading
import time

from src.config.settings import get_settings
from src.models.monitored_source import MonitoredSource, SourceType, OutputChannel, OutputType
from src.core.services.source_handlers import SourceManager
from src.core.services.output_service import OutputService
from src.core.services.text_analysis import TextAnalysisService
from src.utils.db import db_session

settings = get_settings()

# User state management for collecting input
user_states = {}

# Enhanced UI Elements
UI = {
    "emoji": {
        "welcome": "👋",
        "bot": "🤖",
        "source": "📡",
        "output": "📢",
        "ai": "🔬",
        "settings": "⚙️",
        "stats": "📊",
        "help": "❓",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "loading": "⏳",
        "done": "✨"
    },
    "headers": {
        "welcome": "Welcome to MR HUX Alpha Bot",
        "sources": "Source Management",
        "outputs": "Output Channels",
        "ai": "AI Features",
        "settings": "Bot Settings",
        "stats": "Bot Statistics",
        "help": "Help & Support"
    },
    "messages": {
        "welcome": """
🚀 **Welcome to MR HUX Alpha Bot!** 🚀

🎯 **Your Ultimate Social Media Intelligence Hub**

🔥 **What We Do:**
• 📡 **Real-time Monitoring** - Track Telegram, Discord, Reddit, X/Twitter
• 🤖 **AI-Powered Analysis** - Sentiment, trends, and smart insights
• ⚡ **Instant Alerts** - Never miss important signals
• 📊 **Advanced Analytics** - Deep market intelligence

🎮 **Ready to Hunt?**
1. 📡 Add your favorite sources
2. 🎯 Set up smart filters
3. 📢 Configure alerts
4. 🚀 Start catching alpha!

💎 **Pro Features:**
• 🧠 AI Sentiment Analysis
• 🔍 Smart Pattern Recognition
• 🌍 Multi-language Support
• ⚡ Lightning-fast Processing

*Your journey to alpha discovery starts now!* ✨
""",
        "source_menu": """
{e.source} Source Management

Current Status:
• Active Sources: {active_sources}
• Recent Updates: {recent_updates}
• Error Rate: {error_rate}%

Actions:
• Add new sources to monitor
• Manage existing sources
• Configure filters and alerts
• Set scanning schedules
""",
        "output_menu": """
{e.output} Output Channel Setup

Active Channels:
• Telegram: {telegram_channels}
• Discord: {discord_webhooks}
• Total Messages: {total_messages}

Features:
• Smart message formatting
• Rich media support
• Error handling
• Delivery confirmation
""",
        "ai_menu": """
{e.ai} AI Features Control

Active Features:
• Sentiment Analysis: {sentiment_status}
• Summarization: {summary_status}
• Translation: {translation_status}
• Smart Filtering: {filter_status}

Performance:
• Analysis Speed: {analysis_speed}ms
• Success Rate: {success_rate}%
"""
    }
}

# Remove global cache and background thread for active sources

async def setup_command_handlers(client: TelegramClient, db=None):
    """Setup command handlers for the bot."""
    source_manager = SourceManager()
    output_service = OutputService(db, client) if db else None
    text_analyzer = TextAnalysisService()

    async def get_stats() -> Dict[str, Any]:
        """Get current bot statistics."""
        try:
            with db_session() as db:
                sources = db.query(MonitoredSource).filter(MonitoredSource.is_active == True).all()
                day_ago = datetime.utcnow() - timedelta(days=1)
                active_sources = len(sources)
                recent_updates = sum(1 for s in sources if getattr(s, 'last_scanned', None) and s.last_scanned > day_ago)
                error_rate = sum(1 for s in sources if getattr(s, 'error_count', 0) > 0) / max(len(sources), 1) * 100
                # Channel stats
                channels = db.query(OutputChannel).filter(OutputChannel.is_active == True).all()
                telegram_channels = sum(1 for c in channels if getattr(c, 'type', None) == OutputType.TELEGRAM)
                discord_webhooks = sum(1 for c in channels if getattr(c, 'type', None) == OutputType.DISCORD)
                total_messages = sum(getattr(c, 'message_count', 0) or 0 for c in channels)
                ai_stats = text_analyzer.get_stats()
                return {
                    "active_sources": active_sources,
                    "recent_updates": recent_updates,
                    "error_rate": error_rate,
                    "telegram_channels": telegram_channels,
                    "discord_webhooks": discord_webhooks,
                    "total_messages": total_messages,
                    "ai_stats": ai_stats
                }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

    @client.on(events.NewMessage(pattern=r'/start'))
    async def start_command(event: Message):
        """Handle /start command with enhanced UI."""
        # Create an exciting button layout
        keyboard = [
            [
                Button.inline("🎯 HUNT SOURCES", "menu_sources"),
                Button.inline("📢 ALERT CHANNELS", "menu_outputs"),
            ],
            [
                Button.inline("🤖 AI INTELLIGENCE", "menu_ai"),
                Button.inline("⚙️ BOT SETTINGS", "menu_settings"),
            ],
            [
                Button.inline("📊 LIVE STATS", "menu_stats"),
                Button.inline("❓ HELP & SUPPORT", "menu_help"),
            ],
            [
                Button.url("🔥 ALPHA COMMUNITY", "https://t.me/MrHuxCommunity"),
                Button.url("📰 LATEST UPDATES", "https://t.me/MrHuxUpdates"),
            ]
        ]

        # Get current stats
        stats = await get_stats()
        
        # Format welcome message with button-driven instructions
        welcome_msg = f"""
🚀 **Welcome to MR HUX Alpha Bot!** 🚀

🎯 **Your Ultimate Social Media Intelligence Hub**

🔥 **What We Do:**
• 📡 **Real-time Monitoring** - Track Telegram, Discord, Reddit, X/Twitter
• 🤖 **AI-Powered Analysis** - Sentiment, trends, and smart insights
• ⚡ **Instant Alerts** - Never miss important signals
• 📊 **Advanced Analytics** - Deep market intelligence

🎮 **Ready to Hunt?**
1. 📡 Add your favorite sources
2. 🎯 Set up smart filters
3. 📢 Configure alerts
4. 🚀 Start catching alpha!

💎 **Pro Features:**
• 🧠 AI Sentiment Analysis
• 🔍 Smart Pattern Recognition
• 🌍 Multi-language Support
• ⚡ Lightning-fast Processing

*Your journey to alpha discovery starts now!* ✨

**🎯 Everything is button-driven - no commands needed!**
"""

        await event.reply(
            welcome_msg,
            buttons=keyboard
        )

    # Handle text input for adding sources
    @client.on(events.NewMessage(pattern=r'^(?!\/start).*'))
    async def handle_text_input(event: Message):
        """Handle text input for adding sources and other actions."""
        user_id = event.sender_id
        text = event.message.text.strip()
        
        # Check if user is in a state waiting for input
        if user_id in user_states:
            state = user_states[user_id]
            action = state.get('action')
            
            if action == 'add_telegram_source':
                # Handle Telegram source addition
                try:
                    # Add the Telegram source
                    source_data = {
                        'type': SourceType.TELEGRAM,
                        'identifier': text,
                        'name': f"Telegram: {text}",
                        'is_active': True
                    }
                    
                    with db_session() as db:
                        source = MonitoredSource(**source_data)
                        db.add(source)
                        db.commit()
                    
                    # Clear user state
                    del user_states[user_id]
                    
                    keyboard = [
                        [Button.inline("✅ Source Added!", "menu_sources")],
                        [Button.inline("➕ Add Another", "source_add")],
                        [Button.inline("🔙 Main Menu", "menu_main")]
                    ]
                    
                    await event.reply(
                        f"✅ **Telegram Source Added Successfully!**\n\n"
                        f"📱 **Source:** {text}\n"
                        f"🎯 **Status:** Active and monitoring\n"
                        f"⚡ **Next:** Start receiving alerts!",
                        buttons=keyboard
                    )
                    
                except Exception as e:
                    logger.error(f"Error adding Telegram source: {e}")
                    await event.reply(
                        f"❌ **Error adding source:** {str(e)}\n\n"
                        f"Please try again or contact support.",
                        buttons=[[Button.inline("🔙 Back to Sources", "menu_sources")]]
                    )
            
            elif action == 'add_discord_source':
                # Handle Discord source addition
                try:
                    source_data = {
                        'type': SourceType.DISCORD,
                        'identifier': text,
                        'name': f"Discord: {text}",
                        'is_active': True
                    }
                    
                    with db_session() as db:
                        source = MonitoredSource(**source_data)
                        db.add(source)
                        db.commit()
                    
                    del user_states[user_id]
                    
                    keyboard = [
                        [Button.inline("✅ Source Added!", "menu_sources")],
                        [Button.inline("➕ Add Another", "source_add")],
                        [Button.inline("🔙 Main Menu", "menu_main")]
                    ]
                    
                    await event.reply(
                        f"✅ **Discord Source Added Successfully!**\n\n"
                        f"💬 **Server ID:** {text}\n"
                        f"🎯 **Status:** Active and monitoring\n"
                        f"⚡ **Next:** Start receiving alerts!",
                        buttons=keyboard
                    )
                    
                except Exception as e:
                    logger.error(f"Error adding Discord source: {e}")
                    await event.reply(
                        f"❌ **Error adding source:** {str(e)}\n\n"
                        f"Please try again or contact support.",
                        buttons=[[Button.inline("🔙 Back to Sources", "menu_sources")]]
                    )
            
            elif action == 'add_reddit_source':
                # Handle Reddit source addition
                try:
                    source_data = {
                        'type': SourceType.REDDIT,
                        'identifier': text,
                        'name': f"Reddit: r/{text}",
                        'is_active': True
                    }
                    
                    with db_session() as db:
                        source = MonitoredSource(**source_data)
                        db.add(source)
                        db.commit()
                    
                    del user_states[user_id]
                    
                    keyboard = [
                        [Button.inline("✅ Source Added!", "menu_sources")],
                        [Button.inline("➕ Add Another", "source_add")],
                        [Button.inline("🔙 Main Menu", "menu_main")]
                    ]
                    
                    await event.reply(
                        f"✅ **Reddit Source Added Successfully!**\n\n"
                        f"🌐 **Subreddit:** r/{text}\n"
                        f"🎯 **Status:** Active and monitoring\n"
                        f"⚡ **Next:** Start receiving alerts!",
                        buttons=keyboard
                    )
                    
                except Exception as e:
                    logger.error(f"Error adding Reddit source: {e}")
                    await event.reply(
                        f"❌ **Error adding source:** {str(e)}\n\n"
                        f"Please try again or contact support.",
                        buttons=[[Button.inline("🔙 Back to Sources", "menu_sources")]]
                    )
            
            elif action == 'add_twitter_source':
                # Handle Twitter/X source addition
                try:
                    # Clean username (remove @ if present)
                    username = text.lstrip('@')
                    source_data = {
                        'type': SourceType.X,
                        'identifier': username,
                        'name': f"Twitter: @{username}",
                        'is_active': True
                    }
                    
                    with db_session() as db:
                        source = MonitoredSource(**source_data)
                        db.add(source)
                        db.commit()
                    
                    del user_states[user_id]
                    
                    keyboard = [
                        [Button.inline("✅ Source Added!", "menu_sources")],
                        [Button.inline("➕ Add Another", "source_add")],
                        [Button.inline("🔙 Main Menu", "menu_main")]
                    ]
                    
                    await event.reply(
                        f"✅ **Twitter Source Added Successfully!**\n\n"
                        f"🐦 **Username:** @{username}\n"
                        f"🎯 **Status:** Active and monitoring\n"
                        f"⚡ **Next:** Start receiving alerts!",
                        buttons=keyboard
                    )
                    
                except Exception as e:
                    logger.error(f"Error adding Twitter source: {e}")
                    await event.reply(
                        f"❌ **Error adding source:** {str(e)}\n\n"
                        f"Please try again or contact support.",
                        buttons=[[Button.inline("🔙 Back to Sources", "menu_sources")]]
                    )
            
            elif action == 'add_rss_source':
                # Handle RSS source addition
                try:
                    source_data = {
                        'type': SourceType.RSS,
                        'identifier': text,
                        'name': f"RSS: {text[:50]}...",
                        'is_active': True
                    }
                    
                    with db_session() as db:
                        source = MonitoredSource(**source_data)
                        db.add(source)
                        db.commit()
                    
                    del user_states[user_id]
                    
                    keyboard = [
                        [Button.inline("✅ Source Added!", "menu_sources")],
                        [Button.inline("➕ Add Another", "source_add")],
                        [Button.inline("🔙 Main Menu", "menu_main")]
                    ]
                    
                    await event.reply(
                        f"✅ **RSS Source Added Successfully!**\n\n"
                        f"📰 **Feed:** {text[:100]}...\n"
                        f"🎯 **Status:** Active and monitoring\n"
                        f"⚡ **Next:** Start receiving alerts!",
                        buttons=keyboard
                    )
                    
                except Exception as e:
                    logger.error(f"Error adding RSS source: {e}")
                    await event.reply(
                        f"❌ **Error adding source:** {str(e)}\n\n"
                        f"Please try again or contact support.",
                        buttons=[[Button.inline("🔙 Back to Sources", "menu_sources")]]
                    )
            
            elif action == 'add_github_source':
                # Handle GitHub source addition
                try:
                    source_data = {
                        'type': SourceType.GITHUB,
                        'identifier': text,
                        'name': f"GitHub: {text}",
                        'is_active': True
                    }
                    
                    with db_session() as db:
                        source = MonitoredSource(**source_data)
                        db.add(source)
                        db.commit()
                    
                    del user_states[user_id]
                    
                    keyboard = [
                        [Button.inline("✅ Source Added!", "menu_sources")],
                        [Button.inline("➕ Add Another", "source_add")],
                        [Button.inline("🔙 Main Menu", "menu_main")]
                    ]
                    
                    await event.reply(
                        f"✅ **GitHub Source Added Successfully!**\n\n"
                        f"🐙 **Repository:** {text}\n"
                        f"🎯 **Status:** Active and monitoring\n"
                        f"⚡ **Next:** Start receiving alerts!",
                        buttons=keyboard
                    )
                    
                except Exception as e:
                    logger.error(f"Error adding GitHub source: {e}")
                    await event.reply(
                        f"❌ **Error adding source:** {str(e)}\n\n"
                        f"Please try again or contact support.",
                        buttons=[[Button.inline("🔙 Back to Sources", "menu_sources")]]
                    )
            
            elif action == 'add_discord_webhook':
                # Handle Discord webhook addition
                try:
                    output_data = {
                        'type': OutputType.DISCORD,
                        'identifier': text,
                        'name': f"Discord Webhook",
                        'is_active': True
                    }
                    
                    with db_session() as db:
                        output = OutputChannel(**output_data)
                        db.add(output)
                        db.commit()
                    
                    del user_states[user_id]
                    
                    keyboard = [
                        [Button.inline("✅ Webhook Added!", "menu_outputs")],
                        [Button.inline("➕ Add Another", "output_add")],
                        [Button.inline("🔙 Main Menu", "menu_main")]
                    ]
                    
                    await event.reply(
                        f"✅ **Discord Webhook Added Successfully!**\n\n"
                        f"💬 **Status:** Active and ready\n"
                        f"⚡ **Next:** Start receiving alerts!",
                        buttons=keyboard
                    )
                    
                except Exception as e:
                    logger.error(f"Error adding Discord webhook: {e}")
                    await event.reply(
                        f"❌ **Error adding webhook:** {str(e)}\n\n"
                        f"Please try again or contact support.",
                        buttons=[[Button.inline("🔙 Back to Outputs", "menu_outputs")]]
                    )
            
            elif action == 'add_telegram_channel':
                # Handle Telegram channel addition
                try:
                    output_data = {
                        'type': OutputType.TELEGRAM,
                        'identifier': text,
                        'name': f"Telegram: {text}",
                        'is_active': True
                    }
                    
                    with db_session() as db:
                        output = OutputChannel(**output_data)
                        db.add(output)
                        db.commit()
                    
                    del user_states[user_id]
                    
                    keyboard = [
                        [Button.inline("✅ Channel Added!", "menu_outputs")],
                        [Button.inline("➕ Add Another", "output_add")],
                        [Button.inline("🔙 Main Menu", "menu_main")]
                    ]
                    
                    await event.reply(
                        f"✅ **Telegram Channel Added Successfully!**\n\n"
                        f"📱 **Channel:** {text}\n"
                        f"🎯 **Status:** Active and ready\n"
                        f"⚡ **Next:** Start receiving alerts!",
                        buttons=keyboard
                    )
                    
                except Exception as e:
                    logger.error(f"Error adding Telegram channel: {e}")
                    await event.reply(
                        f"❌ **Error adding channel:** {str(e)}\n\n"
                        f"Please try again or contact support.",
                        buttons=[[Button.inline("🔙 Back to Outputs", "menu_outputs")]]
                    )
        
        # If not in a state, ignore the message (only handle button callbacks)
        return

    # Callback handlers for button-driven interface
    @client.on(events.CallbackQuery(data="menu_sources"))
    async def menu_sources_callback(event):
        """Handle sources menu button."""
        keyboard = [
            [
                Button.inline("➕ Add Source", "source_add"),
                Button.inline("📋 View Sources", "source_list")
            ],
            [
                Button.inline("🎯 Filters", "source_filters"),
                Button.inline("⏰ Schedules", "source_schedule")
            ],
            [
                Button.inline("🔙 Main Menu", "menu_main")
            ]
        ]
        
        stats = await get_stats()
        
        await event.edit(
            f"🎯 **SOURCE HUNTING DASHBOARD** 🎯\n\n"
            f"🔍 **Current Status:**\n"
            f"• 📡 Active Sources: {stats.get('active_sources', 0)}\n"
            f"• ⚡ Recent Updates: {stats.get('recent_updates', 0)}\n"
            f"• ❌ Error Rate: {stats.get('error_rate', 0)}%\n\n"
            f"🎯 **What You Can Do:**\n"
            f"• 🆕 **Add New Sources** - Start monitoring fresh alpha\n"
            f"• 📋 **View Active Sources** - See what's being tracked\n"
            f"• 🎯 **Smart Filters** - Set up keyword alerts\n"
            f"• ⏰ **Scan Schedules** - Optimize monitoring frequency\n\n"
            f"*Ready to discover the next big thing?* 🚀",
            buttons=keyboard
        )

    @client.on(events.CallbackQuery(data="menu_outputs"))
    async def menu_outputs_callback(event):
        """Handle outputs menu button."""
        keyboard = [
            [
                Button.inline("➕ Add Output", "output_add"),
                Button.inline("📋 View Channels", "output_list")
            ],
            [
                Button.inline("✏️ Message Format", "format_settings"),
                Button.inline("⚡ Quick Setup", "quick_setup")
            ],
            [
                Button.inline("🔙 Main Menu", "menu_main")
            ]
        ]
        
        stats = await get_stats()
        
        await event.edit(
            f"📢 **ALERT CHANNEL COMMAND CENTER** 📢\n\n"
            f"🚨 **Current Status:**\n"
            f"• 📱 Telegram Channels: {stats.get('telegram_channels', 0)}\n"
            f"• 💬 Discord Webhooks: {stats.get('discord_webhooks', 0)}\n"
            f"• 📊 Total Messages: {stats.get('total_messages', 0)}\n\n"
            f"🚨 **Alert Distribution:**\n"
            f"• 📱 **Telegram Channels** - Send alerts to your groups\n"
            f"• 💬 **Discord Webhooks** - Integrate with Discord servers\n"
            f"• ✨ **Custom Formats** - Style your alerts perfectly\n"
            f"• ⚡ **Smart Notifications** - Get alerts when it matters\n\n"
            f"*Never miss a signal again!* 🔥",
            buttons=keyboard
        )

    @client.on(events.CallbackQuery(data="menu_ai"))
    async def menu_ai_callback(event):
        """Handle AI menu button."""
        keyboard = [
            [
                Button.inline("🎯 Toggle Features", "ai_toggle"),
                Button.inline("📋 View Settings", "ai_settings")
            ],
            [
                Button.inline("📊 AI Stats", "ai_stats"),
                Button.inline("❓ AI Help", "ai_help")
            ],
            [
                Button.inline("🔙 Main Menu", "menu_main")
            ]
        ]
        
        stats = await get_stats()
        
        await event.edit(
            f"🤖 **AI INTELLIGENCE CENTER** 🤖\n\n"
            f"🧠 **Current Status:**\n"
            f"• 💭 Sentiment: {stats.get('sentiment_status', 'Unknown')}\n"
            f"• 📝 Summary: {stats.get('summary_status', 'Unknown')}\n"
            f"• 🌍 Translation: {stats.get('translation_status', 'Unknown')}\n"
            f"• 🎯 Filtering: {stats.get('filter_status', 'Unknown')}\n\n"
            f"🧠 **Superhuman Capabilities:**\n"
            f"• 💭 **Sentiment Analysis** - Read the market's mood\n"
            f"• 📝 **Smart Summarization** - Extract key insights instantly\n"
            f"• 🌍 **Auto-Translation** - Break language barriers\n"
            f"• 🎯 **Context-Aware Filtering** - Only relevant alerts\n\n"
            f"*Your AI-powered alpha hunting companion!* ⚡",
            buttons=keyboard
        )

    @client.on(events.CallbackQuery(data="menu_settings"))
    async def menu_settings_callback(event):
        """Handle settings menu button."""
        keyboard = [
            [
                Button.inline("⚙️ General", "settings_general"),
                Button.inline("🔔 Notifications", "settings_notify")
            ],
            [
                Button.inline("🚀 Performance", "settings_perf"),
                Button.inline("🔒 Privacy", "settings_privacy")
            ],
            [
                Button.inline("🗄️ Data", "settings_data"),
                Button.inline("🧹 Cleanup", "settings_cleanup")
            ],
            [
                Button.inline("🔙 Main Menu", "menu_main")
            ]
        ]
        
        await event.edit(
            f"⚙️ **BOT SETTINGS CENTER** ⚙️\n\n"
            f"🔧 **Configuration Options:**\n"
            f"• ⚙️ **General Settings** - Basic bot configuration\n"
            f"• 🔔 **Notifications** - Alert preferences and timing\n"
            f"• 🚀 **Performance** - Speed and resource optimization\n"
            f"• 🔒 **Privacy** - Data handling and security\n"
            f"• 🗄️ **Data Management** - Storage and backup settings\n"
            f"• 🧹 **Cleanup** - Maintenance and cleanup options\n\n"
            f"*Customize your alpha hunting experience!* 🎯",
            buttons=keyboard
        )

    @client.on(events.CallbackQuery(data="menu_stats"))
    async def menu_stats_callback(event):
        """Handle stats menu button."""
        keyboard = [
            [
                Button.inline("📊 Detailed Stats", "stats_detail"),
                Button.inline("📈 Graphs", "stats_graphs")
            ],
            [
                Button.inline("📜 History", "stats_history"),
                Button.inline("❌ Errors", "stats_errors")
            ],
            [
                Button.inline("🔄 Refresh", "stats_refresh"),
                Button.inline("🌐 Dashboard", "stats_dash")
            ],
            [
                Button.inline("🔙 Main Menu", "menu_main")
            ]
        ]
        
        stats = await get_stats()
        
        await event.edit(
            f"📊 **LIVE STATISTICS DASHBOARD** 📊\n\n"
            f"🎯 **Current Performance:**\n"
            f"• 📡 Active Sources: {stats.get('active_sources', 0)}\n"
            f"• 📢 Output Channels: {stats.get('telegram_channels', 0) + stats.get('discord_webhooks', 0)}\n"
            f"• 📊 Total Messages: {stats.get('total_messages', 0)}\n"
            f"• ⚡ Success Rate: {stats.get('success_rate', 0)}%\n"
            f"• 🧠 AI Speed: {stats.get('analysis_speed', 0)}ms\n\n"
            f"📈 **Real-time Monitoring:**\n"
            f"• 📊 **Detailed Stats** - Comprehensive metrics\n"
            f"• 📈 **Graphs** - Visual performance data\n"
            f"• 📜 **History** - Historical trends\n"
            f"• ❌ **Errors** - Error tracking and analysis\n\n"
            f"*Track your alpha hunting performance!* 🚀",
            buttons=keyboard
        )

    @client.on(events.CallbackQuery(data="menu_help"))
    async def menu_help_callback(event):
        """Handle help menu button."""
        keyboard = [
            [
                Button.inline("📖 User Guide", "help_guide"),
                Button.inline("❓ FAQ", "help_faq")
            ],
            [
                Button.inline("🎓 Tutorial", "help_tutorial"),
                Button.inline("🔧 Troubleshooting", "help_trouble")
            ],
            [
                Button.inline("💬 Support", "help_support"),
                Button.inline("📰 Updates", "help_updates")
            ],
            [
                Button.inline("🔙 Main Menu", "menu_main")
            ]
        ]
        
        await event.edit(
            f"❓ **HELP & SUPPORT CENTER** ❓\n\n"
            f"🎯 **Get the Help You Need:**\n"
            f"• 📖 **User Guide** - Complete usage instructions\n"
            f"• ❓ **FAQ** - Frequently asked questions\n"
            f"• 🎓 **Tutorial** - Step-by-step walkthroughs\n"
            f"• 🔧 **Troubleshooting** - Common issues and solutions\n"
            f"• 💬 **Support** - Contact our support team\n"
            f"• 📰 **Updates** - Latest features and improvements\n\n"
            f"*We're here to help you succeed!* 🤝",
            buttons=keyboard
        )

    @client.on(events.CallbackQuery(data="menu_main"))
    async def menu_main_callback(event):
        """Handle main menu button."""
        keyboard = [
            [
                Button.inline("🎯 HUNT SOURCES", "menu_sources"),
                Button.inline("📢 ALERT CHANNELS", "menu_outputs"),
            ],
            [
                Button.inline("🤖 AI INTELLIGENCE", "menu_ai"),
                Button.inline("⚙️ BOT SETTINGS", "menu_settings"),
            ],
            [
                Button.inline("📊 LIVE STATS", "menu_stats"),
                Button.inline("❓ HELP & SUPPORT", "menu_help"),
            ],
            [
                Button.url("🔥 ALPHA COMMUNITY", "https://t.me/MrHuxCommunity"),
                Button.url("📰 LATEST UPDATES", "https://t.me/MrHuxUpdates"),
            ]
        ]
        
        await event.edit(
            UI["messages"]["welcome"],
            buttons=keyboard
        )

    # Source management callbacks
    @client.on(events.CallbackQuery(data="source_add"))
    async def source_add_callback(event):
        """Handle add source button."""
        keyboard = [
            [
                Button.inline("📱 Telegram", "add_telegram_source"),
                Button.inline("💬 Discord", "add_discord_source")
            ],
            [
                Button.inline("🌐 Reddit", "add_reddit_source"),
                Button.inline("📰 RSS", "add_rss_source")
            ],
            [
                Button.inline("🐙 GitHub", "add_github_source"),
                Button.inline("🐦 X/Twitter", "add_twitter_source")
            ],
            [
                Button.inline("🔙 Back to Sources", "menu_sources")
            ]
        ]
        
        await event.edit(
            f"🆕 **ADD NEW ALPHA SOURCE** 🆕\n\n"
            f"🎯 **Choose Your Hunting Ground:**\n"
            f"• 📱 **Telegram** - Groups and channels\n"
            f"• 💬 **Discord** - Servers and communities\n"
            f"• 🌐 **Reddit** - Subreddits and discussions\n"
            f"• 📰 **RSS** - News feeds and blogs\n"
            f"• 🐙 **GitHub** - Repository updates\n"
            f"• 🐦 **X/Twitter** - Social media signals\n\n"
            f"*Select where you want to discover the next big thing!* 🚀",
            buttons=keyboard
        )

    @client.on(events.CallbackQuery(data="add_telegram_source"))
    async def add_telegram_source_callback(event):
        """Handle add Telegram source button."""
        user_id = event.sender_id
        user_states[user_id] = {'action': 'add_telegram_source'}
        
        keyboard = [
            [Button.inline("🔙 Back to Sources", "source_add")]
        ]
        
        await event.edit(
            f"📱 **TELEGRAM ALPHA HUNTING** 📱\n\n"
            f"🎯 **Send the group/channel to monitor:**\n\n"
            f"📝 **Format Examples:**\n"
            f"• **@ Username:** @cryptogroup\n"
            f"• **Username:** cryptogroup (without @)\n"
            f"• **Group ID:** -1001234567890\n"
            f"• **Channel:** @solana_alpha\n\n"
            f"⚡ **Stealth Mode:** We monitor without joining!\n"
            f"🔒 **Privacy:** Your monitoring is completely private\n"
            f"🎯 **Supports:** Both @ usernames and group IDs\n\n"
            f"*Ready to catch that alpha?* 🚀\n\n"
            f"**Type the @username or group ID below:**",
            buttons=keyboard
        )

    @client.on(events.CallbackQuery(data="add_discord_source"))
    async def add_discord_source_callback(event):
        """Handle add Discord source button."""
        user_id = event.sender_id
        user_states[user_id] = {'action': 'add_discord_source'}
        
        keyboard = [
            [Button.inline("🔙 Back to Sources", "source_add")]
        ]
        
        await event.edit(
            f"💬 **DISCORD ALPHA HUNTING** 💬\n\n"
            f"🎯 **Send the Discord server ID to monitor:**\n\n"
            f"🔧 **How to find Server ID:**\n"
            f"1. Enable Developer Mode in Discord\n"
            f"2. Right-click server → Copy ID\n"
            f"3. Paste the ID below\n\n"
            f"📝 **Example:** 123456789012345678\n\n"
            f"⚡ **Features:**\n"
            f"• Monitor all channels in the server\n"
            f"• Real-time message tracking\n"
            f"• Smart filtering and alerts\n\n"
            f"*Let's hunt some Discord alpha!* 🔥\n\n"
            f"**Type the server ID below:**",
            buttons=keyboard
        )

    @client.on(events.CallbackQuery(data="add_reddit_source"))
    async def add_reddit_source_callback(event):
        """Handle add Reddit source button."""
        user_id = event.sender_id
        user_states[user_id] = {'action': 'add_reddit_source'}
        
        keyboard = [
            [Button.inline("🔙 Back to Sources", "source_add")]
        ]
        
        await event.edit(
            f"🌐 **REDDIT ALPHA HUNTING** 🌐\n\n"
            f"🎯 **Send the subreddit name to monitor:**\n\n"
            f"📝 **Popular Examples:**\n"
            f"• **solana** - Solana ecosystem\n"
            f"• **CryptoMoonShots** - Moon potential\n"
            f"• **defi** - DeFi discussions\n"
            f"• **cryptocurrency** - General crypto\n"
            f"• **altcoin** - Altcoin discussions\n\n"
            f"⚡ **Features:**\n"
            f"• Monitor posts and comments\n"
            f"• Sentiment analysis\n"
            f"• Trending topic detection\n"
            f"• Real-time alerts\n\n"
            f"*Reddit alpha is waiting!* 🚀\n\n"
            f"**Type the subreddit name below:**",
            buttons=keyboard
        )

    @client.on(events.CallbackQuery(data="add_twitter_source"))
    async def add_twitter_source_callback(event):
        """Handle add Twitter source button."""
        user_id = event.sender_id
        user_states[user_id] = {'action': 'add_twitter_source'}
        
        keyboard = [
            [Button.inline("🔙 Back to Sources", "source_add")]
        ]
        
        await event.edit(
            f"🐦 **X/TWITTER ALPHA HUNTING** 🐦\n\n"
            f"🎯 **Send the username to monitor:**\n\n"
            f"📝 **Format Examples:**\n"
            f"• **@username** - With @ symbol\n"
            f"• **username** - Without @ symbol\n\n"
            f"🎯 **Popular Alpha Accounts:**\n"
            f"• @solana - Official Solana\n"
            f"• @VitalikButerin - Ethereum founder\n"
            f"• @cz_binance - Binance CEO\n\n"
            f"⚡ **Features:**\n"
            f"• Monitor tweets and replies\n"
            f"• Sentiment analysis\n"
            f"• Trend detection\n"
            f"• Real-time alerts\n\n"
            f"*Twitter alpha is waiting!* 🚀\n\n"
            f"**Type the username below:**",
            buttons=keyboard
        )

    @client.on(events.CallbackQuery(data="add_rss_source"))
    async def add_rss_source_callback(event):
        """Handle add RSS source button."""
        user_id = event.sender_id
        user_states[user_id] = {'action': 'add_rss_source'}
        
        keyboard = [
            [Button.inline("🔙 Back to Sources", "source_add")]
        ]
        
        await event.edit(
            f"📰 **RSS ALPHA HUNTING** 📰\n\n"
            f"🎯 **Send the RSS feed URL to monitor:**\n\n"
            f"📝 **Popular Examples:**\n"
            f"• **CoinDesk:** https://www.coindesk.com/arc/outboundfeeds/rss/\n"
            f"• **Cointelegraph:** https://cointelegraph.com/rss\n"
            f"• **Decrypt:** https://decrypt.co/feed\n\n"
            f"⚡ **Features:**\n"
            f"• Monitor news feeds\n"
            f"• Article analysis\n"
            f"• Keyword filtering\n"
            f"• Real-time alerts\n\n"
            f"*Stay ahead with RSS alpha!* 📰\n\n"
            f"**Type the RSS URL below:**",
            buttons=keyboard
        )

    @client.on(events.CallbackQuery(data="add_github_source"))
    async def add_github_source_callback(event):
        """Handle add GitHub source button."""
        user_id = event.sender_id
        user_states[user_id] = {'action': 'add_github_source'}
        
        keyboard = [
            [Button.inline("🔙 Back to Sources", "source_add")]
        ]
        
        await event.edit(
            f"🐙 **GITHUB ALPHA HUNTING** 🐙\n\n"
            f"🎯 **Send the repository to monitor:**\n\n"
            f"📝 **Format:** owner/repo\n"
            f"📝 **Examples:**\n"
            f"• **solana-labs/solana** - Solana blockchain\n"
            f"• **ethereum/go-ethereum** - Ethereum client\n"
            f"• **bitcoin/bitcoin** - Bitcoin core\n\n"
            f"⚡ **Features:**\n"
            f"• Monitor commits and releases\n"
            f"• Issue tracking\n"
            f"• Pull request monitoring\n"
            f"• Real-time alerts\n\n"
            f"*GitHub alpha is waiting!* 🚀\n\n"
            f"**Type the repository (owner/repo) below:**",
            buttons=keyboard
        )

    # Output management callbacks
    @client.on(events.CallbackQuery(data="output_add"))
    async def output_add_callback(event):
        """Handle add output button."""
        keyboard = [
            [
                Button.inline("📱 Telegram Channel", "add_telegram_channel"),
                Button.inline("💬 Discord Webhook", "add_discord_webhook")
            ],
            [
                Button.inline("🌐 Dashboard", "add_dashboard_output"),
                Button.inline("📧 Email", "add_email_output")
            ],
            [
                Button.inline("🔙 Back to Outputs", "menu_outputs")
            ]
        ]
        
        await event.edit(
            f"📢 **ADD ALERT CHANNEL** 📢\n\n"
            f"🎯 **Choose Your Alert Destination:**\n"
            f"• 📱 **Telegram Channel** - Send to your groups/channels\n"
            f"• 💬 **Discord Webhook** - Integrate with Discord servers\n"
            f"• 🌐 **Dashboard** - Web-based monitoring\n"
            f"• 📧 **Email** - Email notifications\n\n"
            f"⚡ **Features:**\n"
            f"• Real-time alerts\n"
            f"• Rich formatting\n"
            f"• Custom templates\n"
            f"• Delivery confirmation\n\n"
            f"*Never miss important signals!* 🔥",
            buttons=keyboard
        )

    @client.on(events.CallbackQuery(data="add_telegram_channel"))
    async def add_telegram_channel_callback(event):
        """Handle add Telegram channel button."""
        user_id = event.sender_id
        user_states[user_id] = {'action': 'add_telegram_channel'}
        
        keyboard = [
            [Button.inline("🔙 Back to Outputs", "output_add")]
        ]
        
        await event.edit(
            f"📱 **ADD TELEGRAM CHANNEL** 📱\n\n"
            f"🎯 **Send the channel/group to receive alerts:**\n\n"
            f"📝 **Format Examples:**\n"
            f"• **Username:** @myalerts\n"
            f"• **Channel ID:** -1001234567890\n"
            f"• **Group:** @mygroup\n\n"
            f"⚡ **Setup Instructions:**\n"
            f"1. Add the bot to your channel/group\n"
            f"2. Make the bot an admin (for channels)\n"
            f"3. Send the username or ID below\n\n"
            f"🔒 **Privacy:** Only you can see your alerts\n\n"
            f"*Ready to receive alpha alerts!* 🚀\n\n"
            f"**Type the channel/group below:**",
            buttons=keyboard
        )

    @client.on(events.CallbackQuery(data="add_discord_webhook"))
    async def add_discord_webhook_callback(event):
        """Handle add Discord webhook button."""
        user_id = event.sender_id
        user_states[user_id] = {'action': 'add_discord_webhook'}
        
        keyboard = [
            [Button.inline("🔙 Back to Outputs", "output_add")]
        ]
        
        await event.edit(
            f"💬 **ADD DISCORD WEBHOOK** 💬\n\n"
            f"🎯 **Send the Discord webhook URL:**\n\n"
            f"🔧 **How to create a webhook:**\n"
            f"1. Go to your Discord server\n"
            f"2. Server Settings → Integrations → Webhooks\n"
            f"3. Create New Webhook\n"
            f"4. Copy the webhook URL\n"
            f"5. Paste it below\n\n"
            f"📝 **Format:** https://discord.com/api/webhooks/...\n\n"
            f"⚡ **Features:**\n"
            f"• Rich embeds\n"
            f"• Custom formatting\n"
            f"• Real-time delivery\n"
            f"• Error handling\n\n"
            f"*Ready to send Discord alerts!* 🔥\n\n"
            f"**Type the webhook URL below:**",
            buttons=keyboard
        )

    @client.on(events.CallbackQuery(data="add_dashboard_output"))
    async def add_dashboard_output_callback(event):
        """Handle add dashboard output button."""
        keyboard = [
            [Button.inline("✅ Dashboard Added!", "menu_outputs")],
            [Button.inline("🔙 Back to Outputs", "output_add")]
        ]
        
        await event.edit(
            f"🌐 **DASHBOARD OUTPUT ADDED** 🌐\n\n"
            f"✅ **Dashboard is automatically enabled!**\n\n"
            f"🌐 **Access your dashboard:**\n"
            f"• **URL:** http://localhost:8000\n"
            f"• **Features:** Real-time monitoring\n"
            f"• **Updates:** Live statistics\n\n"
            f"⚡ **Dashboard Features:**\n"
            f"• Real-time alerts\n"
            f"• Source management\n"
            f"• Statistics and graphs\n"
            f"• Settings configuration\n\n"
            f"*Your web dashboard is ready!* 🚀",
            buttons=keyboard
        )

    # View sources and outputs
    @client.on(events.CallbackQuery(data="source_list"))
    async def source_list_callback(event):
        """Handle view sources button."""
        try:
            with db_session() as db:
                sources = db.query(MonitoredSource).filter(
                    MonitoredSource.is_active == True
                ).all()
                # Convert to dicts before session closes
                source_dicts = [
                    {
                        'type': s.type.value if hasattr(s.type, 'value') else str(s.type),
                        'name': s.name or s.identifier
                    }
                    for s in sources
                ]
            if not source_dicts:
                keyboard = [
                    [Button.inline("➕ Add First Source", "source_add")],
                    [Button.inline("🔙 Back to Sources", "menu_sources")]
                ]
                await event.edit(
                    f"📋 **ACTIVE SOURCES** 📋\n\n"
                    f"❌ **No sources found**\n\n"
                    f"🎯 **Get started by adding your first source!**\n"
                    f"• 📱 Telegram groups\n"
                    f"• 💬 Discord servers\n"
                    f"• 🌐 Reddit subreddits\n"
                    f"• 🐦 Twitter accounts\n\n"
                    f"*Ready to start hunting alpha?* 🚀",
                    buttons=keyboard
                )
            else:
                source_list = "\n".join([
                    f"• {src['type']}: {src['name']}" for src in source_dicts[:10]
                ])
                keyboard = [
                    [Button.inline("➕ Add More", "source_add")],
                    [Button.inline("🔙 Back to Sources", "menu_sources")]
                ]
                await event.edit(
                    f"📋 **ACTIVE SOURCES** 📋\n\n"
                    f"✅ **Found {len(source_dicts)} active sources:**\n\n"
                    f"{source_list}\n\n"
                    f"{'... and more' if len(source_dicts) > 10 else ''}\n\n"
                    f"🎯 **All sources are actively monitoring for alpha!**",
                    buttons=keyboard
                )
        except Exception as e:
            logger.error(f"Error listing sources: {e}")
            keyboard = [
                [Button.inline("🔙 Back to Sources", "menu_sources")]
            ]
            await event.edit(
                f"❌ **Error loading sources**\n\n"
                f"Please try again or contact support.",
                buttons=keyboard
            )

    @client.on(events.CallbackQuery(data="output_list"))
    async def output_list_callback(event):
        """Handle view outputs button."""
        try:
            with db_session() as db:
                outputs = db.query(OutputChannel).filter(OutputChannel.is_active == True).all()
                # Convert to dicts before session closes
                output_dicts = [
                    {
                        'type': o.type.value if hasattr(o.type, 'value') else str(o.type),
                        'name': o.name or o.identifier
                    }
                    for o in outputs
                ]
            if not output_dicts:
                keyboard = [
                    [Button.inline("➕ Add Output", "output_add")],
                    [Button.inline("🔙 Back to Outputs", "menu_outputs")]
                ]
                await event.edit(
                    f"📢 **ACTIVE OUTPUTS** 📢\n\n"
                    f"❌ **No outputs found**\n\n"
                    f"*Add an output channel to start receiving alerts!* 🚀",
                    buttons=keyboard
                )
            else:
                output_list = "\n".join([
                    f"• {out['type']}: {out['name']}" for out in output_dicts[:10]
                ])
                keyboard = [
                    [Button.inline("➕ Add More", "output_add")],
                    [Button.inline("🔙 Back to Outputs", "menu_outputs")]
                ]
                await event.edit(
                    f"📢 **ACTIVE OUTPUTS** 📢\n\n"
                    f"✅ **Found {len(output_dicts)} active outputs:**\n\n"
                    f"{output_list}\n\n"
                    f"{'... and more' if len(output_dicts) > 10 else ''}\n\n"
                    f"*All outputs are ready to deliver alerts!* 🚀",
                    buttons=keyboard
                )
        except Exception as e:
            logger.error(f"Error listing outputs: {e}")
            keyboard = [
                [Button.inline("🔙 Back to Outputs", "menu_outputs")]
            ]
            await event.edit(
                f"❌ **Error loading outputs**\n\n"
                f"Please try again or contact support.",
                buttons=keyboard
            )
