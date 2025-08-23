"""
Database configuration and models for DaiLY Notification Manager
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import os

from .config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database Models
class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    notification_preferences = relationship("NotificationPreference", back_populates="user")
    integrations = relationship("Integration", back_populates="user")

class Integration(Base):
    """Integration model for different notification platforms"""
    __tablename__ = "integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform = Column(String(50), nullable=False)  # email, slack, teams, webhook
    name = Column(String(100), nullable=False)
    config = Column(JSON, nullable=False)  # Platform-specific configuration
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="integrations")
    notifications = relationship("Notification", back_populates="integration")

class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform = Column(String(50), nullable=False)
    priority_levels = Column(JSON, nullable=False)  # Priority settings for different notification types
    quiet_hours = Column(JSON, nullable=True)  # Quiet hours configuration
    filters = Column(JSON, nullable=True)  # Custom filters
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="notification_preferences")

class Notification(Base):
    """Notification model"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False)
    external_id = Column(String(255), nullable=True, index=True)  # ID from external platform
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    sender = Column(String(255), nullable=True)
    recipient = Column(String(255), nullable=True)
    platform = Column(String(50), nullable=False)
    notification_type = Column(String(100), nullable=False)  # message, mention, alert, etc.
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    status = Column(String(20), default="unread")  # unread, read, archived
    platform_metadata = Column(JSON, nullable=True)  # Platform-specific metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # Track updates
    
    # Relationships
    integration = relationship("Integration", back_populates="notifications")

class NotificationRule(Base):
    """Rules for notification processing"""
    __tablename__ = "notification_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    conditions = Column(JSON, nullable=False)  # Rule conditions
    actions = Column(JSON, nullable=False)  # Actions to take when conditions are met
    priority = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class UserContext(Base):
    """User working context for dynamic notification prioritization"""
    __tablename__ = "user_contexts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    context_description = Column(Text, nullable=False)  # User's current working context
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class NotificationHistory(Base):
    """Notification delivery history"""
    __tablename__ = "notification_history"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False)
    delivery_method = Column(String(50), nullable=False)  # email, push, sms, etc.
    delivery_status = Column(String(20), nullable=False)  # sent, delivered, failed
    delivery_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0) 