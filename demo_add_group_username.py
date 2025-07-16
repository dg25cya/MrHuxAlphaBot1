from src.database import SessionLocal
from src.models.monitored_source import MonitoredSource

def print_monitored_sources():
    with SessionLocal() as db:
        sources = db.query(MonitoredSource).all()
        print("\n==== Monitored Sources ====")
        for s in sources:
            print(f"ID: {s.id} | Type: {s.type} | Identifier: {s.identifier} | Name: {s.name} | Active: {s.is_active}")
        print("==========================\n")

if __name__ == "__main__":
    print_monitored_sources()
