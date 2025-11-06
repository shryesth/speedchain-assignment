import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class MemoryService:
    """Service for managing conversation memory and metadata extraction."""
    
    def __init__(self, data_file: str = "../data/conversations.json"):
        self.data_file = data_file
        self.conversations = self._load_conversations()
        self.llm_service = None  # Will be injected
    
    def set_llm_service(self, llm_service):
        """Inject LLM service for intelligent metadata extraction."""
        self.llm_service = llm_service

    def _load_conversations(self) -> Dict[str, Any]:
        """Load conversations from JSON file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _save_conversations(self):
        """Save conversations to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w') as f:
                json.dump(self.conversations, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving conversations: {e}")

    def add_message(self, user_id: str, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add message to conversation history."""
        if user_id not in self.conversations:
            self.conversations[user_id] = {
                "messages": [],
                "metadata": {},
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self.conversations[user_id]["messages"].append(message)
        self.conversations[user_id]["last_updated"] = datetime.now().isoformat()
        
        if metadata:
            self.conversations[user_id]["metadata"].update(metadata)

        self._save_conversations()

    def get_conversation_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get conversation history."""
        if user_id in self.conversations:
            return self.conversations[user_id]["messages"]
        return []

    async def extract_metadata(self, user_id: str, text: str) -> Dict[str, Any]:
        """
        Extract metadata from conversation text using LLM (preferred) or regex fallback.
        LLM extraction is much more robust for speech-to-text variations.
        """
        metadata = {}
        
        # Try LLM extraction first (if available)
        if self.llm_service:
            try:
                # Get full conversation context for better extraction
                conversation_history = self.get_conversation_history(user_id)
                
                # Build context from recent messages
                context_messages = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
                context_text = " ".join([msg["content"] for msg in context_messages])
                context_text += f" {text}"  # Add current message
                
                # Use LLM to extract metadata
                metadata = await self.llm_service.extract_metadata_with_llm(context_text)
                logger.info(f"LLM extracted metadata: {metadata}")
                
            except Exception as e:
                logger.error(f"LLM extraction failed, falling back to regex: {e}")
                metadata = self._extract_metadata_regex(text)
        else:
            # Fallback to regex if LLM not available
            logger.warning("LLM service not available, using regex extraction")
            metadata = self._extract_metadata_regex(text)

        # Update user metadata
        if user_id in self.conversations:
            self.conversations[user_id]["metadata"].update(metadata)
            self._save_conversations()

        return metadata

    def _extract_metadata_regex(self, text: str) -> Dict[str, Any]:
        """
        Fallback regex-based metadata extraction.
        Less robust than LLM but works without API calls.
        """
        import re
        
        metadata = {}
        text_lower = text.lower()
        
        # Extract name
        name_indicators = ["my name is", "i'm", "im", "call me", "this is"]
        for indicator in name_indicators:
            if indicator in text_lower:
                parts = text_lower.split(indicator)
                if len(parts) > 1:
                    potential_name = parts[1].strip().split()[0]
                    if len(potential_name) > 1:
                        metadata["customer_name"] = potential_name.title()
                        break

        # Extract service types
        services = ["haircut", "coloring", "color", "styling", "spa", "treatment"]
        for service in services:
            if service in text_lower:
                metadata["service_type"] = service.title()
                break

        # Extract stylist preferences
        stylists = ["riya", "maya", "sarah", "alex"]
        for stylist in stylists:
            if stylist in text_lower:
                metadata["preferred_stylist"] = stylist.title()
                break

        # Extract email - handle both normal emails and speech-to-text variations
        # First try normal email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            metadata["email"] = emails[0]
        else:
            # Clean up common speech-to-text variations for email
            # Look for email keywords to isolate the email part
            email_keywords = ['email is', 'email id is', 'email address is', 'my email', 'email:', 'mail is']
            email_part = text_lower
            
            for keyword in email_keywords:
                if keyword in email_part:
                    # Extract only the part after the keyword
                    email_part = email_part.split(keyword)[1].strip()
                    # Take only the first sentence/phrase (up to period, comma, or end)
                    email_part = email_part.split('.')[0].split(',')[0].split('and')[0].strip()
                    break
            
            # Now clean up the isolated email part
            email_part = email_part.replace('at the rate', '@')
            email_part = email_part.replace('at rate', '@')
            email_part = email_part.replace(' at ', '@')
            email_part = email_part.replace(' dot ', '.')
            email_part = email_part.replace(' by ', '')
            
            # Try to extract email from cleaned text
            emails = re.findall(email_pattern, email_part)
            if emails:
                metadata["email"] = emails[0]
            else:
                # Last resort: look for pattern like "word+numbers@word.com"
                simple_pattern = r'([a-z0-9]+)@([a-z0-9]+\.[a-z]{2,})'
                simple_match = re.search(simple_pattern, email_part)
                if simple_match:
                    metadata["email"] = simple_match.group(0)

        # Extract time - improved pattern matching
        time_patterns = [
            (r'(\d{1,2})\s*(?:a\.?m\.?|am)', 'AM'),
            (r'(\d{1,2})\s*(?:p\.?m\.?|pm)', 'PM'),
            (r'(\d{1,2}):00\s*(am|pm)', lambda m: m.upper())
        ]
        
        for pattern, suffix in time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                hour = match.group(1)
                if isinstance(suffix, str):
                    metadata["time"] = f"{hour}:00 {suffix}"
                else:
                    metadata["time"] = f"{hour}:00 {match.group(2).upper()}"
                break

        date_keywords = ["tomorrow", "today", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        for keyword in date_keywords:
            if keyword in text_lower:
                metadata["date"] = keyword.title()
                break

        return metadata

    def get_user_metadata(self, user_id: str) -> Dict[str, Any]:
        """Get user metadata."""
        if user_id in self.conversations:
            return self.conversations[user_id]["metadata"]
        return {}
