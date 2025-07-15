import aiohttp
from ...config.settings import get_settings
from loguru import logger

settings = get_settings()

class XClient:
    """Client for X/Twitter API v2."""
    def __init__(self):
        self.base_url = "https://api.twitter.com/2"
        self.bearer_token = getattr(settings, 'x_bearer_token', None)
        if not self.bearer_token:
            raise ValueError("X_BEARER_TOKEN is not set in settings.")
        self.headers = {"Authorization": f"Bearer {self.bearer_token}"}

    async def get_user_profile(self, username: str):
        url = f"{self.base_url}/users/by/username/{username}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logger.error(f"Failed to fetch X profile for {username}: {resp.status}")
                    return None
