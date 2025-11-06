import logging
import os
import json
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AppointmentMetadata(BaseModel):
    """Schema for extracted appointment metadata."""
    customer_name: Optional[str] = Field(None, description="Customer's full name")
    service_type: Optional[str] = Field(None, description="Type of service (e.g., Haircut, Coloring, Styling)")
    preferred_stylist: Optional[str] = Field(None, description="Preferred stylist name (Riya, Maya, Sarah, or Alex)")
    date: Optional[str] = Field(None, description="Appointment date (e.g., Monday, Tomorrow, Today)")
    time: Optional[str] = Field(None, description="Appointment time in 12-hour format (e.g., 10:00 AM)")
    email: Optional[str] = Field(None, description="Customer's email address")
    phone: Optional[str] = Field(None, description="Customer's phone number")

class LLMService:
    """Service for LLM-based conversation and intent understanding."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"
        
        # Salon context
        self.salon_context = {
            "name": "Gloss & Glow Hair Salon",
            "services": ["Haircuts", "Hair Coloring", "Styling", "Spa Treatments"],
            "stylists": {
                "Riya": "Haircuts & Styling",
                "Maya": "Hair Coloring & Highlights",
                "Sarah": "Spa Treatments & Hair Care",
                "Alex": "Creative Cuts & Color"
            },
            "hours": "Monday-Saturday, 10 AM - 7 PM",
            "booking_slots": ["10:00 AM", "11:00 AM", "12:00 PM", "2:00 PM", 
                            "3:00 PM", "4:00 PM", "5:00 PM", "6:00 PM"]
        }
    
    def get_system_prompt(self) -> str:
        """Generate system prompt for the AI receptionist."""
        return f"""You are a friendly AI receptionist for {self.salon_context['name']}, a premium hair salon.

SALON DETAILS:
- Services: {', '.join(self.salon_context['services'])}
- Stylists and Specializations:
  * Riya: {self.salon_context['stylists']['Riya']}
  * Maya: {self.salon_context['stylists']['Maya']}
  * Sarah: {self.salon_context['stylists']['Sarah']}
  * Alex: {self.salon_context['stylists']['Alex']}
- Hours: {self.salon_context['hours']}
- Available slots: {', '.join(self.salon_context['booking_slots'])}

YOUR ROLE:
1. Greet customers warmly and professionally
2. Help them choose services based on their needs
3. Collect booking information: name, service, stylist, date, time, email
4. Confirm appointments clearly
5. Answer questions about services and policies

BOOKING PROCESS:
- Ask for: customer name, service type, preferred stylist, date, time, and email
- Suggest appropriate stylists based on service
- Confirm all details before booking
- Inform about email confirmation

STYLE:
- Warm, professional, conversational
- Keep responses concise (2-3 sentences max)
- Ask one question at a time
- Be helpful and knowledgeable

Remember: You represent the salon's first impression!"""

    async def get_response(self, user_message: str, conversation_history: List[Dict[str, str]]) -> str:
        """
        Get LLM response based on user message and conversation history.
        
        Args:
            user_message: Current user message
            conversation_history: Previous conversation messages
            
        Returns:
            LLM-generated response
        """
        try:
            # Build messages for API
            messages = [{"role": "system", "content": self.get_system_prompt()}]
            
            # Add conversation history (last 10 messages for context)
            for msg in conversation_history[-10:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Get response from LLM
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=200
            )
            
            assistant_message = response.choices[0].message.content
            logger.info(f"LLM Response: {assistant_message}")
            
            return assistant_message
            
        except Exception as e:
            logger.error(f"Error getting LLM response: {e}")
            return "I apologize, I'm having trouble processing that. Could you please repeat?"
    
    async def should_book_appointment(self, llm_response: str, metadata: Dict[str, Any]) -> bool:
        """
        Determine if an appointment should be booked based on context.
        
        Args:
            llm_response: Latest LLM response
            metadata: Extracted conversation metadata
            
        Returns:
            True if appointment should be booked
        """
        # Check for booking confirmation phrases
        booking_phrases = [
            "confirmed", "scheduled", "booked", "appointment set",
            "i've scheduled", "i've booked", "all set",
            "appointment is confirmed", "you're all set",
            "i have you booked", "booking confirmed"
        ]
        
        response_lower = llm_response.lower()
        has_booking_phrase = any(phrase in response_lower for phrase in booking_phrases)
        
        # Check if we have all required information
        required_fields = ["customer_name", "service_type", "email", "date", "time"]
        has_all_info = all(field in metadata and metadata[field] for field in required_fields)
        
        # Log for debugging
        if has_booking_phrase:
            logger.info(f"Booking phrase detected in response: {llm_response}")
        if has_all_info:
            logger.info(f"All required fields present: {metadata}")
        else:
            missing = [f for f in required_fields if f not in metadata or not metadata[f]]
            logger.info(f"Missing required fields for booking: {missing}")
        
        return has_booking_phrase and has_all_info

    async def extract_metadata_with_llm(self, conversation_text: str, existing_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extract appointment metadata from conversation using LLM with structured output.
        This is more robust than regex for handling speech-to-text variations.
        
        Args:
            conversation_text: The conversation text to extract metadata from
            existing_metadata: Previously extracted metadata to include in context
            
        Returns:
            Dictionary with extracted metadata fields
        """
        try:
            # Build existing info context
            existing_info = ""
            if existing_metadata:
                existing_info = "\n\nPreviously extracted information:"
                for key, value in existing_metadata.items():
                    existing_info += f"\n- {key}: {value}"
            
            extraction_prompt = f"""Extract appointment booking information from this conversation text.
The text may come from speech-to-text and might have variations like:
- "my email is shresth at the rate 4236 at gmail dot com" → shresth4236@gmail.com
- "aloni at the regiment" → aloni@theregiment.com (assume .com if no extension mentioned)
- "my name is john smith" → John Smith  
- "eleven am" or "11 am" → 11:00 AM
- "hair coloring" or "color" → Hair Coloring

Conversation text: "{conversation_text}"{existing_info}

IMPORTANT: 
1. Extract ALL available information from the ENTIRE conversation
2. Include previously extracted information in your response
3. Look for customer name, service type, stylist preference, date, time, email, and phone
4. Return null only for fields that were NEVER mentioned in the conversation
5. Keep previously extracted values if they're not updated in new messages
6. If user mentions MULTIPLE services, pick the PRIMARY/FIRST one mentioned as a STRING (not a list)
7. For incomplete email domains, add .com as default (e.g., "regiment" → "regiment.com")
8. Always return service_type as a STRING, never as an array

Service types: Haircut, Hair Coloring, Styling, Spa Treatment
Stylists: Riya, Maya, Sarah, Alex
Time format: Use 12-hour format with AM/PM (e.g., 11:00 AM)

Return format example:
{{
  "customer_name": "John Smith",
  "service_type": "Haircut",
  "preferred_stylist": "Riya",
  "date": "Monday",
  "time": "10:00 AM",
  "email": "john@gmail.com",
  "phone": null
}}
"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data extraction assistant. Extract appointment information accurately from the ENTIRE conversation, handling speech-to-text variations. Convert email addresses properly (e.g., 'at the rate' → '@', 'dot' → '.'). Include ALL information mentioned anywhere in the conversation. Return valid JSON with all available fields."
                    },
                    {
                        "role": "user",
                        "content": extraction_prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1  # Low temperature for consistent extraction
            )
            
            # Parse the JSON response
            extracted_data = json.loads(response.choices[0].message.content)
            logger.info(f"Raw LLM extraction response: {extracted_data}")
            
            # Clean and validate the extracted data
            metadata = {}
            
            if extracted_data.get("customer_name"):
                name = extracted_data["customer_name"]
                if isinstance(name, str):
                    metadata["customer_name"] = name.strip().title()
            
            if extracted_data.get("service_type"):
                service = extracted_data["service_type"]
                # Handle both string and list (user might request multiple services)
                if isinstance(service, list):
                    # Take the first service or join them
                    metadata["service_type"] = service[0].strip().title() if service else None
                elif isinstance(service, str):
                    metadata["service_type"] = service.strip().title()
            
            if extracted_data.get("preferred_stylist") or extracted_data.get("stylist"):
                stylist = extracted_data.get("preferred_stylist") or extracted_data.get("stylist")
                if isinstance(stylist, str):
                    metadata["preferred_stylist"] = stylist.strip().title()
                elif isinstance(stylist, dict):
                    # If LLM returns nested structure, take the first value
                    for key, value in stylist.items():
                        if isinstance(value, str):
                            metadata["preferred_stylist"] = value.strip().title()
                            break
            
            if extracted_data.get("date"):
                date = extracted_data["date"]
                if isinstance(date, str):
                    metadata["date"] = date.strip().title()
            
            if extracted_data.get("time"):
                time = extracted_data["time"]
                if isinstance(time, str):
                    metadata["time"] = time.strip()
            
            if extracted_data.get("email"):
                # More lenient email validation - handle incomplete domains
                email = extracted_data["email"].strip().lower()
                
                # Basic check: has @ and at least one character on each side
                if "@" in email and len(email.split("@")) == 2:
                    local, domain = email.split("@")
                    if local and domain:
                        # If domain looks incomplete (no dot), try to fix common patterns
                        if "." not in domain:
                            # Common speech-to-text errors
                            domain_fixes = {
                                "gmail": "gmail.com",
                                "yahoo": "yahoo.com",
                                "hotmail": "hotmail.com",
                                "outlook": "outlook.com",
                                "theregiment": "theregiment.com",  # Assume .com for unclear domains
                                "regiment": "regiment.com"
                            }
                            domain = domain_fixes.get(domain, f"{domain}.com")
                        
                        metadata["email"] = f"{local}@{domain}"
                        logger.info(f"Email extracted and cleaned: {metadata['email']}")
            
            if extracted_data.get("phone"):
                phone = extracted_data["phone"]
                if isinstance(phone, str):
                    metadata["phone"] = phone.strip()
            
            logger.info(f"LLM extracted metadata: {metadata}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error in LLM metadata extraction: {e}")
            return {}
