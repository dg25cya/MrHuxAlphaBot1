"""Bot command handlers with enhanced UI and features."""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from telethon import events, TelegramClient, Button
from telethon.tl.custom import Message
from loguru import logger
import emoji
import threading
import time
from telethon.errors.rpcerrorlist import MessageNotModifiedError

from src.config.settings import get_settings
from src.models.monitored_source import MonitoredSource, SourceType, OutputChannel, OutputType
from src.core.services.source_handlers import SourceManager
from src.core.services.output_service import OutputService
from src.core.services.text_analysis import TextAnalysisService
from src.utils.db import db_session
from src.core.telegram.listener import get_sources_summary
from src.core.services.token_monitor import TokenMonitor
from src.core.services.continuous_hunter import ContinuousPlayHunter

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

    # Place the helper before any callback handlers so it's in scope
    async def safe_edit_event_message(event, text=None, **kwargs):
        """
        Edits the event message only if the content or markup is different.
        """
        message = await event.get_message()
        current_text = message.text or message.message
        new_text = text or kwargs.get("message") or kwargs.get("text")
        markup = kwargs.get("buttons") or kwargs.get("reply_markup")
        current_markup = message.reply_markup
        # If both text and markup are unchanged, skip edit
        if current_text == new_text and current_markup == markup:
            return
        try:
            await event.edit(text, **kwargs)
        except MessageNotModifiedError:
            pass  # Silently ignore

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
                    # Try to resolve both chat_id and @username if possible
                    identifier = text
                    name = f"Telegram: {text}"
                    # If the text is an @username, try to resolve to chat_id
                    if text.startswith('@'):
                        # Try to get chat_id using Telegram API
                        try:
                            entity = await client.get_entity(text)
                            # get_entity may return a list, use first if so
                            if isinstance(entity, list):
                                entity = entity[0]
                            if hasattr(entity, 'id'):
                                identifier = str(entity.id)
                                name = f"Telegram: {text} ({identifier})"
                        except Exception as e:
                            logger.warning(f"Could not resolve chat_id for {text}: {e}")
                    source_data = {
                        'type': SourceType.TELEGRAM,
                        'identifier': identifier,
                        'name': name,
                        'is_active': True
                    }
                    with db_session() as db:
                        source = MonitoredSource(**source_data)
                        db.add(source)
                        db.commit()
                        # After adding, scan last 30 minutes of messages for this source
                        from src.core.telegram.listener import scan_last_30min_messages
                        import asyncio
                        # Only scan this new source
                        class DummySource:
                            def __init__(self, identifier, name):
                                self.identifier = identifier
                                self.name = name
                                self.type = 'telegram'
                                self.is_active = True
                        dummy_source = DummySource(identifier, name)
                        async def scan_new_source():
                            await scan_last_30min_messages(client, db, sources=[dummy_source])
                        asyncio.create_task(scan_new_source())
                    # Clear user state
                    del user_states[user_id]
                    keyboard = [
                        [Button.inline("✅ Source Added!", "menu_sources")],
                        [Button.inline("➕ Add Another", "source_add")],
                        [Button.inline("🔙 Main Menu", "menu_main")]
                    ]
                    await safe_edit_event_message(event,
                        f"✅ **Telegram Source Added Successfully!**\n\n"
                        f"📱 **Source:** {text}\n"
                        f"🆔 **Identifier:** {identifier}\n"
                        f"🎯 **Status:** Active and monitoring\n"
                        f"⚡ **Next:** Start receiving alerts!",
                        buttons=keyboard
                    )
                    
                except Exception as e:
                    logger.error(f"Error adding Telegram source: {e}")
                    await safe_edit_event_message(event,
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
                    
                    await safe_edit_event_message(event,
                        f"✅ **Discord Source Added Successfully!**\n\n"
                        f"💬 **Server ID:** {text}\n"
                        f"🎯 **Status:** Active and monitoring\n"
                        f"⚡ **Next:** Start receiving alerts!",
                        buttons=keyboard
                    )
                    
                except Exception as e:
                    logger.error(f"Error adding Discord source: {e}")
                    await safe_edit_event_message(event,
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
                    
                    await safe_edit_event_message(event,
                        f"✅ **Reddit Source Added Successfully!**\n\n"
                        f"🌐 **Subreddit:** r/{text}\n"
                        f"🎯 **Status:** Active and monitoring\n"
                        f"⚡ **Next:** Start receiving alerts!",
                        buttons=keyboard
                    )
                    
                except Exception as e:
                    logger.error(f"Error adding Reddit source: {e}")
                    await safe_edit_event_message(event,
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
                    
                    await safe_edit_event_message(event,
                        f"✅ **Twitter Source Added Successfully!**\n\n"
                        f"🐦 **Username:** @{username}\n"
                        f"🎯 **Status:** Active and monitoring\n"
                        f"⚡ **Next:** Start receiving alerts!",
                        buttons=keyboard
                    )
                    
                except Exception as e:
                    logger.error(f"Error adding Twitter source: {e}")
                    await safe_edit_event_message(event,
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
                    
                    await safe_edit_event_message(event,
                        f"✅ **RSS Source Added Successfully!**\n\n"
                        f"📰 **Feed:** {text[:100]}...\n"
                        f"🎯 **Status:** Active and monitoring\n"
                        f"⚡ **Next:** Start receiving alerts!",
                        buttons=keyboard
                    )
                    
                except Exception as e:
                    logger.error(f"Error adding RSS source: {e}")
                    await safe_edit_event_message(event,
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
                    
                    await safe_edit_event_message(event,
                        f"✅ **GitHub Source Added Successfully!**\n\n"
                        f"🐙 **Repository:** {text}\n"
                        f"🎯 **Status:** Active and monitoring\n"
                        f"⚡ **Next:** Start receiving alerts!",
                        buttons=keyboard
                    )
                    
                except Exception as e:
                    logger.error(f"Error adding GitHub source: {e}")
                    await safe_edit_event_message(event,
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
                    
                    await safe_edit_event_message(event,
                        f"✅ **Discord Webhook Added Successfully!**\n\n"
                        f"💬 **Status:** Active and ready\n"
                        f"⚡ **Next:** Start receiving alerts!",
                        buttons=keyboard
                    )
                    
                except Exception as e:
                    logger.error(f"Error adding Discord webhook: {e}")
                    await safe_edit_event_message(event,
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
                    
                    await safe_edit_event_message(event,
                        f"✅ **Telegram Channel Added Successfully!**\n\n"
                        f"📱 **Channel:** {text}\n"
                        f"🎯 **Status:** Active and ready\n"
                        f"⚡ **Next:** Start receiving alerts!",
                        buttons=keyboard
                    )
                    
                except Exception as e:
                    logger.error(f"Error adding Telegram channel: {e}")
                    await safe_edit_event_message(event,
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
        
        new_text = (
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
            f"*Ready to discover the next big thing?* ��"
        )
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

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
        
        new_text = (
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
            f"*Never miss a signal again!* ��"
        )
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

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
        
        new_text = (
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
            f"*Your AI-powered alpha hunting companion!* ⚡"
        )
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

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
        
        new_text = (
            f"⚙️ **BOT SETTINGS CENTER** ⚙️\n\n"
            f"🔧 **Configuration Options:**\n"
            f"• ⚙️ **General Settings** - Basic bot configuration\n"
            f"• 🔔 **Notifications** - Alert preferences and timing\n"
            f"• 🚀 **Performance** - Speed and resource optimization\n"
            f"• 🔒 **Privacy** - Data handling and security\n"
            f"• 🗄️ **Data Management** - Storage and backup settings\n"
            f"• 🧹 **Cleanup** - Maintenance and cleanup options\n\n"
            f"*Customize your alpha hunting experience!* ��"
        )
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

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
        
        new_text = (
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
            f"*Track your alpha hunting performance!* ��"
        )
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

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
        
        new_text = (
            f"❓ **HELP & SUPPORT CENTER** ❓\n\n"
            f"🎯 **Get the Help You Need:**\n"
            f"• 📖 **User Guide** - Complete usage instructions\n"
            f"• ❓ **FAQ** - Frequently asked questions\n"
            f"• 🎓 **Tutorial** - Step-by-step walkthroughs\n"
            f"• 🔧 **Troubleshooting** - Common issues and solutions\n"
            f"• 💬 **Support** - Contact our support team\n"
            f"• 📰 **Updates** - Latest features and improvements\n\n"
            f"*We're here to help you succeed!* ��"
        )
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

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
        
        new_text = (
            UI["messages"]["welcome"]
        )
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

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
        
        new_text = (
            f"🆕 **ADD NEW ALPHA SOURCE** 🆕\n\n"
            f"🎯 **Choose Your Hunting Ground:**\n"
            f"• 📱 **Telegram** - Groups and channels\n"
            f"• 💬 **Discord** - Servers and communities\n"
            f"• 🌐 **Reddit** - Subreddits and discussions\n"
            f"• 📰 **RSS** - News feeds and blogs\n"
            f"• 🐙 **GitHub** - Repository updates\n"
            f"• 🐦 **X/Twitter** - Social media signals\n\n"
            f"*Select where you want to discover the next big thing!* ��"
        )
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

    @client.on(events.CallbackQuery(data="add_telegram_source"))
    async def add_telegram_source_callback(event):
        """Handle add Telegram source button."""
        user_id = event.sender_id
        user_states[user_id] = {'action': 'add_telegram_source'}
        
        keyboard = [
            [Button.inline("🔙 Back to Sources", "source_add")]
        ]
        
        new_text = (
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
            f"**Type the @username or group ID below:**"
        )
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

    @client.on(events.CallbackQuery(data="add_discord_source"))
    async def add_discord_source_callback(event):
        """Handle add Discord source button."""
        user_id = event.sender_id
        user_states[user_id] = {'action': 'add_discord_source'}
        
        keyboard = [
            [Button.inline("🔙 Back to Sources", "source_add")]
        ]
        
        new_text = (
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
            f"**Type the server ID below:**"
        )
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

    @client.on(events.CallbackQuery(data="add_reddit_source"))
    async def add_reddit_source_callback(event):
        """Handle add Reddit source button."""
        user_id = event.sender_id
        user_states[user_id] = {'action': 'add_reddit_source'}
        
        keyboard = [
            [Button.inline("🔙 Back to Sources", "source_add")]
        ]
        
        new_text = (
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
            f"**Type the subreddit name below:**"
        )
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

    @client.on(events.CallbackQuery(data="add_twitter_source"))
    async def add_twitter_source_callback(event):
        """Handle add Twitter source button."""
        user_id = event.sender_id
        user_states[user_id] = {'action': 'add_twitter_source'}
        
        keyboard = [
            [Button.inline("🔙 Back to Sources", "source_add")]
        ]
        
        new_text = (
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
            f"**Type the username below:**"
        )
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

    @client.on(events.CallbackQuery(data="add_rss_source"))
    async def add_rss_source_callback(event):
        """Handle add RSS source button."""
        user_id = event.sender_id
        user_states[user_id] = {'action': 'add_rss_source'}
        
        keyboard = [
            [Button.inline("🔙 Back to Sources", "source_add")]
        ]
        
        new_text = (
            f"📰 **RSS ALPHA HUNTING** 📰\n\n"
            f"🎯 **Send the RSS feed URL to monitor:**\n\n"
            f"�� **Popular Examples:**\n"
            f"• **CoinDesk:** https://www.coindesk.com/arc/outboundfeeds/rss/\n"
            f"• **Cointelegraph:** https://cointelegraph.com/rss\n"
            f"• **Decrypt:** https://decrypt.co/feed\n\n"
            f"⚡ **Features:**\n"
            f"• Monitor news feeds\n"
            f"• Article analysis\n"
            f"• Keyword filtering\n"
            f"• Real-time alerts\n\n"
            f"*Stay ahead with RSS alpha!* 📰\n\n"
            f"**Type the RSS URL below:**"
        )
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

    @client.on(events.CallbackQuery(data="add_github_source"))
    async def add_github_source_callback(event):
        """Handle add GitHub source button."""
        user_id = event.sender_id
        user_states[user_id] = {'action': 'add_github_source'}
        
        keyboard = [
            [Button.inline("🔙 Back to Sources", "source_add")]
        ]
        
        new_text = (
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
            f"**Type the repository (owner/repo) below:**"
        )
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

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
        
        new_text = (
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
            f"*Never miss important signals!* ��"
        )
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

    @client.on(events.CallbackQuery(data="add_telegram_channel"))
    async def add_telegram_channel_callback(event):
        """Handle add Telegram channel button."""
        user_id = event.sender_id
        user_states[user_id] = {'action': 'add_telegram_channel'}
        
        keyboard = [
            [Button.inline("🔙 Back to Outputs", "output_add")]
        ]
        
        new_text = (
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
            f"**Type the channel/group below:**"
        )
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

    @client.on(events.CallbackQuery(data="add_discord_webhook"))
    async def add_discord_webhook_callback(event):
        """Handle add Discord webhook button."""
        user_id = event.sender_id
        user_states[user_id] = {'action': 'add_discord_webhook'}
        
        keyboard = [
            [Button.inline("🔙 Back to Outputs", "output_add")]
        ]
        
        new_text = (
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
            f"**Type the webhook URL below:**"
        )
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

    @client.on(events.CallbackQuery(data="add_dashboard_output"))
    async def add_dashboard_output_callback(event):
        text = "🌐 **Dashboard Output Added!**\n\nYour dashboard is always enabled.\n\nAccess it here: https://mr-hux-alpha-bot.onrender.com\n"
        await safe_edit_event_message(event, text, buttons=[[Button.inline("🔙 Back to Outputs", "output_add")]])

    # View sources and outputs
    @client.on(events.CallbackQuery(data="source_list"))
    async def source_list_callback(event):
        """Handle view sources button."""
        try:
            with db_session() as db:
                sources = db.query(MonitoredSource).filter(
                    MonitoredSource.is_active == True
                ).all()
                source_dicts = [
                    {
                        'id': s.id,
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
                new_text = (
                    f"📋 **ACTIVE SOURCES** 📋\n\n"
                    f"❌ **No sources found**\n\n"
                    f"🎯 **Get started by adding your first source!**\n"
                    f"• 📱 Telegram groups\n"
                    f"• 💬 Discord servers\n"
                    f"• 🌐 Reddit subreddits\n"
                    f"• 🐦 Twitter accounts\n\n"
                    f"*Ready to start hunting alpha?* 🚀"
                )
                message = await event.get_message()
                if message and hasattr(message, 'text') and message.text != new_text:
                    await safe_edit_event_message(event, new_text, buttons=keyboard)
            else:
                source_list = "\n".join([
                    f"• {src['type']}: {src['name']}" for src in source_dicts[:10]
                ])
                keyboard = []
                for src in source_dicts[:10]:
                    keyboard.append([
                        Button.inline(f"❌ Remove {src['name']}", f"remove_source_{src['id']}")
                    ])
                keyboard.append([Button.inline("➕ Add More", "source_add")])
                keyboard.append([Button.inline("🔙 Back to Sources", "menu_sources")])
                new_text = (
                    f"📋 **ACTIVE SOURCES** 📋\n\n"
                    f"✅ **Found {len(source_dicts)} active sources:**\n\n"
                    f"{source_list}\n\n"
                    f"{'... and more' if len(source_dicts) > 10 else ''}\n\n"
                    f"🎯 **All sources are actively monitoring for alpha!**"
                )
                message = await event.get_message()
                if message and hasattr(message, 'text') and message.text != new_text:
                    await safe_edit_event_message(event, new_text, buttons=keyboard)
        except Exception as e:
            logger.error(f"Error listing sources: {e}")
            keyboard = [
                [Button.inline("🔙 Back to Sources", "menu_sources")]
            ]
            await safe_edit_event_message(event, f"❌ **Error loading sources**\n\nPlease try again or contact support.", buttons=keyboard)

    @client.on(events.CallbackQuery(pattern=r"remove_source_\\d+"))
    async def remove_source_callback(event):
        source_id = int(event.data.decode().split("_")[-1])
        # Ask for confirmation
        keyboard = [
            [Button.inline("✅ Confirm Remove", f"confirm_remove_source_{source_id}"), Button.inline("❌ Cancel", "source_list")]
        ]
        await safe_edit_event_message(event, f"⚠️ Are you sure you want to remove this source? This cannot be undone.", buttons=keyboard)

    @client.on(events.CallbackQuery(pattern=r"confirm_remove_source_\\d+"))
    async def confirm_remove_source_callback(event):
        source_id = int(event.data.decode().split("_")[-1])
        with db_session() as db:
            source = db.query(MonitoredSource).get(source_id)
            if not source:
                await safe_edit_event_message(event, "❌ Source not found.", buttons=[[Button.inline("🔙 Back to Sources", "source_list")]])
                return
            db.delete(source)
            db.commit()
        await safe_edit_event_message(event, "✅ Source removed successfully.", buttons=[[Button.inline("🔙 Back to Sources", "source_list")]])

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
                new_text = (
                    f"📢 **ACTIVE OUTPUTS** 📢\n\n"
                    f"❌ **No outputs found**\n\n"
                    f"*Add an output channel to start receiving alerts!* 📢"
                )
                message = await event.get_message()
                if message and hasattr(message, 'text') and message.text != new_text:
                    await safe_edit_event_message(event, new_text, buttons=keyboard)
            else:
                output_list = "\n".join([
                    f"• {out['type']}: {out['name']}" for out in output_dicts[:10]
                ])
                keyboard = [
                    [Button.inline("➕ Add More", "output_add")],
                    [Button.inline("🔙 Back to Outputs", "menu_outputs")]
                ]
                new_text = (
                    f"📢 **ACTIVE OUTPUTS** 📢\n\n"
                    f"✅ **Found {len(output_dicts)} active outputs:**\n\n"
                    f"{output_list}\n\n"
                    f"{'... and more' if len(output_dicts) > 10 else ''}\n\n"
                    f"*All outputs are ready to deliver alerts!* 🚀"
                )
                message = await event.get_message()
                if message and hasattr(message, 'text') and message.text != new_text:
                    await safe_edit_event_message(event, new_text, buttons=keyboard)
        except Exception as e:
            logger.error(f"Error listing outputs: {e}")
            keyboard = [
                [Button.inline("🔙 Back to Outputs", "menu_outputs")]
            ]
            await safe_edit_event_message(event, f"❌ **Error loading outputs**\n\nPlease try again or contact support.", buttons=keyboard)

    # --- PLACEHOLDER HANDLERS FOR ALL BUTTONS ---
    # Utility for placeholder
    async def placeholder_handler(event, title, back_data, back_text):
        keyboard = [[Button.inline(back_text, back_data)]]
        new_text = f"{title}\n\n🚧 This feature is coming soon!"
        message = await event.get_message()
        if message and hasattr(message, 'text') and message.text != new_text:
            await safe_edit_event_message(event, new_text, buttons=keyboard)

    # Source Filters
    @client.on(events.CallbackQuery(data="source_filters"))
    async def source_filters_callback(event):
        user_id = event.sender_id
        with db_session() as db:
            sources = db.query(MonitoredSource).filter(MonitoredSource.is_active == True).all()
            if not sources:
                await safe_edit_event_message(event, "❌ No sources found. Add a source first.", buttons=[[Button.inline("🔙 Back to Sources", "menu_sources")]])
                return
            if len(sources) == 1:
                source = sources[0]
                user_states[user_id] = {"action": "manage_filters", "source_id": source.id}
                await show_filters_menu(event, source)
                return
            # Multiple sources: let user pick
            keyboard = [[Button.inline(f"{s.name or s.identifier}", f"filter_src_{s.id}")] for s in sources]
            keyboard.append([Button.inline("🔙 Back to Sources", "menu_sources")])
            await safe_edit_event_message(event, "🔍 **Select a source to manage filters:**", buttons=keyboard)

    @client.on(events.CallbackQuery(pattern=r"filter_src_\d+"))
    async def filter_source_select_callback(event):
        user_id = event.sender_id
        source_id = int(event.data.decode().split("_")[-1])
        with db_session() as db:
            source = db.query(MonitoredSource).get(source_id)
            if not source:
                await safe_edit_event_message(event, "❌ Source not found.", buttons=[[Button.inline("🔙 Back", "source_filters")]])
                return
            user_states[user_id] = {"action": "manage_filters", "source_id": source.id}
            await show_filters_menu(event, source)

    async def show_filters_menu(event, source):
        filters = source.custom_filters or {}
        filter_list = filters.get("keywords", [])
        text = f"🔍 **Filters for {source.name or source.identifier}:**\n\n"
        if filter_list:
            text += "\n".join([f"• `{f}`" for f in filter_list]) + "\n\n"
        else:
            text += "_No filters set._\n\n"
        keyboard = []
        if filter_list:
            for idx, f in enumerate(filter_list):
                keyboard.append([Button.inline(f"❌ Remove: {f}", f"remove_filter_{source.id}_{idx}")])
        keyboard.append([Button.inline("➕ Add Filter", f"add_filter_{source.id}")])
        keyboard.append([Button.inline("🔙 Back to Sources", "menu_sources")])
        await safe_edit_event_message(event, text, buttons=keyboard)

    @client.on(events.CallbackQuery(pattern=r"add_filter_\d+"))
    async def add_filter_callback(event):
        user_id = event.sender_id
        source_id = int(event.data.decode().split("_")[-1])
        user_states[user_id] = {"action": "awaiting_filter_input", "source_id": source_id}
        await safe_edit_event_message(event, "✏️ **Send the keyword or regex to add as a filter:**\n\n_Example: presale, moon, pump, ^SOL_", buttons=[[Button.inline("🔙 Cancel", f"filter_src_{source_id}")]])

    @client.on(events.NewMessage(pattern=r'^(?!/).+'))
    async def handle_filter_input(event: Message):
        user_id = event.sender_id
        state = user_states.get(user_id)
        if not state or state.get("action") != "awaiting_filter_input":
            return
        filter_text = (event.text or "").strip()
        source_id = state["source_id"]
        with db_session() as db:
            source = db.query(MonitoredSource).get(source_id)
            if not source:
                await event.reply("❌ Source not found.")
                return
            filters = source.custom_filters or {}
            filter_list = filters.get("keywords", [])
            if filter_text in filter_list:
                await event.reply("⚠️ This filter already exists.")
                return
            filter_list.append(filter_text)
            filters["keywords"] = filter_list
            source.custom_filters = filters
            db.commit()
        del user_states[user_id]
        await show_filters_menu(event, source)

    @client.on(events.CallbackQuery(pattern=r"remove_filter_\d+_\d+"))
    async def remove_filter_callback(event):
        user_id = event.sender_id
        parts = event.data.decode().split("_")
        source_id = int(parts[2])
        idx = int(parts[3])
        with db_session() as db:
            source = db.query(MonitoredSource).get(source_id)
            if not source:
                await safe_edit_event_message(event, "❌ Source not found.", buttons=[[Button.inline("🔙 Back", "source_filters")]])
                return
            filters = source.custom_filters or {}
            filter_list = filters.get("keywords", [])
            if idx < 0 or idx >= len(filter_list):
                await safe_edit_event_message(event, "❌ Invalid filter index.", buttons=[[Button.inline("🔙 Back", f"filter_src_{source_id}")]])
                return
            removed = filter_list.pop(idx)
            filters["keywords"] = filter_list
            source.custom_filters = filters
            db.commit()
        await show_filters_menu(event, source)

    # Source Schedule
    @client.on(events.CallbackQuery(data="source_schedule"))
    async def source_schedule_callback(event):
        user_id = event.sender_id
        with db_session() as db:
            sources = db.query(MonitoredSource).filter(MonitoredSource.is_active == True).all()
            if not sources:
                await safe_edit_event_message(event, "❌ No sources found. Add a source first.", buttons=[[Button.inline("🔙 Back to Sources", "menu_sources")]])
                return
            if len(sources) == 1:
                source = sources[0]
                user_states[user_id] = {"action": "manage_schedule", "source_id": source.id}
                await show_schedule_menu(event, source)
                return
            # Multiple sources: let user pick
            keyboard = [[Button.inline(f"{s.name or s.identifier}", f"schedule_src_{s.id}")] for s in sources]
            keyboard.append([Button.inline("🔙 Back to Sources", "menu_sources")])
            await safe_edit_event_message(event, "⏰ **Select a source to manage scan schedule:**", buttons=keyboard)

    @client.on(events.CallbackQuery(pattern=r"schedule_src_\d+"))
    async def schedule_source_select_callback(event):
        user_id = event.sender_id
        source_id = int(event.data.decode().split("_")[-1])
        with db_session() as db:
            source = db.query(MonitoredSource).get(source_id)
            if not source:
                await safe_edit_event_message(event, "❌ Source not found.", buttons=[[Button.inline("🔙 Back", "source_schedule")]])
                return
            user_states[user_id] = {"action": "manage_schedule", "source_id": source.id}
            await show_schedule_menu(event, source)

    async def show_schedule_menu(event, source):
        interval = source.scan_interval or 60
        text = f"⏰ **Scan Schedule for {source.name or source.identifier}:**\n\n"
        text += f"Current scan interval: **{interval} seconds** ({interval//60} min {interval%60} sec)\n\n"
        text += "You can change how often this source is scanned for new messages.\n\n"
        keyboard = [
            [Button.inline("✏️ Change Interval", f"change_schedule_{source.id}")],
            [Button.inline("🔙 Back to Sources", "menu_sources")]
        ]
        await safe_edit_event_message(event, text, buttons=keyboard)

    @client.on(events.CallbackQuery(pattern=r"change_schedule_\d+"))
    async def change_schedule_callback(event):
        user_id = event.sender_id
        source_id = int(event.data.decode().split("_")[-1])
        user_states[user_id] = {"action": "awaiting_schedule_input", "source_id": source_id}
        await safe_edit_event_message(event, "⏰ **Send the new scan interval in seconds (10-86400):**", buttons=[[Button.inline("🔙 Cancel", f"schedule_src_{source_id}")]])

    @client.on(events.NewMessage(pattern=r'^(?!/).+'))
    async def handle_schedule_input(event: Message):
        user_id = event.sender_id
        state = user_states.get(user_id)
        if not state or state.get("action") != "awaiting_schedule_input":
            return
        interval_text = (event.text or "").strip()
        try:
            interval = int(interval_text)
            if interval < 10 or interval > 86400:
                raise ValueError
        except Exception:
            await event.reply("❌ Invalid interval. Please enter a number between 10 and 86400.")
            return
        source_id = state["source_id"]
        with db_session() as db:
            source = db.query(MonitoredSource).get(source_id)
            if not source:
                await event.reply("❌ Source not found.")
                return
            source.scan_interval = interval
            db.commit()
        del user_states[user_id]
        await show_schedule_menu(event, source)

    # AI Menu
    @client.on(events.CallbackQuery(data="ai_toggle"))
    async def ai_toggle_callback(event):
        user_id = event.sender_id
        with db_session() as db:
            sources = db.query(MonitoredSource).filter(MonitoredSource.is_active == True).all()
            if not sources:
                await safe_edit_event_message(event, "❌ No sources found. Add a source first.", buttons=[[Button.inline("🔙 Back to AI Menu", "menu_ai")]])
                return
            if len(sources) == 1:
                source = sources[0]
                user_states[user_id] = {"action": "manage_ai", "source_id": source.id}
                await show_ai_menu(event, source)
                return
            # Multiple sources: let user pick
            keyboard = [[Button.inline(f"{s.name or s.identifier}", f"ai_src_{s.id}")] for s in sources]
            keyboard.append([Button.inline("🔙 Back to AI Menu", "menu_ai")])
            await safe_edit_event_message(event, "🤖 **Select a source to manage AI features:**", buttons=keyboard)

    @client.on(events.CallbackQuery(pattern=r"ai_src_\d+"))
    async def ai_source_select_callback(event):
        user_id = event.sender_id
        source_id = int(event.data.decode().split("_")[-1])
        with db_session() as db:
            source = db.query(MonitoredSource).get(source_id)
            if not source:
                await safe_edit_event_message(event, "❌ Source not found.", buttons=[[Button.inline("🔙 Back", "ai_toggle")]])
                return
            user_states[user_id] = {"action": "manage_ai", "source_id": source.id}
            await show_ai_menu(event, source)

    async def show_ai_menu(event, source):
        text = f"🤖 **AI Features for {source.name or source.identifier}:**\n\n"
        text += f"• Sentiment Analysis: {'✅ ON' if source.sentiment_analysis else '❌ OFF'}\n"
        text += f"• Pattern Learning: {'✅ ON' if source.pattern_learning else '❌ OFF'}\n"
        text += f"• Smart Filtering: {'✅ ON' if source.smart_filtering else '❌ OFF'}\n\n"
        text += "Toggle features below.\n\n"
        keyboard = [
            [Button.inline(f"{'✅' if source.sentiment_analysis else '❌'} Sentiment Analysis", f"toggle_ai_{source.id}_sentiment")],
            [Button.inline(f"{'✅' if source.pattern_learning else '❌'} Pattern Learning", f"toggle_ai_{source.id}_pattern")],
            [Button.inline(f"{'✅' if source.smart_filtering else '❌'} Smart Filtering", f"toggle_ai_{source.id}_smart")],
            [Button.inline("🔙 Back to AI Menu", "menu_ai")]
        ]
        await safe_edit_event_message(event, text, buttons=keyboard)

    @client.on(events.CallbackQuery(pattern=r"toggle_ai_\d+_(sentiment|pattern|smart)"))
    async def toggle_ai_feature_callback(event):
        user_id = event.sender_id
        parts = event.data.decode().split("_")
        source_id = int(parts[2])
        feature = parts[3]
        with db_session() as db:
            source = db.query(MonitoredSource).get(source_id)
            if not source:
                await safe_edit_event_message(event, "❌ Source not found.", buttons=[[Button.inline("🔙 Back", f"ai_src_{source_id}")]])
                return
            if feature == "sentiment":
                source.sentiment_analysis = not source.sentiment_analysis
            elif feature == "pattern":
                source.pattern_learning = not source.pattern_learning
            elif feature == "smart":
                source.smart_filtering = not source.smart_filtering
            db.commit()
        await show_ai_menu(event, source)

    @client.on(events.CallbackQuery(data="ai_settings"))
    async def ai_settings_callback(event):
        await safe_edit_event_message(event, "📋 **AI Settings:**\n\nAI features can be toggled per source. Use the 'Toggle Features' menu to enable or disable Sentiment Analysis, Pattern Learning, and Smart Filtering for each source.\n\nFor advanced configuration, contact support.", buttons=[[Button.inline("🔙 Back to AI Menu", "menu_ai")]])

    @client.on(events.CallbackQuery(data="ai_stats"))
    async def ai_stats_callback(event):
        # Show AI stats (use text_analyzer if available)
        stats = None
        try:
            stats = text_analyzer.get_stats()
        except Exception:
            stats = None
        text = "📊 **AI Stats:**\n\n"
        if stats:
            for k, v in stats.items():
                text += f"• {k}: {v}\n"
        else:
            text += "No stats available.\n"
        await safe_edit_event_message(event, text, buttons=[[Button.inline("🔙 Back to AI Menu", "menu_ai")]])

    @client.on(events.CallbackQuery(data="ai_help"))
    async def ai_help_callback(event):
        text = "❓ **AI Help:**\n\n"
        text += "• **Sentiment Analysis:** Uses AI to detect positive/negative/neutral sentiment in messages.\n"
        text += "• **Pattern Learning:** Learns from message patterns to improve detection.\n"
        text += "• **Smart Filtering:** Uses AI to filter spam and irrelevant messages.\n\n"
        text += "Toggle these features in the AI menu for each source.\n"
        await safe_edit_event_message(event, text, buttons=[[Button.inline("🔙 Back to AI Menu", "menu_ai")]])

    # Settings
    @client.on(events.CallbackQuery(data="settings_general"))
    async def settings_general_callback(event):
        user_id = event.sender_id
        with db_session() as db:
            sources = db.query(MonitoredSource).filter(MonitoredSource.is_active == True).all()
            if not sources:
                await safe_edit_event_message(event, "❌ No sources found. Add a source first.", buttons=[[Button.inline("🔙 Back to Settings", "menu_settings")]])
                return
            if len(sources) == 1:
                source = sources[0]
                user_states[user_id] = {"action": "manage_settings", "source_id": source.id}
                await show_settings_menu(event, source)
                return
            keyboard = [[Button.inline(f"{s.name or s.identifier}", f"settings_src_{s.id}")] for s in sources]
            keyboard.append([Button.inline("🔙 Back to Settings", "menu_settings")])
            await safe_edit_event_message(event, "⚙️ **Select a source to manage settings:**", buttons=keyboard)

    @client.on(events.CallbackQuery(pattern=r"settings_src_\d+"))
    async def settings_source_select_callback(event):
        user_id = event.sender_id
        source_id = int(event.data.decode().split("_")[-1])
        with db_session() as db:
            source = db.query(MonitoredSource).get(source_id)
            if not source:
                await safe_edit_event_message(event, "❌ Source not found.", buttons=[[Button.inline("🔙 Back", "settings_general")]])
                return
            user_states[user_id] = {"action": "manage_settings", "source_id": source.id}
            await show_settings_menu(event, source)

    async def show_settings_menu(event, source):
        text = f"⚙️ **Settings for {source.name or source.identifier}:**\n\n"
        text += f"• Notifications: {'✅ ON' if source.notification_channels else '❌ OFF'}\n"
        text += f"• Rate Limit: {source.rate_limit or 'Unlimited'} alerts/hour\n"
        text += f"• Privacy: {'🔒 Strict' if source.meta_data and source.meta_data.get('privacy') == 'strict' else '🔓 Standard'}\n\n"
        keyboard = [
            [Button.inline("🔔 Toggle Notifications", f"toggle_notify_{source.id}")],
            [Button.inline("🚀 Set Rate Limit", f"set_rate_{source.id}")],
            [Button.inline("🔒 Toggle Privacy", f"toggle_privacy_{source.id}")],
            [Button.inline("🗄️ Data", f"settings_data_{source.id}")],
            [Button.inline("🧹 Cleanup", f"settings_cleanup_{source.id}")],
            [Button.inline("🔙 Back to Settings", "menu_settings")]
        ]
        await safe_edit_event_message(event, text, buttons=keyboard)

    @client.on(events.CallbackQuery(pattern=r"toggle_notify_\d+"))
    async def toggle_notify_callback(event):
        source_id = int(event.data.decode().split("_")[-1])
        with db_session() as db:
            source = db.query(MonitoredSource).get(source_id)
            if not source:
                await safe_edit_event_message(event, "❌ Source not found.", buttons=[[Button.inline("🔙 Back", f"settings_src_{source_id}")]])
                return
            if source.notification_channels:
                source.notification_channels = []
            else:
                source.notification_channels = [1]  # Dummy channel for ON (replace with real logic)
            db.commit()
        await show_settings_menu(event, source)

    @client.on(events.CallbackQuery(pattern=r"set_rate_\d+"))
    async def set_rate_callback(event):
        user_id = event.sender_id
        source_id = int(event.data.decode().split("_")[-1])
        user_states[user_id] = {"action": "awaiting_rate_input", "source_id": source_id}
        await safe_edit_event_message(event, "🚀 **Send the new rate limit (alerts per hour, 1-1000, or 0 for unlimited):**", buttons=[[Button.inline("🔙 Cancel", f"settings_src_{source_id}")]])

    @client.on(events.NewMessage(pattern=r'^(?!/).+'))
    async def handle_rate_input(event: Message):
        user_id = event.sender_id
        state = user_states.get(user_id)
        if not state or state.get("action") != "awaiting_rate_input":
            return
        rate_text = (event.text or "").strip()
        try:
            rate = int(rate_text)
            if rate < 0 or rate > 1000:
                raise ValueError
        except Exception:
            await event.reply("❌ Invalid rate. Please enter a number between 0 and 1000.")
            return
        source_id = state["source_id"]
        with db_session() as db:
            source = db.query(MonitoredSource).get(source_id)
            if not source:
                await event.reply("❌ Source not found.")
                return
            source.rate_limit = rate if rate > 0 else None
            db.commit()
        del user_states[user_id]
        await show_settings_menu(event, source)

    @client.on(events.CallbackQuery(pattern=r"toggle_privacy_\d+"))
    async def toggle_privacy_callback(event):
        source_id = int(event.data.decode().split("_")[-1])
        with db_session() as db:
            source = db.query(MonitoredSource).get(source_id)
            if not source:
                await safe_edit_event_message(event, "❌ Source not found.", buttons=[[Button.inline("🔙 Back", f"settings_src_{source_id}")]])
                return
            meta = source.meta_data or {}
            if meta.get('privacy') == 'strict':
                meta['privacy'] = 'standard'
            else:
                meta['privacy'] = 'strict'
            source.meta_data = meta
            db.commit()
        await show_settings_menu(event, source)

    @client.on(events.CallbackQuery(pattern=r"settings_data_\d+"))
    async def settings_data_callback(event):
        source_id = int(event.data.decode().split("_")[-1])
        with db_session() as db:
            source = db.query(MonitoredSource).get(source_id)
            if not source:
                await safe_edit_event_message(event, "❌ Source not found.", buttons=[[Button.inline("🔙 Back", f"settings_src_{source_id}")]])
                return
            text = f"🗄️ **Data for {source.name or source.identifier}:**\n\n"
            text += f"• Alerts sent: {getattr(source, 'alert_count', 0)}\n"
            text += f"• Mentions: {getattr(source, 'mention_count', 0)}\n"
            text += f"• Errors: {source.error_count}\n"
            await safe_edit_event_message(event, text, buttons=[[Button.inline("🔙 Back", f"settings_src_{source_id}")]])

    @client.on(events.CallbackQuery(pattern=r"settings_cleanup_\d+"))
    async def settings_cleanup_callback(event):
        source_id = int(event.data.decode().split("_")[-1])
        with db_session() as db:
            source = db.query(MonitoredSource).get(source_id)
            if not source:
                await safe_edit_event_message(event, "❌ Source not found.", buttons=[[Button.inline("🔙 Back", f"settings_src_{source_id}")]])
                return
            source.error_count = 0
            source.last_scanned_at = None
            db.commit()
            await safe_edit_event_message(event, f"🧹 **Cleanup complete for {source.name or source.identifier}.**", buttons=[[Button.inline("🔙 Back", f"settings_src_{source_id}")]])

    # Stats
    @client.on(events.CallbackQuery(data="stats_detail"))
    async def stats_detail_callback(event):
        stats = await get_stats()
        text = "📊 **Bot Statistics:**\n\n"
        text += f"• Active Sources: {stats.get('active_sources', 0)}\n"
        text += f"• Recent Updates: {stats.get('recent_updates', 0)}\n"
        text += f"• Error Rate: {stats.get('error_rate', 0):.2f}%\n"
        text += f"• Telegram Channels: {stats.get('telegram_channels', 0)}\n"
        text += f"• Discord Webhooks: {stats.get('discord_webhooks', 0)}\n"
        text += f"• Total Messages: {stats.get('total_messages', 0)}\n"
        await safe_edit_event_message(event, text, buttons=[[Button.inline("🔙 Back to Stats", "menu_stats")]])

    @client.on(events.CallbackQuery(data="stats_graphs"))
    async def stats_graphs_callback(event):
        # Simple text-based bar graph for active sources and errors
        stats = await get_stats()
        active = stats.get('active_sources', 0)
        errors = int(stats.get('error_rate', 0))
        bar = '█' * min(active, 20)
        err_bar = '█' * min(errors, 20)
        text = f"📈 **Stats Graphs:**\n\nActive Sources: {bar} ({active})\nErrors: {err_bar} ({errors})\n"
        await safe_edit_event_message(event, text, buttons=[[Button.inline("🔙 Back to Stats", "menu_stats")]])

    @client.on(events.CallbackQuery(data="stats_history"))
    async def stats_history_callback(event):
        # Show last 10 events from logs (if available)
        try:
            with open('logs/bot.log', 'r') as f:
                lines = f.readlines()[-10:]
        except Exception:
            lines = ["No history available."]
        text = "📜 **Recent Bot Events:**\n\n" + "".join(lines)
        await safe_edit_event_message(event, text, buttons=[[Button.inline("🔙 Back to Stats", "menu_stats")]])

    @client.on(events.CallbackQuery(data="stats_errors"))
    async def stats_errors_callback(event):
        # Show last 10 errors from logs (if available)
        try:
            with open('logs/bot.log', 'r') as f:
                errors = [l for l in f if 'ERROR' in l][-10:]
        except Exception:
            errors = ["No error logs available."]
        text = "❌ **Recent Errors:**\n\n" + "".join(errors)
        await safe_edit_event_message(event, text, buttons=[[Button.inline("🔙 Back to Stats", "menu_stats")]])

    @client.on(events.CallbackQuery(data="stats_refresh"))
    async def stats_refresh_callback(event):
        # Just re-call the stats_detail handler
        await stats_detail_callback(event)

    @client.on(events.CallbackQuery(data="stats_dash"))
    async def stats_dash_callback(event):
        text = "🌐 **Dashboard:**\n\nAccess the live dashboard at:\nhttps://mr-hux-alpha-bot.onrender.com\n\nFeatures:\n• Real-time monitoring\n• Source management\n• Statistics and graphs\n• Settings configuration\n"
        await safe_edit_event_message(event, text, buttons=[[Button.inline("🔙 Back to Stats", "menu_stats")]])

    # Help
    @client.on(events.CallbackQuery(data="help_guide"))
    async def help_guide_callback(event):
        text = "📖 **User Guide:**\n\nWelcome to MR HUX Alpha Bot!\n\n- Use the main menu to access all features.\n- Add sources to monitor Telegram, Discord, Reddit, X/Twitter, and more.\n- Set up filters, schedules, and alerts.\n- Configure output channels for notifications.\n- Use the dashboard for advanced analytics.\n\nFor a full guide, visit: https://mr-hux-alpha-bot.onrender.com/docs\n"
        await safe_edit_event_message(event, text, buttons=[[Button.inline("🔙 Back to Help", "menu_help")]])

    @client.on(events.CallbackQuery(data="help_faq"))
    async def help_faq_callback(event):
        text = "❓ **FAQ:**\n\nQ: How do I add a new source?\nA: Use the 'HUNT SOURCES' button and follow the prompts.\n\nQ: How do I get alerts?\nA: Add an output channel in 'ALERT CHANNELS'.\n\nQ: How do I use filters?\nA: Go to 'Filters' in the source menu to add keywords or regex.\n\nQ: Where is the dashboard?\nA: https://mr-hux-alpha-bot.onrender.com\n"
        await safe_edit_event_message(event, text, buttons=[[Button.inline("🔙 Back to Help", "menu_help")]])

    @client.on(events.CallbackQuery(data="help_tutorial"))
    async def help_tutorial_callback(event):
        text = "🎓 **Tutorial:**\n\n1. Click /start to open the main menu.\n2. Add a source to monitor.\n3. Set up filters and schedules.\n4. Add an output channel.\n5. Watch for alerts and check the dashboard.\n\nFor a video tutorial, visit: https://mr-hux-alpha-bot.onrender.com/tutorial\n"
        await safe_edit_event_message(event, text, buttons=[[Button.inline("🔙 Back to Help", "menu_help")]])

    @client.on(events.CallbackQuery(data="help_trouble"))
    async def help_trouble_callback(event):
        text = "🔧 **Troubleshooting:**\n\n- Not receiving alerts? Check your output channels and filters.\n- Errors in dashboard? Try refreshing or contact support.\n- Still stuck? Use the Support button below.\n"
        await safe_edit_event_message(event, text, buttons=[[Button.inline("🔙 Back to Help", "menu_help")]])

    @client.on(events.CallbackQuery(data="help_support"))
    async def help_support_callback(event):
        text = "💬 **Support:**\n\nFor help, join our Telegram community:\nhttps://t.me/MrHuxCommunity\n\nOr email: support@mrhuxbot.com\n"
        await safe_edit_event_message(event, text, buttons=[[Button.inline("🔙 Back to Help", "menu_help")]])

    @client.on(events.CallbackQuery(data="help_updates"))
    async def help_updates_callback(event):
        try:
            with open('CHANGELOG.md', 'r') as f:
                changelog = ''.join(f.readlines()[-10:])
        except Exception:
            changelog = "No recent updates found."
        text = f"📰 **Latest Updates:**\n\n{changelog}\n"
        await safe_edit_event_message(event, text, buttons=[[Button.inline("🔙 Back to Help", "menu_help")]])

    # Output management - Email output
    @client.on(events.CallbackQuery(data="add_email_output"))
    async def add_email_output_callback(event):
        user_id = event.sender_id
        user_states[user_id] = {"action": "awaiting_email_output"}
        await safe_edit_event_message(event, "📧 **Send the email address to receive alerts:**", buttons=[[Button.inline("🔙 Cancel", "output_add")]])

    @client.on(events.NewMessage(pattern=r'^(?!/).+'))
    async def handle_email_output_input(event: Message):
        user_id = event.sender_id
        state = user_states.get(user_id)
        if not state or state.get("action") != "awaiting_email_output":
            return
        email = (event.text or "").strip()
        import re
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            await event.reply("❌ Invalid email address. Please try again.")
            return
        from src.models.monitored_source import OutputChannel, OutputType
        from src.utils.db import db_session
        with db_session() as db:
            exists = db.query(OutputChannel).filter(OutputChannel.identifier == email, OutputChannel.type == OutputType.WEBHOOK).first()
            if exists:
                await event.reply("⚠️ This email is already registered as an output.")
            else:
                output = OutputChannel(type=OutputType.WEBHOOK, identifier=email, name=email, is_active=True)
                db.add(output)
                db.commit()
                await event.reply(f"✅ Email output added: {email}")
        del user_states[user_id]

    @client.on(events.NewMessage(pattern='/whereami'))
    async def whereami_command(event: Message):
        """Reply with bot status, DB path, number of sources, and outputs."""
        from src.database import SessionLocal
        import os
        db = SessionLocal()
        db_path = os.environ.get('DATABASE_URL') or getattr(db.bind, 'url', None)
        from src.models.monitored_source import MonitoredSource
        from src.models.output_channel import OutputChannel
        sources = db.query(MonitoredSource).all()
        outputs = db.query(OutputChannel).all()
        text = (
            f"🤖 <b>MR HUX Alpha Bot Status</b> 🤖\n"
            f"<b>DB:</b> {db_path}\n"
            f"<b>Sources:</b> {len(sources)}\n"
            f"<b>Outputs:</b> {len(outputs)}\n"
            f"<b>Active:</b> {sum(1 for s in sources if bool(s.is_active))} sources, {sum(1 for o in outputs if bool(o.is_active))} outputs\n"
        )
        await event.reply(text, parse_mode='html')
        db.close()

    @client.on(events.NewMessage(pattern='/sources'))
    async def sources_command(event: Message):
        """Reply with a list of all monitored sources."""
        from src.database import SessionLocal
        db = SessionLocal()
        summary = await get_sources_summary(db)
        await event.reply(f"<b>Monitored Sources:</b>\n{summary}", parse_mode='html')
        db.close()

    @client.on(events.NewMessage(pattern='/scanners'))
    async def scanners_command(event: Message):
        """Reply with the status of all background scanners."""
        token_monitor = TokenMonitor()
        status = await token_monitor.get_system_status()
        text = (
            f"<b>Background Scanners Status</b>\n"
            f"Pump.fun: {status['api_status'].get('pumpfun', 'unknown')}\n"
            f"Dexscreener: {status['api_status'].get('dexscreener', 'unknown')}\n"
            f"Birdeye: {status['api_status'].get('birdeye', 'unknown')}\n"
            f"Bonkfun: {status['api_status'].get('bonkfun', 'unknown')}\n"
            f"Rugcheck: {status['api_status'].get('rugcheck', 'unknown')}\n"
            f"Telegram: running\n"
            f"Uptime: {status.get('uptime_hours', 0):.2f} hours\n"
            f"Messages Processed: {status.get('messages_processed', 0)}\n"
            f"Errors (last hour): {status.get('errors_last_hour', 0)}\n"
        )
        await event.reply(text, parse_mode='html')

    @client.on(events.NewMessage(pattern='/status'))
    async def status_command(event: Message):
        """Reply with overall bot health and stats."""
        token_monitor = TokenMonitor()
        status = await token_monitor.get_system_status()
        text = (
            f"<b>MR HUX Alpha Bot Status</b>\n"
            f"Running: {status.get('is_running', False)}\n"
            f"Uptime: {status.get('uptime_hours', 0):.2f} hours\n"
            f"Messages Processed: {status.get('messages_processed', 0)}\n"
            f"Errors (last hour): {status.get('errors_last_hour', 0)}\n"
            f"API Health: {status.get('api_status', {})}\n"
            f"Memory Usage: {status.get('memory_usage_mb', 0):.2f} MB\n"
        )
        await event.reply(text, parse_mode='html')
