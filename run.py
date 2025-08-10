#!/usr/bin/env python3
"""
Startup script for DaiLY Notification Manager
"""

import asyncio
import uvicorn
from app.core.database import Base, engine
from app.core.scheduler import NotificationScheduler
from app.core.config import settings

async def init_database():
    """Initialize database tables"""
    print("🗄️  Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")

async def start_scheduler():
    """Start the notification scheduler"""
    print("⏰ Starting notification scheduler...")
    scheduler = NotificationScheduler()
    await scheduler.start()
    print("✅ Scheduler started")
    return scheduler

async def main():
    """Main startup function"""
    print("🚀 Starting DaiLY Notification Manager...")
    
    # Initialize database
    await init_database()
    
    # Start scheduler
    scheduler = await start_scheduler()
    
    print(f"🌐 Starting FastAPI server on port 8000...")
    print(f"📖 API documentation: http://localhost:8000/docs")
    print(f"🔧 Health check: http://localhost:8000/health")
    
    # Start FastAPI server
    config = uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        await scheduler.stop()
        print("✅ Shutdown complete")

if __name__ == "__main__":
    asyncio.run(main()) 