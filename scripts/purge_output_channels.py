from src.utils.db import db_session
from src.models.monitored_source import OutputChannel

with db_session() as db:
    deleted = db.query(OutputChannel).delete()
    db.commit()
    print(f"Purged {deleted} output channels.") 