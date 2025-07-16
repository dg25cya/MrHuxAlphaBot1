import asyncio
from src.utils.db import db_session
from src.models.monitored_source import OutputChannel
from src.core.telegram.client import initialize_client
from src.core.services.output_service import OutputService

async def send_test_alert():
    client = await initialize_client()
    await client.start()
    with db_session() as db:
        channel = db.query(OutputChannel).filter(OutputChannel.identifier == '@MrHuAlphaBotPlays').first()
        if not channel:
            print('Output channel @MrHuAlphaBotPlays not found.')
            return
        output_service = OutputService(db, telegram_client=client)
        await output_service.send_message(
            channel=channel,
            content='🚨 TEST ALERT: This is a test message from MR HUX ALPHA BOT.'
        )
        print('Test alert sent to @MrHuAlphaBotPlays.')
    client.disconnect()

if __name__ == "__main__":
    asyncio.run(send_test_alert()) 