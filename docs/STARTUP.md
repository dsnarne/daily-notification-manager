# 🚀 Quick Start Guide

## Prerequisites
- Python 3.8+
- pip

## Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env  # or create .env manually
```

## Environment Variables
Create a `.env` file with these variables:

```bash
# Application Settings
APP_NAME=DaiLY Notification Manager
DEBUG=false
SECRET_KEY=your-super-secret-key-change-this-in-production

# Database
DATABASE_URL=sqlite:///./daily.db

# Gmail Integration
GMAIL_CLIENT_ID=your-gmail-client-id
GMAIL_CLIENT_SECRET=your-gmail-client-secret

# Outlook/Teams Integration  
OUTLOOK_CLIENT_ID=your-outlook-client-id
OUTLOOK_CLIENT_SECRET=your-outlook-client-secret
OUTLOOK_TENANT_ID=your-tenant-id

# Slack Integration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret
SLACK_APP_TOKEN=xapp-your-slack-app-token

# Webhook Security
WEBHOOK_SECRET=your-webhook-secret-key

# Notification Settings
NOTIFICATION_CHECK_INTERVAL=60
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Running the Application

### Option 1: Full System (Recommended)
```bash
python run.py
```
This starts the database, scheduler, and API server together.

### Option 2: API Only
```bash
python main.py
```
This starts just the FastAPI server.

### Option 3: CLI Only
```bash
python daily_cli.py --help
```

## Access Points
- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Testing Integrations
```bash
python test_integrations.py
```

## CLI Commands
```bash
# List integrations
python daily_cli.py integrations list

# Create integration
python daily_cli.py integrations create

# Test integration
python daily_cli.py integrations test

# Demo mode
python daily_cli.py demo
``` 