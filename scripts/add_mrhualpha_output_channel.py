from src.utils.db import db_session
from src.models.monitored_source import OutputChannel, OutputType

with db_session() as db:
    channel = OutputChannel(
        type=OutputType.TELEGRAM,
        identifier='@MrHuAlphaBotPlays',
        name='Mr Hux Alpha Bot Plays',
        is_active=True,
        is_alerts=True
    )
    db.add(channel)
    db.commit()
    print('Added @MrHuAlphaBotPlays as Telegram output channel for alerts.') 