from src.database import SessionLocal
from src.models.output_channel import OutputChannel
from sqlalchemy import update

def fix_output_channel_types():
    session = SessionLocal()
    try:
        # Map of lowercase to uppercase enum values
        type_map = {
            'telegram': 'TELEGRAM',
            'discord': 'DISCORD',
            'x': 'X',
            'webhook': 'WEBHOOK',
        }
        for old, new in type_map.items():
            session.execute(
                update(OutputChannel).where(OutputChannel.type == old).values(type=new)
            )
        session.commit()
        print("✅ OutputChannel types fixed.")
    except Exception as e:
        print(f"❌ Error fixing OutputChannel types: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    fix_output_channel_types() 