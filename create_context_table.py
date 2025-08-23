"""
Script to create the user_contexts table in the database
"""

from app.core.database import engine, Base, UserContext
from sqlalchemy import inspect

def create_context_table():
    """Create the user_contexts table if it doesn't exist"""
    inspector = inspect(engine)
    
    # Check if table exists
    if 'user_contexts' not in inspector.get_table_names():
        print("Creating user_contexts table...")
        UserContext.__table__.create(engine)
        print("✅ user_contexts table created successfully!")
    else:
        print("user_contexts table already exists")

if __name__ == "__main__":
    create_context_table()