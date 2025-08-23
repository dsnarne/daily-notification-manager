"""
Migration script to add deduplication support to notifications table
"""

from app.core.database import engine, Base
from sqlalchemy import text, inspect
import logging

logger = logging.getLogger(__name__)

def migrate_notification_dedup():
    """Add columns for deduplication support"""
    
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('notifications')]
    
    with engine.connect() as conn:
        # Add last_updated column if it doesn't exist
        if 'last_updated' not in columns:
            try:
                conn.execute(text("""
                    ALTER TABLE notifications 
                    ADD COLUMN last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                """))
                conn.commit()
                print("✅ Added last_updated column to notifications table")
            except Exception as e:
                print(f"❌ Failed to add last_updated column: {e}")
        
        # Add index on external_id for faster lookups if not exists
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notifications_external_id ON notifications(external_id)"))
            conn.commit()
            print("✅ Added index on external_id")
        except Exception as e:
            print(f"❌ Failed to create index: {e}")
        
        # Add composite index for deduplication lookups
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notifications_dedup ON notifications(external_id, platform)"))
            conn.commit()
            print("✅ Added composite deduplication index")
        except Exception as e:
            print(f"❌ Failed to create composite index: {e}")

if __name__ == "__main__":
    migrate_notification_dedup()
    print("🎉 Migration completed!")