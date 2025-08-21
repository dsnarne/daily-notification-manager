#!/usr/bin/env python3
"""
Script to refresh Google OAuth tokens for Gmail and Calendar access.
Run this when you get 'invalid_grant' errors.
"""

import os
import json
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

load_dotenv()

# Your OAuth2 credentials from .env
CLIENT_ID = os.getenv('GMAIL_CLIENT_ID')
CLIENT_SECRET = os.getenv('GMAIL_CLIENT_SECRET')

# OAuth2 scopes for Gmail and Calendar
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.acls.readonly'  # Google may add this automatically
]

def get_new_tokens():
    """Get new OAuth2 tokens"""
    
    # Configure OAuth flow
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["https://localhost:8080"]
            }
        },
        scopes=SCOPES
    )
    
    flow.redirect_uri = "https://localhost:8080"
    
    # Get authorization URL
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force consent to get refresh token
    )
    
    print("=" * 60)
    print("🔑 GOOGLE OAUTH TOKEN REFRESH")
    print("=" * 60)
    print()
    print("1. Open this URL in your browser:")
    print(f"   {auth_url}")
    print()
    print("2. Complete the authorization process")
    print("3. Copy the authorization code from the redirect URL")
    print("   (It will be in the 'code=' parameter)")
    print("   Note: You may get a 'connection not secure' warning - this is normal for localhost HTTPS")
    print()
    
    # Get authorization code from user
    auth_code = input("Enter the authorization code: ").strip()
    
    try:
        # Exchange code for tokens
        flow.fetch_token(code=auth_code)
        
        credentials = flow.credentials
        
        print()
        print("✅ SUCCESS! New tokens generated:")
        print("=" * 40)
        print(f"ACCESS_TOKEN: {credentials.token}")
        print(f"REFRESH_TOKEN: {credentials.refresh_token}")
        print()
        print("🔧 Update your .env file with:")
        print(f"GMAIL_REFRESH_TOKEN={credentials.refresh_token}")
        print(f"GOOGLE_CALENDAR_REFRESH_TOKEN={credentials.refresh_token}")
        print()
        
        # Save to file for backup
        token_data = {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scopes": SCOPES
        }
        
        with open("google_tokens_backup.json", "w") as f:
            json.dump(token_data, f, indent=2)
        
        print("💾 Tokens also saved to: google_tokens_backup.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_new_tokens()