from src.database import SessionLocal
from src.models.monitored_source import MonitoredSource

def print_monitored_sources():
    with SessionLocal() as db:
        sources = db.query(MonitoredSource).all()
        print("Monitored Sources:")
        for s in sources:
            print(f"ID: {s.id}, Type: {s.type}, Identifier: {s.identifier}, Name: {s.name}, Active: {s.is_active}")

def update_telegram_identifier(source_id: int, new_identifier: str):
    with SessionLocal() as db:
        source = db.query(MonitoredSource).get(source_id)
        if not source:
            print(f"Source with ID {source_id} not found.")
            return
        print(f"Updating source {source_id} identifier from {source.identifier} to {new_identifier}")
        source.identifier = new_identifier
        db.commit()
        print("Update complete.")

if __name__ == "__main__":
    print_monitored_sources()
    # Example usage: update_telegram_identifier(1, "-1001234567890")
