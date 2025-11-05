import json
import os
from datetime import datetime
from typing import List, Dict, Any

class MemoryService:
    """Service for managing conversation memory and metadata extraction."""
    
    def __init__(self, data_file: str = "../data/conversations.json"):
        self.data_file = data_file
        self.conversations = self._load_conversations()

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

    def extract_metadata(self, user_id: str, text: str) -> Dict[str, Any]:
        """Extract metadata from conversation text."""
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

        # Extract service types
        services = ["haircut", "coloring", "color", "styling", "spa", "treatment"]
        for service in services:
            if service in text_lower:
                metadata["service_type"] = service.title()

        # Extract stylist preferences
        stylists = ["riya", "maya", "sarah", "alex"]
        for stylist in stylists:
            if stylist in text_lower:
                metadata["preferred_stylist"] = stylist.title()

        # Extract email
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            metadata["email"] = emails[0]

        # Extract time and date keywords
        time_slots = ["10", "11", "12", "2", "3", "4", "5", "6"]
        for slot in time_slots:
            if f"{slot} am" in text_lower or f"{slot} pm" in text_lower or f"{slot}:00" in text_lower:
                if "am" in text_lower:
                    metadata["time"] = f"{slot}:00 AM"
                else:
                    metadata["time"] = f"{slot}:00 PM"

        date_keywords = ["tomorrow", "today", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        for keyword in date_keywords:
            if keyword in text_lower:
                metadata["date"] = keyword.title()

        if user_id in self.conversations:
            self.conversations[user_id]["metadata"].update(metadata)
            self._save_conversations()

        return metadata

    def get_user_metadata(self, user_id: str) -> Dict[str, Any]:
        """Get user metadata."""
        if user_id in self.conversations:
            return self.conversations[user_id]["metadata"]
        return {}
