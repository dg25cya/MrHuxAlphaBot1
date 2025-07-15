"""Source monitoring command handlers."""
from datetime import datetime
import re

from loguru import logger
from telethon import events, TelegramClient
from telethon.tl.custom import Message

from src.models.monitored_source import MonitoredSource, SourceType
from src.utils.db import db_session

# Command patterns
MONITOR_PATTERNS = {
    'telegram': r'/monitor_tg (\-?\d+)',
    'discord': r'/monitor_discord ([A-Za-z0-9]+)',
    'x': r'/monitor_x (@[A-Za-z0-9_]+)'
}

UNMONITOR_PATTERNS = {
    'telegram': r'/unmonitor_tg (\-?\d+)',
    'discord': r'/unmonitor_discord ([A-Za-z0-9]+)',
    'x': r'/unmonitor_x (@[A-Za-z0-9_]+)'
}

async def setup_source_commands(client: TelegramClient):
    """Setup commands for managing monitored sources."""
    
    @client.on(events.NewMessage(pattern='/sources'))
    async def sources_command(event: Message):
        """Handle /sources command to list all monitored sources."""
        try:
            with db_session() as db:
                sources = db.query(MonitoredSource).all()
                
                if not sources:
                    await event.reply("No monitored sources")
                    return
                
                response = "📡 Monitored Sources:\n\n"
                
                for source in sources:
                    status = "✅" if source.is_active else "❌"
                    response += (
                        f"{status} {source.source_type.upper()}: {source.name}\n"
                        f"ID: {source.source_id}\n"
                        f"Added: {source.added_at.strftime('%Y-%m-%d')}\n\n"
                    )
                    
                await event.reply(response)
                
        except Exception as e:
            logger.exception(f"Error in sources command: {e}")
            await event.reply("Error processing command")

    # Telegram Groups
    @client.on(events.NewMessage(pattern=MONITOR_PATTERNS['telegram']))
    async def monitor_telegram_command(event: Message):
        """Handle /monitor_tg command."""
        try:
            group_id = int(event.pattern_match.group(1))
            
            with db_session() as db:
                # Check if already monitoring
                existing = db.query(MonitoredSource).filter(
                    MonitoredSource.source_type == SourceType.TELEGRAM,
                    MonitoredSource.source_id == str(group_id)
                ).first()
                
                if existing:
                    await event.reply(f"Already monitoring Telegram group {group_id}")
                    return
                
                # Add new source
                source = MonitoredSource(
                    source_type=SourceType.TELEGRAM,
                    source_id=str(group_id),
                    name=f"Telegram Group {group_id}",
                    added_at=datetime.utcnow()
                )
                db.add(source)
                db.commit()
                
            await event.reply(f"Started monitoring Telegram group {group_id}")
            
        except ValueError:
            await event.reply("Invalid group ID format")
        except Exception as e:
            logger.exception(f"Error in monitor_telegram command: {e}")
            await event.reply("Error processing command")

    # Discord Servers
    @client.on(events.NewMessage(pattern=MONITOR_PATTERNS['discord']))
    async def monitor_discord_command(event: Message):
        """Handle /monitor_discord command."""
        try:
            server_id = event.pattern_match.group(1)
            
            with db_session() as db:
                existing = db.query(MonitoredSource).filter(
                    MonitoredSource.source_type == SourceType.DISCORD,
                    MonitoredSource.source_id == server_id
                ).first()
                
                if existing:
                    await event.reply(f"Already monitoring Discord server {server_id}")
                    return
                
                source = MonitoredSource(
                    source_type=SourceType.DISCORD,
                    source_id=server_id,
                    name=f"Discord Server {server_id}",
                    added_at=datetime.utcnow()
                )
                db.add(source)
                db.commit()
                
            await event.reply(f"Started monitoring Discord server {server_id}")
            
        except Exception as e:
            logger.exception(f"Error in monitor_discord command: {e}")
            await event.reply("Error processing command")

    # X Profiles
    @client.on(events.NewMessage(pattern=MONITOR_PATTERNS['x']))
    async def monitor_x_command(event: Message):
        """Handle /monitor_x command."""
        try:
            handle = event.pattern_match.group(1)  # Includes @ symbol
            
            with db_session() as db:
                existing = db.query(MonitoredSource).filter(
                    MonitoredSource.source_type == SourceType.X,
                    MonitoredSource.source_id == handle
                ).first()
                
                if existing:
                    await event.reply(f"Already monitoring X profile {handle}")
                    return
                
                source = MonitoredSource(
                    source_type=SourceType.X,
                    source_id=handle,
                    name=f"X Profile {handle}",
                    added_at=datetime.utcnow()
                )
                db.add(source)
                db.commit()
                
            await event.reply(f"Started monitoring X profile {handle}")
            
        except Exception as e:
            logger.exception(f"Error in monitor_x command: {e}")
            await event.reply("Error processing command")

    # Unmonitor commands
    @client.on(events.NewMessage(pattern=UNMONITOR_PATTERNS['telegram']))
    async def unmonitor_telegram_command(event: Message):
        """Handle /unmonitor_tg command."""
        try:
            group_id = int(event.pattern_match.group(1))
            
            with db_session() as db:
                source = db.query(MonitoredSource).filter(
                    MonitoredSource.source_type == SourceType.TELEGRAM,
                    MonitoredSource.source_id == str(group_id)
                ).first()
                
                if not source:
                    await event.reply(f"Not monitoring Telegram group {group_id}")
                    return
                    
                db.delete(source)
                db.commit()
                
            await event.reply(f"Stopped monitoring Telegram group {group_id}")
            
        except ValueError:
            await event.reply("Invalid group ID format")
        except Exception as e:
            logger.exception(f"Error in unmonitor_telegram command: {e}")
            await event.reply("Error processing command")

    @client.on(events.NewMessage(pattern=UNMONITOR_PATTERNS['discord']))
    async def unmonitor_discord_command(event: Message):
        """Handle /unmonitor_discord command."""
        try:
            server_id = event.pattern_match.group(1)
            
            with db_session() as db:
                source = db.query(MonitoredSource).filter(
                    MonitoredSource.source_type == SourceType.DISCORD,
                    MonitoredSource.source_id == server_id
                ).first()
                
                if not source:
                    await event.reply(f"Not monitoring Discord server {server_id}")
                    return
                    
                db.delete(source)
                db.commit()
                
            await event.reply(f"Stopped monitoring Discord server {server_id}")
            
        except Exception as e:
            logger.exception(f"Error in unmonitor_discord command: {e}")
            await event.reply("Error processing command")

    @client.on(events.NewMessage(pattern=UNMONITOR_PATTERNS['x']))
    async def unmonitor_x_command(event: Message):
        """Handle /unmonitor_x command."""
        try:
            handle = event.pattern_match.group(1)
            
            with db_session() as db:
                source = db.query(MonitoredSource).filter(
                    MonitoredSource.source_type == SourceType.X,
                    MonitoredSource.source_id == handle
                ).first()
                
                if not source:
                    await event.reply(f"Not monitoring X profile {handle}")
                    return
                    
                db.delete(source)
                db.commit()
                
            await event.reply(f"Stopped monitoring X profile {handle}")
            
        except Exception as e:
            logger.exception(f"Error in unmonitor_x command: {e}")
            await event.reply("Error processing command")

    logger.info("Source command handlers setup complete")
