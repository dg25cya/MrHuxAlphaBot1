from src.utils.db import db_session
from src.models.monitored_source import OutputChannel, OutputType
from src.config.settings import get_settings
from src.core.telegram.client import initialize_client
import asyncio

async def add_telegram_output():
    settings = get_settings()
    client = await initialize_client()
    await client.start()
    me = await client.get_me()
    print(f"Bot user: {me.username or me.id}")

    # Get all dialogs (groups/channels)
    async for dialog in client.iter_dialogs():
        if dialog.is_channel and dialog.entity.creator or dialog.entity.admin_rights:
            print(f"Found admin in: {dialog.name} (ID: {dialog.id})")
            with db_session() as db:
                channel = OutputChannel(
                    type=OutputType.TELEGRAM,
                    identifier=str(dialog.id),
                    name=dialog.name,
                    is_active=True,
                    is_alerts=True
                )
                db.add(channel)
                db.commit()
                print(f"Added output channel: {dialog.name} (ID: {dialog.id})")
            break
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(add_telegram_output()) 