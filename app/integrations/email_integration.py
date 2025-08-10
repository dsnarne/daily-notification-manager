"""
Email integration service for DaiLY Notification Manager
Supports Gmail, Outlook, and Exchange
"""

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import re

from exchangelib import Credentials, Account, DELEGATE, Configuration
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as GoogleCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ..models.schemas import EmailConfig, GmailConfig, OutlookConfig
from ..core.config import EMAIL_PROVIDERS

logger = logging.getLogger(__name__)

class EmailIntegration:
    """Base email integration class"""
    
    def __init__(self, config: EmailConfig):
        self.config = config
        self.connection = None
        
    def connect(self) -> bool:
        """Establish connection to email server"""
        try:
            if self.config.use_ssl:
                self.connection = smtplib.SMTP_SSL(self.config.server, self.config.port)
            else:
                self.connection = smtplib.SMTP(self.config.server, self.config.port)
                
            if self.config.use_tls:
                self.connection.starttls()
                
            self.connection.login(self.config.username, self.config.password)
            logger.info(f"Connected to email server: {self.config.server}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            return False
    
    def disconnect(self):
        """Close email connection"""
        if self.connection:
            self.connection.quit()
            self.connection = None
    
    def send_email(self, to: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send an email"""
        try:
            if not self.connection:
                if not self.connect():
                    return False
            
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.username
            msg['To'] = to
            msg['Subject'] = subject
            
            # Add text and HTML parts
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            self.connection.send_message(msg)
            logger.info(f"Email sent successfully to {to}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

class GmailIntegration(EmailIntegration):
    """Gmail-specific integration using Gmail API"""
    
    def __init__(self, config: GmailConfig):
        self.gmail_config = config
        self.service = None
        self.credentials = None
        
    def authenticate(self) -> bool:
        """Authenticate with Gmail API"""
        try:
            SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
                     'https://www.googleapis.com/auth/gmail.send']
            
            # Load existing credentials
            if self.gmail_config.refresh_token:
                self.credentials = GoogleCredentials(
                    None,  # No access token initially
                    refresh_token=self.gmail_config.refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.gmail_config.client_id,
                    client_secret=self.gmail_config.client_secret
                )
            
            # If no valid credentials, get new ones
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_config(
                        {
                            "installed": {
                                "client_id": self.gmail_config.client_id,
                                "client_secret": self.gmail_config.client_secret,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
                            }
                        },
                        SCOPES
                    )
                    self.credentials = flow.run_local_server(port=0)
            
            # Build the Gmail service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            logger.info("Gmail API authenticated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            return False
    
    def fetch_emails(self, max_results: int = 50, query: str = "") -> List[Dict[str, Any]]:
        """Fetch emails from Gmail"""
        try:
            if not self.service:
                if not self.authenticate():
                    return []
            
            # Build query
            gmail_query = query if query else "is:unread"
            
            # Get messages
            results = self.service.users().messages().list(
                userId='me', 
                q=gmail_query, 
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me', 
                    id=message['id']
                ).execute()
                
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                
                # Extract body
                body = self._extract_body(msg['payload'])
                
                emails.append({
                    'id': message['id'],
                    'subject': subject,
                    'sender': sender,
                    'body': body,
                    'date': date,
                    'thread_id': msg.get('threadId', ''),
                    'labels': msg.get('labelIds', [])
                })
            
            return emails
            
        except Exception as e:
            logger.error(f"Failed to fetch Gmail emails: {e}")
            return []
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from Gmail API payload"""
        if 'body' in payload and payload['body'].get('data'):
            import base64
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        import base64
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        
        return ""

class OutlookIntegration(EmailIntegration):
    """Outlook/Exchange integration using Microsoft Graph API"""
    
    def __init__(self, config: OutlookConfig):
        self.outlook_config = config
        self.account = None
        
    def authenticate(self) -> bool:
        """Authenticate with Microsoft Graph API"""
        try:
            credentials = Credentials(
                username=self.outlook_config.client_id,
                password=self.outlook_config.client_secret
            )
            
            config = Configuration(
                service_endpoint=f'https://outlook.office365.com/EWS/Exchange.asmx',
                credentials=credentials
            )
            
            self.account = Account(
                primary_smtp_address=self.outlook_config.client_id,
                config=config,
                access_type=DELEGATE
            )
            
            logger.info("Outlook API authenticated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Outlook authentication failed: {e}")
            return False
    
    def fetch_emails(self, max_results: int = 50, folder: str = "Inbox") -> List[Dict[str, Any]]:
        """Fetch emails from Outlook"""
        try:
            if not self.account:
                if not self.authenticate():
                    return []
            
            # Get inbox folder
            inbox = self.account.inbox
            
            # Get messages
            messages = inbox.filter(is_read=False).order_by('-datetime_received')[:max_results]
            
            emails = []
            for msg in messages:
                emails.append({
                    'id': str(msg.id),
                    'subject': msg.subject or 'No Subject',
                    'sender': str(msg.sender.email_address) if msg.sender else 'Unknown',
                    'body': msg.body or '',
                    'date': msg.datetime_received.isoformat() if msg.datetime_received else '',
                    'thread_id': str(msg.thread_id) if hasattr(msg, 'thread_id') else '',
                    'labels': [str(label) for label in msg.categories] if msg.categories else []
                })
            
            return emails
            
        except Exception as e:
            logger.error(f"Failed to fetch Outlook emails: {e}")
            return []

class IMAPIntegration(EmailIntegration):
    """Generic IMAP integration for any email provider"""
    
    def __init__(self, config: EmailConfig):
        super().__init__(config)
        self.imap_connection = None
        
    def connect_imap(self) -> bool:
        """Connect to IMAP server"""
        try:
            if self.config.use_ssl:
                self.imap_connection = imaplib.IMAP4_SSL(self.config.server, 993)
            else:
                self.imap_connection = imaplib.IMAP4(self.config.server, 143)
            
            self.imap_connection.login(self.config.username, self.config.password)
            logger.info(f"IMAP connection established: {self.config.server}")
            return True
            
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            return False
    
    def fetch_emails(self, max_results: int = 50, folder: str = "INBOX") -> List[Dict[str, Any]]:
        """Fetch emails via IMAP"""
        try:
            if not self.imap_connection:
                if not self.connect_imap():
                    return []
            
            # Select folder
            self.imap_connection.select(folder)
            
            # Search for unread messages
            status, messages = self.imap_connection.search(None, 'UNSEEN')
            
            if status != 'OK':
                logger.error("Failed to search emails")
                return []
            
            email_ids = messages[0].split()
            emails = []
            
            # Limit results
            email_ids = email_ids[-max_results:] if len(email_ids) > max_results else email_ids
            
            for email_id in email_ids:
                status, msg_data = self.imap_connection.fetch(email_id, '(RFC822)')
                
                if status == 'OK':
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Extract subject
                    subject = decode_header(email_message["subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    
                    # Extract sender
                    sender = decode_header(email_message["from"])[0][0]
                    if isinstance(sender, bytes):
                        sender = sender.decode()
                    
                    # Extract body
                    body = self._extract_body_from_message(email_message)
                    
                    emails.append({
                        'id': email_id.decode(),
                        'subject': subject or 'No Subject',
                        'sender': sender or 'Unknown',
                        'body': body,
                        'date': email_message.get('date', ''),
                        'thread_id': email_message.get('message-id', ''),
                        'labels': []
                    })
            
            return emails
            
        except Exception as e:
            logger.error(f"Failed to fetch IMAP emails: {e}")
            return []
    
    def _extract_body_from_message(self, email_message) -> str:
        """Extract body from email message"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = email_message.get_payload(decode=True).decode()
        
        return body
    
    def disconnect_imap(self):
        """Close IMAP connection"""
        if self.imap_connection:
            self.imap_connection.close()
            self.imap_connection.logout()
            self.imap_connection = None

class EmailIntegrationFactory:
    """Factory for creating email integrations"""
    
    @staticmethod
    def create_integration(config: EmailConfig) -> EmailIntegration:
        """Create appropriate email integration based on config"""
        if hasattr(config, 'provider') and config.provider:
            if config.provider.lower() == 'gmail':
                return GmailIntegration(config)
            elif config.provider.lower() == 'outlook':
                return OutlookIntegration(config)
        
        # Default to IMAP
        return IMAPIntegration(config) 