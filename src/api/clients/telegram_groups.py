from loguru import logger

class TelegramGroupsClient:
    """Client for Telegram group search (not publicly available)."""
    def __init__(self):
        logger.warning("Telegram does not provide a public group search API. This client is a placeholder.")

    async def search_groups(self, query: str):
        """Attempt to search for Telegram groups. Not implemented."""
        raise NotImplementedError("Telegram group search is not supported by the public API.")
