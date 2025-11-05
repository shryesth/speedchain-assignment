import logging
import os
from typing import List, Dict, Any
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

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
            "i've scheduled", "i've booked", "all set"
        ]
        
        response_lower = llm_response.lower()
        has_booking_phrase = any(phrase in response_lower for phrase in booking_phrases)
        
        # Check if we have all required information
        required_fields = ["customer_name", "service_type", "email", "date", "time"]
        has_all_info = all(field in metadata for field in required_fields)
        
        return has_booking_phrase and has_all_info
