# mcp-servers/communication-server/integrations/gmail.py
import os
import asyncio
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import List, Dict, Optional
from pathlib import Path
from collections import defaultdict, Counter

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

from ..models import SenderImportance, ConversationMessage, DomainInfo

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

class GmailIntegration:
    """Gmail integration for notification and communication analysis"""
    
    def __init__(self):
        self.company_domain = os.getenv("COMPANY_DOMAIN", "company.com")
        self.trusted_domains = set(os.getenv("TRUSTED_DOMAINS", "").split(","))
        if self.company_domain:
            self.trusted_domains.add(self.company_domain)
    
    def _mint_access_token(self) -> str:
        """Generate access token from refresh token"""
        refresh = os.getenv("GMAIL_REFRESH_TOKEN")
        cid = os.getenv("GMAIL_CLIENT_ID")
        csec = os.getenv("GMAIL_CLIENT_SECRET")
        
        if not all([refresh, cid, csec]):
            raise RuntimeError("Missing env: GMAIL_REFRESH_TOKEN / GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET")
        
        creds = Credentials(
            None, 
            refresh_token=refresh, 
            token_uri="https://oauth2.googleapis.com/token",
            client_id=cid, 
            client_secret=csec, 
            scopes=SCOPES
        )
        creds.refresh(Request())
        return creds.token
    
    def _get_service(self, access_token: str):
        """Get Gmail service client"""
        creds = Credentials(token=access_token)
        return build("gmail", "v1", credentials=creds, cache_discovery=False)
    
    async def list_notifications(self, 
                                since_iso: Optional[str] = None,
                                query: Optional[str] = None,
                                max_results: int = 20) -> List[Dict]:
        """List Gmail notifications with filters"""
        
        # Run in thread pool since Gmail API is sync
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._list_notifications_sync,
            since_iso,
            query, 
            max_results
        )
    
    def _list_notifications_sync(self,
                                since_iso: Optional[str] = None,
                                query: Optional[str] = None, 
                                max_results: int = 20) -> List[Dict]:
        """Synchronous implementation of list_notifications"""
        
        access_token = self._mint_access_token()
        service = self._get_service(access_token)
        
        # Build Gmail query
        q = query or "label:INBOX newer_than:1d"
        if since_iso:
            try:
                dt = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))
                q = f"{q} after:{dt.strftime('%Y/%m/%d')}"
            except Exception:
                pass
        
        # Get message list
        result = service.users().messages().list(
            userId="me", 
            q=q, 
            maxResults=max_results
        ).execute()
        
        messages = result.get("messages", [])
        notifications = []
        
        for msg in messages:
            try:
                # Get message metadata
                meta = service.users().messages().get(
                    userId="me",
                    id=msg["id"],
                    format="metadata",
                    metadataHeaders=["From", "To", "Subject", "Date"]
                ).execute()
                
                headers = {
                    h["name"].lower(): h["value"] 
                    for h in meta.get("payload", {}).get("headers", [])
                }
                
                # Parse date
                created_at = datetime.utcnow()
                if headers.get("date"):
                    try:
                        created_at = parsedate_to_datetime(headers["date"])
                    except:
                        pass
                
                # Build notification object
                notification = {
                    "id": f"gmail:{msg['id']}",
                    "external_id": msg["id"],
                    "thread_id": meta.get("threadId"),
                    "platform": "email",
                    "notification_type": "message",
                    "title": headers.get("subject", "(No Subject)"),
                    "content": meta.get("snippet", ""),
                    "sender": headers.get("from", ""),
                    "recipient": headers.get("to", ""),
                    "priority": self._determine_priority(headers),
                    "metadata": {
                        "labelIds": ",".join(meta.get("labelIds", [])),
                        "threadId": meta.get("threadId", ""),
                        "internalDate": meta.get("internalDate", "")
                    },
                    "created_at": created_at,
                    "link": f"https://mail.google.com/mail/u/0/#inbox/{msg['id']}"
                }
                
                notifications.append(notification)
                
            except Exception as e:
                print(f"Error processing message {msg.get('id')}: {e}")
                continue
        
        return notifications
    
    def _determine_priority(self, headers: Dict[str, str]) -> str:
        """Determine message priority based on headers and content"""
        sender = headers.get("from", "").lower()
        subject = headers.get("subject", "").lower()
        
        # Check for urgent keywords
        urgent_keywords = ["urgent", "asap", "emergency", "critical", "immediate"]
        if any(keyword in subject for keyword in urgent_keywords):
            return "urgent"
        
        # Check if from company domain
        if self.company_domain and self.company_domain in sender:
            return "high"
        
        # Check for high priority keywords
        high_keywords = ["deadline", "meeting", "review", "approval", "action required"]
        if any(keyword in subject for keyword in high_keywords):
            return "high"
        
        return "medium"
    
    async def analyze_sender_importance(self, 
                                      sender_email: str, 
                                      days_back: int = 30) -> SenderImportance:
        """Analyze sender importance based on communication history"""
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._analyze_sender_importance_sync,
            sender_email,
            days_back
        )
    
    def _analyze_sender_importance_sync(self, 
                                      sender_email: str,
                                      days_back: int = 30) -> Dict:
        """Synchronous implementation of sender importance analysis"""
        
        try:
            access_token = self._mint_access_token()
            service = self._get_service(access_token)
            
            # Search for emails from this sender
            since_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            query = f"from:{sender_email} after:{since_date}"
            
            result = service.users().messages().list(
                userId="me",
                q=query,
                maxResults=100
            ).execute()
            
            messages = result.get("messages", [])
            
            # Analyze communication patterns
            message_count = len(messages)
            response_times = []
            last_interaction = None
            
            # Get domain info
            domain = sender_email.split("@")[-1] if "@" in sender_email else ""
            domain_info = self._analyze_domain(domain)
            
            # Determine relationship type
            relationship_type = "external"
            if domain == self.company_domain:
                relationship_type = "internal"
            elif domain in self.trusted_domains:
                relationship_type = "client"
            
            # Calculate importance score (0-10)
            importance_score = 5.0  # Base score
            
            # Adjust based on communication frequency
            monthly_frequency = (message_count / days_back) * 30
            if monthly_frequency > 20:
                importance_score += 2.0
            elif monthly_frequency > 10:
                importance_score += 1.0
            elif monthly_frequency < 2:
                importance_score -= 1.0
            
            # Adjust based on relationship type
            if relationship_type == "internal":
                importance_score += 1.5
            elif relationship_type == "client":
                importance_score += 1.0
            
            # Adjust based on domain trust
            if domain_info["is_trusted"]:
                importance_score += 0.5
            
            # Cap at 10
            importance_score = min(10.0, max(0.0, importance_score))
            
            # Get last interaction date
            if messages:
                try:
                    latest_msg = service.users().messages().get(
                        userId="me",
                        id=messages[0]["id"],
                        format="metadata",
                        metadataHeaders=["Date"]
                    ).execute()
                    
                    headers = {
                        h["name"].lower(): h["value"]
                        for h in latest_msg.get("payload", {}).get("headers", [])
                    }
                    
                    if headers.get("date"):
                        last_interaction = parsedate_to_datetime(headers["date"])
                        
                except Exception:
                    pass
            
            return {
                "sender": sender_email,
                "sender_email": sender_email,
                "importance_score": importance_score,
                "email_frequency": int(monthly_frequency),
                "response_rate": 0.9,  # Mock value
                "avg_response_time_hours": 2.5,  # Mock value
                "is_internal": domain_info["is_internal"],
                "recent_interactions": message_count,
                "classification": "high_priority" if importance_score > 7 else "medium"
            }
            
        except Exception as e:
            # Return default low importance on error
            return {
                "sender_email": sender_email,
                "importance_score": 3.0,
                "relationship_type": "unknown",
                "communication_frequency": 0,
                "avg_response_time_hours": None,
                "last_interaction": None,
                "domain_trust_level": "low",
                "context": f"Error analyzing sender: {str(e)}"
            }
    
    async def get_recent_conversations(self,
                                     contact_email: str,
                                     days_back: int = 7,
                                     max_messages: int = 10) -> List[Dict]:
        """Get recent conversation history with a contact"""
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._get_recent_conversations_sync,
            contact_email,
            days_back,
            max_messages
        )
    
    def _get_recent_conversations_sync(self,
                                     contact_email: str,
                                     days_back: int = 7,
                                     max_messages: int = 10) -> List[Dict]:
        """Synchronous implementation of recent conversations"""
        
        try:
            access_token = self._mint_access_token()
            service = self._get_service(access_token)
            
            # Search for emails with this contact
            since_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            query = f"(from:{contact_email} OR to:{contact_email}) after:{since_date}"
            
            result = service.users().messages().list(
                userId="me",
                q=query,
                maxResults=max_messages
            ).execute()
            
            messages = result.get("messages", [])
            conversations = []
            
            for msg in messages:
                try:
                    meta = service.users().messages().get(
                        userId="me",
                        id=msg["id"],
                        format="metadata",
                        metadataHeaders=["From", "To", "Subject", "Date", "In-Reply-To"]
                    ).execute()
                    
                    headers = {
                        h["name"].lower(): h["value"]
                        for h in meta.get("payload", {}).get("headers", [])
                    }
                    
                    timestamp = datetime.utcnow()
                    if headers.get("date"):
                        try:
                            timestamp = parsedate_to_datetime(headers["date"])
                        except:
                            pass
                    
                    conversation = {
                        "id": msg["id"],
                        "subject": headers.get("subject", "(No Subject)"),
                        "sender": headers.get("from", ""),
                        "recipient": headers.get("to", ""),
                        "content_preview": meta.get("snippet", "")[:200],
                        "timestamp": timestamp,
                        "is_reply": bool(headers.get("in-reply-to"))
                    }
                    
                    conversations.append(conversation)
                    
                except Exception as e:
                    print(f"Error processing conversation message {msg.get('id')}: {e}")
                    continue
            
            # Sort by timestamp (newest first)
            conversations.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return conversations
            
        except Exception as e:
            print(f"Error getting conversations with {contact_email}: {e}")
            return []
    
    async def check_sender_domain(self, sender_email: str) -> Dict:
        """Check sender domain information"""
        
        domain = sender_email.split("@")[-1] if "@" in sender_email else ""
        result = self._analyze_domain(domain)
        result["email"] = sender_email
        return result
    
    def _analyze_domain(self, domain: str) -> Dict:
        """Analyze domain reputation and type"""
        
        is_company = domain == self.company_domain
        is_trusted = domain in self.trusted_domains
        
        # Basic domain type detection
        domain_type = "unknown"
        if domain.endswith(".edu"):
            domain_type = "educational"
        elif domain.endswith(".gov"):
            domain_type = "government"
        elif domain in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]:
            domain_type = "public"
        elif is_company or is_trusted:
            domain_type = "corporate"
        
        # Calculate reputation score
        reputation_score = 5.0
        if is_company:
            reputation_score = 10.0
        elif is_trusted:
            reputation_score = 8.0
        elif domain_type == "educational":
            reputation_score = 7.0
        elif domain_type == "government":
            reputation_score = 8.0
        elif domain_type == "public":
            reputation_score = 4.0
        
        return {
            "email": f"user@{domain}",
            "domain": domain,
            "domain_type": domain_type,
            "is_internal": is_company,
            "is_trusted": is_trusted
        }