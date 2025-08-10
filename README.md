# DaiLY - Agentic Work Notification Manager

DaiLY is an intelligent notification manager that filters and prioritizes your work notifications across multiple platforms based on your priorities and preferences.

## 🚀 Features

- **Multi-Platform Integration**: Connect to Email, Slack, Microsoft Teams, and custom webhooks
- **Smart Filtering**: AI-powered notification prioritization and filtering
- **Priority Management**: Customize notification priorities and quiet hours
- **Unified Interface**: Single dashboard for all your notifications
- **CLI & API**: Command-line interface and REST API for automation

## 🔌 Supported Integrations

### 1. Email APIs
- **Gmail**: OAuth2 integration with Gmail API
- **Outlook/Exchange**: Microsoft Graph API integration
- **Generic IMAP/SMTP**: Support for any email provider

### 2. Slack API
- **Bot Integration**: Full Slack bot with real-time events
- **Socket Mode**: Real-time message processing
- **Channel Management**: Access to public and private channels
- **Direct Messages**: Handle DMs and mentions

### 3. Microsoft Teams API
- **Microsoft Graph**: Full Teams integration
- **Team Management**: Access to teams, channels, and chats
- **Message Handling**: Process messages, mentions, and reactions
- **Webhook Support**: Real-time event subscriptions

### 4. Webhook/WebX API
- **Custom Integrations**: Connect any third-party service
- **Security**: HMAC signature verification
- **Flexible Format**: Support for various webhook payloads
- **Event Handling**: Custom event processing

## 🛠️ Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd daily-notification-manager
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables** (create `.env` file):
```bash
# Email Configuration
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
GMAIL_REFRESH_TOKEN=your_gmail_refresh_token

OUTLOOK_CLIENT_ID=your_outlook_client_id
OUTLOOK_CLIENT_SECRET=your_outlook_client_secret
OUTLOOK_TENANT_ID=your_outlook_tenant_id

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_APP_TOKEN=xapp-your-slack-app-token
SLACK_SIGNING_SECRET=your-slack-signing-secret

# Teams Configuration
TEAMS_CLIENT_ID=your_teams_client_id
TEAMS_CLIENT_SECRET=your_teams_client_secret
TEAMS_TENANT_ID=your_teams_tenant_id

# Security
SECRET_KEY=your-secret-key-here
```

## 🚀 Quick Start

### Using the CLI

1. **List available integrations**:
```bash
python daily_cli.py integrations list
```

2. **Create a Gmail integration**:
```bash
python daily_cli.py integrations create --platform email --name "My Gmail" --config '{"provider": "gmail", "client_id": "your_id", "client_secret": "your_secret", "refresh_token": "your_token"}'
```

3. **Create a Slack integration**:
```bash
python daily_cli.py integrations create --platform slack --name "My Slack" --config '{"bot_token": "xoxb-your-token", "app_token": "xapp-your-token", "signing_secret": "your-secret"}'
```

4. **Create a Teams integration**:
```bash
python daily_cli.py integrations create --platform teams --name "My Teams" --config '{"client_id": "your_id", "client_secret": "your_secret", "tenant_id": "your_tenant"}'
```

5. **Create a webhook integration**:
```bash
python daily_cli.py integrations create --platform webhook --name "My Webhook" --config '{"url": "https://api.example.com/webhook", "secret": "your-secret"}'
```

6. **Test an integration**:
```bash
python daily_cli.py integrations test 1
```

7. **Sync notifications**:
```bash
python daily_cli.py integrations sync 1
```

8. **View notifications**:
```bash
python daily_cli.py notifications list
```

9. **Run the demo**:
```bash
python daily_cli.py demo
```

### Using the API

Start the API server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## 📧 Email Integration Setup

### Gmail Setup

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Gmail API

2. **Create OAuth2 Credentials**:
   - Go to APIs & Services > Credentials
   - Create OAuth 2.0 Client ID
   - Download the client configuration

3. **Get Refresh Token**:
   - Use the OAuth2 flow to get a refresh token
   - Store it securely

### Outlook Setup

1. **Register Azure App**:
   - Go to [Azure Portal](https://portal.azure.com/)
   - Register a new application
   - Get client ID and secret

2. **Configure Permissions**:
   - Add Microsoft Graph permissions
   - Grant admin consent

## 💬 Slack Integration Setup

1. **Create Slack App**:
   - Go to [Slack API](https://api.slack.com/apps)
   - Create New App
   - Choose "From scratch"

2. **Configure OAuth & Permissions**:
   - Add bot token scopes:
     - `channels:read`
     - `chat:write`
     - `users:read`
     - `im:read`
     - `mpim:read`

3. **Install App to Workspace**:
   - Install the app
   - Copy the bot token

4. **Enable Socket Mode** (optional):
   - Enable Socket Mode
   - Generate app-level token

## 🏢 Teams Integration Setup

1. **Register Azure App**:
   - Go to [Azure Portal](https://portal.azure.com/)
   - Register a new application
   - Get client ID and secret

2. **Configure Microsoft Graph Permissions**:
   - Add permissions:
     - `Team.ReadBasic.All`
     - `Channel.ReadBasic.All`
     - `Chat.Read`
     - `User.Read`

3. **Grant Admin Consent**:
   - Grant admin consent for the permissions

## 🔗 Webhook Integration Setup

1. **Create Webhook Endpoint**:
   - Set up an endpoint to receive webhooks
   - Configure security (HMAC signatures)

2. **Configure DaiLY**:
   - Add webhook integration
   - Set the webhook URL and secret

3. **Send Test Webhook**:
   - Test the integration with sample data

## 🎯 Notification Management

### Priority Levels
- **Low**: Non-urgent notifications
- **Medium**: Standard work notifications
- **High**: Important notifications
- **Urgent**: Critical notifications requiring immediate attention

### Filtering Options
- **Keywords**: Include/exclude specific words
- **Senders**: Filter by notification source
- **Channels**: Filter by platform channels
- **Time-based**: Quiet hours and scheduling

### Rules Engine
Create custom rules for automatic notification processing:
- Mark certain notifications as read automatically
- Change priority based on content
- Forward notifications to other platforms
- Archive old notifications

## 🔧 Configuration

### Email Providers
```python
# Gmail
{
    "provider": "gmail",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "refresh_token": "your_refresh_token"
}

# Outlook
{
    "provider": "outlook",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "tenant_id": "your_tenant_id"
}

# Generic IMAP/SMTP
{
    "server": "smtp.example.com",
    "port": 587,
    "username": "your_email@example.com",
    "password": "your_password",
    "use_tls": True,
    "use_ssl": False
}
```

### Slack Configuration
```python
{
    "bot_token": "xoxb-your-bot-token",
    "app_token": "xapp-your-app-token",  # Optional
    "signing_secret": "your-signing-secret"  # Optional
}
```

### Teams Configuration
```python
{
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "tenant_id": "your_tenant_id"
}
```

### Webhook Configuration
```python
{
    "url": "https://api.example.com/webhook",
    "secret": "your_webhook_secret",  # Optional
    "headers": {"X-Custom-Header": "value"}  # Optional
}
```

## 🧪 Testing

Run the integration tests:
```bash
python test_integrations.py
```

Or use the CLI demo:
```bash
python daily_cli.py demo
```

## 📚 API Documentation

Once the server is running, visit:
- **Interactive API docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the test examples

## 🔮 Roadmap

- [ ] Database persistence
- [ ] User authentication
- [ ] Web dashboard
- [ ] Mobile app
- [ ] Advanced AI filtering
- [ ] Integration marketplace
- [ ] Analytics and reporting
- [ ] Team collaboration features 