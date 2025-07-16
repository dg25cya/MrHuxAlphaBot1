from src.utils.db import db_session
from src.models.monitored_source import MonitoredSource

with db_session() as db:
    sources = db.query(MonitoredSource).filter(MonitoredSource.is_active == True).all()
    if not sources:
        print('No active sources found.')
    else:
        for s in sources:
            print(f"Active source: {s.type} | {s.identifier} | {s.name}") 