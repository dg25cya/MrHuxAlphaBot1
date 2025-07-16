"""Source monitoring handlers."""
from datetime import datetime
import feedparser
import praw
from github import Github
from telethon import TelegramClient
import discord
from discord.ext import commands
from loguru import logger
import aiohttp

from src.models.monitored_source import MonitoredSource, SourceType
from src.utils.db import db_session
from src.config.settings import get_settings

settings = get_settings()

class SourceManager:
    """Manager for handling different source types."""
    
    def __init__(self) -> None:
        """Initialize source manager."""
        # Initialize Reddit client (if credentials available)
        try:
            if hasattr(settings, 'reddit_client_id') and hasattr(settings, 'reddit_client_secret'):
                if settings.reddit_client_id and settings.reddit_client_secret:
                    self.reddit = praw.Reddit(
                        client_id=settings.reddit_client_id,
                        client_secret=settings.reddit_client_secret,
                        user_agent=getattr(settings, 'reddit_user_agent', None) or "MR_HUX_Alpha_Bot/1.0"
                    )
                else:
                    self.reddit = None
                    logger.warning("Reddit credentials not configured - Reddit monitoring disabled")
            else:
                self.reddit = None
                logger.warning("Reddit settings not found - Reddit monitoring disabled")
        except Exception as e:
            self.reddit = None
            logger.warning(f"Failed to initialize Reddit client: {e}")
        
        # Initialize GitHub client (if token available)
        try:
            if hasattr(settings, 'github_token') and settings.github_token:
                self.github = Github(settings.github_token)
            else:
                self.github = None
                logger.warning("GitHub token not configured - GitHub monitoring disabled")
        except Exception as e:
            self.github = None
            logger.warning(f"Failed to initialize GitHub client: {e}")
        
        # Initialize Discord bot (if token available)
        try:
            if hasattr(settings, 'discord_token') and settings.discord_token:
                intents = discord.Intents.default()
                intents.message_content = True
                self.discord_bot = commands.Bot(command_prefix="!", intents=intents)
            else:
                self.discord_bot = None
                logger.warning("Discord token not configured - Discord monitoring disabled")
        except Exception as e:
            self.discord_bot = None
            logger.warning(f"Failed to initialize Discord client: {e}")

        # Initialize aiohttp session for API calls
        self.session = None
        
    async def __aenter__(self):
        """Context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.session:
            await self.session.close()
            
    async def scan_source(
        self,
        source: MonitoredSource,
        telegram_client: TelegramClient = None
    ) -> list:
        """Scan a source for new content."""
        try:
            if source.type == SourceType.TELEGRAM:
                return await self._scan_telegram(source, telegram_client)
            elif source.type == SourceType.DISCORD:
                return await self._scan_discord(source)
            elif source.type == SourceType.REDDIT:
                return await self._scan_reddit(source)
            elif source.type == SourceType.RSS:
                return await self._scan_rss(source)
            elif source.type == SourceType.GITHUB:
                return await self._scan_github(source)
            elif source.type == SourceType.TWITTER:
                return await self._scan_twitter(source)
            elif source.type == SourceType.BONK:
                return await self._scan_bonk(source)
            elif source.type == SourceType.DEX:
                return await self._scan_dex(source)
            else:
                logger.warning(f"Unknown source type: {source.type}")
                return []
                
        except Exception as e:
            logger.exception(f"Error scanning source {source.id}: {e}")
            self._update_source_error(source, str(e))
            return []

    async def scan_all_sources(self, telegram_client=None, output_service=None):
        """Scan all active sources and send detected plays to output service."""
        from src.models.monitored_source import MonitoredSource
        from src.utils.db import db_session
        plays_found = []
        with db_session() as db:
            sources = db.query(MonitoredSource).filter(MonitoredSource.is_active == True).all()
            for source in sources:
                try:
                    results = await self.scan_source(source, telegram_client)
                    for play in results:
                        plays_found.append(play)
                        if output_service:
                            await output_service.send_alert(play)
                except Exception as e:
                    logger.error(f"Error scanning source {source.id}: {e}")
        return plays_found

    async def _scan_telegram(
        self,
        source: MonitoredSource,
        client: TelegramClient
    ) -> list:
        """Scan Telegram channel/group."""
        if not client:
            logger.error("No Telegram client provided")
            return []
            
        try:
            messages = []
            
            # Handle different identifier formats
            entity_id = source.identifier
            
            # If it's a username (starts with @), remove the @
            if entity_id.startswith('@'):
                entity_id = entity_id[1:]
            
            # Try to get the entity
            try:
                entity = await client.get_entity(entity_id)
            except Exception as e:
                logger.error(f"Could not get entity for {entity_id}: {e}")
                return []
            
            async for message in client.iter_messages(
                entity,
                limit=50,
                offset_date=source.last_scanned
            ):
                if not message.text:
                    continue
                    
                # Generate proper URL
                if hasattr(entity, 'username') and entity.username:
                    url = f"https://t.me/{entity.username}/{message.id}"
                else:
                    url = f"https://t.me/c/{str(entity.id)[4:]}/{message.id}" if str(entity.id).startswith('-100') else f"https://t.me/c/{entity.id}/{message.id}"
                    
                messages.append({
                    "text": message.text,
                    "timestamp": message.date,
                    "url": url,
                    "attachments": []
                })
                
            self._update_source_success(source)
            return messages
            
        except Exception as e:
            logger.exception(f"Telegram scan error for {source.identifier}: {e}")
            self._update_source_error(source, str(e))
            return []
            
    async def _scan_discord(self, source: MonitoredSource) -> list:
        """Scan Discord server/channel."""
        try:
            messages = []
            
            async with discord.Client() as client:
                channel = await client.fetch_channel(int(source.source_id))
                async for message in channel.history(
                    limit=50,
                    after=source.last_scanned
                ):
                    if not message.content:
                        continue
                        
                    attachments = [a.url for a in message.attachments]
                    messages.append({
                        "text": message.content,
                        "timestamp": message.created_at,
                        "url": message.jump_url,
                        "attachments": attachments
                    })
                    
            self._update_source_success(source)
            return messages
            
        except Exception as e:
            logger.exception(f"Discord scan error for {source.source_id}: {e}")
            self._update_source_error(source, str(e))
            return []
            
    async def _scan_reddit(self, source: MonitoredSource) -> list:
        """Scan Reddit subreddit."""
        if not self.reddit:
            logger.warning("Reddit client not initialized - skipping Reddit scan")
            return []
            
        try:
            messages = []
            subreddit = self.reddit.subreddit(source.source_id)
            
            for post in subreddit.new(limit=50):
                if source.last_scanned and post.created_utc <= source.last_scanned.timestamp():
                    continue
                    
                messages.append({
                    "text": f"{post.title}\n\n{post.selftext}",
                    "timestamp": datetime.fromtimestamp(post.created_utc),
                    "url": f"https://reddit.com{post.permalink}",
                    "attachments": [post.url] if post.url.endswith(('.jpg', '.png', '.gif')) else []
                })
                
            self._update_source_success(source)
            return messages
            
        except Exception as e:
            logger.exception(f"Reddit scan error for {source.source_id}: {e}")
            self._update_source_error(source, str(e))
            return []
            
    async def _scan_rss(self, source: MonitoredSource) -> list:
        """Scan RSS feed."""
        try:
            messages = []
            feed = feedparser.parse(source.source_id)
            
            for entry in feed.entries[:50]:
                timestamp = datetime(*entry.published_parsed[:6])
                if source.last_scanned and timestamp <= source.last_scanned:
                    continue
                    
                messages.append({
                    "text": f"{entry.title}\n\n{entry.description}",
                    "timestamp": timestamp,
                    "url": entry.link,
                    "attachments": []
                })
                
            self._update_source_success(source)
            return messages
            
        except Exception as e:
            logger.exception(f"RSS scan error for {source.source_id}: {e}")
            self._update_source_error(source, str(e))
            return []
            
    async def _scan_github(self, source: MonitoredSource) -> list:
        """Scan GitHub repository."""
        if not self.github:
            logger.warning("GitHub client not initialized - skipping GitHub scan")
            return []
            
        try:
            messages = []
            owner, repo = source.source_id.split('/')
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            # Get recent commits
            for commit in repository.get_commits()[:50]:
                if source.last_scanned and commit.commit.author.date <= source.last_scanned:
                    continue
                    
                messages.append({
                    "text": f"New commit: {commit.commit.message}",
                    "timestamp": commit.commit.author.date,
                    "url": commit.html_url,
                    "attachments": []
                })
                
            # Get recent issues
            for issue in repository.get_issues(state='all')[:20]:
                if source.last_scanned and issue.created_at <= source.last_scanned:
                    continue
                    
                messages.append({
                    "text": f"New issue: {issue.title}\n\n{issue.body}",
                    "timestamp": issue.created_at,
                    "url": issue.html_url,
                    "attachments": []
                })
                
            self._update_source_success(source)
            return messages
            
        except Exception as e:
            logger.exception(f"GitHub scan error for {source.source_id}: {e}")
            self._update_source_error(source, str(e))
            return []
            
    async def _scan_twitter(self, source: MonitoredSource) -> list:
        """Scan X/Twitter profile using web scraping (no API required)."""
        try:
            messages = []
            username = source.source_id.strip('@')
            
            # Use nitter.net as an alternative Twitter frontend
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://nitter.net/{username}/rss") as response:
                    if response.status == 200:
                        text = await response.text()
                        feed = feedparser.parse(text)
                        
                        for entry in feed.entries[:50]:
                            timestamp = datetime(*entry.published_parsed[:6])
                            if source.last_scanned and timestamp <= source.last_scanned:
                                continue
                                
                            messages.append({
                                "text": entry.title,
                                "timestamp": timestamp,
                                "url": entry.link.replace("nitter.net", "twitter.com"),
                                "attachments": []
                            })
                            
            self._update_source_success(source)
            return messages
            
        except Exception as e:
            logger.exception(f"Twitter scan error for {source.source_id}: {e}")
            self._update_source_error(source, str(e))
            return []
            
    async def _scan_bonk(self, source: MonitoredSource) -> list:
        """Scan Bonk chain for activities and contract updates."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            messages = []
            headers = {"Authorization": f"Bearer {settings.bonkfun_api_key}"}
            
            # Monitor contract interactions with enhanced filtering
            contract_url = f"https://api.bonkfun.io/v1/contracts/activities"
            async with self.session.get(contract_url, headers=headers) as response:
                if response.status == 200:
                    activities = await response.json()
                    for activity in activities['data']:
                        if source.last_scanned and datetime.fromisoformat(activity['timestamp']) <= source.last_scanned:
                            continue
                            
                        # Enhanced filtering for relevant activities
                        if self._is_relevant_activity(activity):
                            msg = {
                                "text": self._format_bonk_activity(activity),
                                "timestamp": datetime.fromisoformat(activity['timestamp']),
                                "url": f"https://explorer.bonkfun.io/tx/{activity['txHash']}",
                                "attachments": []
                            }
                            messages.append(msg)
                            
            # Monitor new deployments with improved validation
            deploy_url = f"https://api.bonkfun.io/v1/contracts/deployments"
            async with self.session.get(deploy_url, headers=headers) as response:
                if response.status == 200:
                    deployments = await response.json()
                    for deployment in deployments['data']:
                        if source.last_scanned and datetime.fromisoformat(deployment['timestamp']) <= source.last_scanned:
                            continue
                            
                        # Enhanced contract validation
                        if self._is_valid_deployment(deployment):
                            msg = {
                                "text": self._format_bonk_deployment(deployment),
                                "timestamp": datetime.fromisoformat(deployment['timestamp']),
                                "url": f"https://explorer.bonkfun.io/address/{deployment['contractAddress']}",
                                "attachments": []
                            }
                            messages.append(msg)
                            
            # Track Bonk token holders and whales
            whale_url = f"https://api.bonkfun.io/v1/holders"
            async with self.session.get(whale_url, headers=headers) as response:
                if response.status == 200:
                    holders = await response.json()
                    whale_movements = self._analyze_whale_movements(holders['data'])
                    messages.extend(whale_movements)
                    
            self._update_source_success(source)
            return messages
            
        except Exception as e:
            logger.exception(f"Bonk scan error: {e}")
            self._update_source_error(source, str(e))
            return []

    def _is_relevant_activity(self, activity: dict) -> bool:
        """Determine if a Bonk chain activity is relevant for monitoring."""
        # Skip low-value transactions
        if float(activity.get('value', 0)) < settings.min_bonk_value:
            return False
            
        # Focus on important activity types
        important_types = ['mint', 'burn', 'transfer', 'swap', 'stake']
        if activity.get('type', '').lower() not in important_types:
            return False
            
        return True
        
    def _is_valid_deployment(self, deployment: dict) -> bool:
        """Validate a new Bonk contract deployment."""
        # Check for minimum required fields
        if not all(k in deployment for k in ['contractAddress', 'name', 'contractType']):
            return False
            
        # Filter out known spam contract types
        spam_types = ['test', 'proxy', 'minimal']
        if deployment.get('contractType', '').lower() in spam_types:
            return False
            
        # Require verification for production contracts
        if deployment.get('environment') == 'production' and not deployment.get('verified'):
            return False
            
        return True
        
    def _analyze_whale_movements(self, holders_data: list) -> list:
        """Analyze whale wallet movements on Bonk chain."""
        messages = []
        
        for holder in holders_data:
            # Consider wallets with > 1M BONK as whales
            if float(holder.get('balance', 0)) > 1_000_000:
                timestamp = datetime.fromisoformat(holder['lastActivity'])
                
                msg = {
                    "text": f"🐋 Whale Activity Detected\n\n"
                           f"Wallet: {holder['address'][:8]}...{holder['address'][-6:]}\n"
                           f"Balance: {float(holder['balance']):,.0f} BONK\n"
                           f"Change: {holder.get('balanceChange', 'Unknown')}\n"
                           f"Type: {holder.get('activityType', 'Unknown')}",
                    "timestamp": timestamp,
                    "url": f"https://explorer.bonkfun.io/address/{holder['address']}",
                    "attachments": []
                }
                messages.append(msg)
                
        return messages

    def _format_bonk_activity(self, activity: dict) -> str:
        """Format Bonk chain activity for output with enhanced details."""
        activity_type = activity.get('type', 'Unknown')
        contract_name = activity.get('contractName', 'Unknown Contract')
        value = float(activity.get('value', 0))
        
        msg = f"🔥 New Bonk Activity\n\n"
        msg += f"Type: {activity_type}\n"
        msg += f"Contract: {contract_name}\n"
        msg += f"Value: {value:,.0f} BONK"
        
        # Add price impact if available
        if price_impact := activity.get('priceImpact'):
            msg += f"\nPrice Impact: {float(price_impact):.2f}%"
            
        # Add gas costs
        if gas := activity.get('gasCost'):
            msg += f"\nGas Cost: {float(gas):.4f} SOL"
            
        if activity.get('description'):
            msg += f"\n\nDetails: {activity['description']}"
            
        return msg

    def _format_bonk_deployment(self, deployment: dict) -> str:
        """Format Bonk contract deployment for output with enhanced validation."""
        verification_status = "✅ Verified" if deployment.get('verified') else "⚠️ Unverified"
        audit_status = "✅ Audited" if deployment.get('audited') else "⚠️ Not Audited"
        
        msg = f"🚀 New Bonk Contract Deployed\n\n"
        msg += f"Name: {deployment.get('name', 'Unknown')}\n"
        msg += f"Type: {deployment.get('contractType', 'Unknown')}\n"
        msg += f"Address: {deployment['contractAddress']}\n"
        msg += f"Status: {verification_status} | {audit_status}\n"
        
        if deployment.get('description'):
            msg += f"\nDescription: {deployment['description']}"
            
        if deployment.get('audit'):
            msg += f"\n🔒 Audit Report: {deployment['audit']['url']}"
            
        if deployment.get('social'):
            msg += "\n\nSocial Links:"
            for platform, url in deployment['social'].items():
                msg += f"\n{platform}: {url}"
                
        return msg

    def _update_source_success(self, source: MonitoredSource) -> None:
        """Update source after successful scan."""
        with db_session() as db:
            source = db.query(MonitoredSource).get(source.id)
            source.last_scanned = datetime.utcnow()
            source.error_count = 0
            db.commit()
            
    def _update_source_error(self, source: MonitoredSource, error: str) -> None:
        """Update source after failed scan."""
        with db_session() as db:
            source = db.query(MonitoredSource).get(source.id)
            source.last_error = error
            source.error_count = (source.error_count or 0) + 1
            db.commit()
