import json
import os
import uuid
import aiosmtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List

class AppointmentService:
    """Service for managing appointments and sending email confirmations."""
    
    def __init__(self, data_file: str = "../data/appointments.json"):
        self.data_file = data_file
        self.appointments = self._load_appointments()
        self.gmail_user = os.getenv("GMAIL_USER")
        self.gmail_password = os.getenv("GMAIL_PASSWORD")

    def _load_appointments(self) -> Dict[str, Any]:
        """Load appointments from JSON file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _save_appointments(self):
        """Save appointments to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w') as f:
                json.dump(self.appointments, f, indent=2)
        except Exception as e:
            print(f"Error saving appointments: {e}")

    async def schedule_appointment(self, customer_name: str, service_type: str,
                                  stylist: str, date: str, time: str,
                                  email: str, phone: str = "") -> Dict[str, Any]:
        """Schedule appointment and send confirmation email."""
        
        appointment_id = str(uuid.uuid4())
        
        appointment = {
            "id": appointment_id,
            "customer_name": customer_name,
            "service_type": service_type,
            "stylist": stylist,
            "date": date,
            "time": time,
            "email": email,
            "phone": phone,
            "status": "confirmed",
            "created_at": datetime.now().isoformat(),
            "meeting_link": f"https://meet.google.com/demo-{appointment_id[:8]}"
        }
        
        self.appointments[appointment_id] = appointment
        self._save_appointments()
        
        await self._send_confirmation_email(appointment)
        
        return {"appointment_id": appointment_id, "status": "scheduled"}

    async def _send_confirmation_email(self, appointment: Dict[str, Any]):
        """Send appointment confirmation email asynchronously."""
        try:
            subject = f"Appointment Confirmation - {appointment['service_type']} at Gloss & Glow"
            
            body = f"""
Dear {appointment['customer_name']},

Your appointment has been confirmed! Here are the details:

🌟 APPOINTMENT DETAILS 🌟
Service: {appointment['service_type']}
Stylist: {appointment['stylist']}
Date: {appointment['date']}
Time: {appointment['time']}

📍 Location: Gloss & Glow Hair Salon

💻 Virtual Consultation: {appointment['meeting_link']}

We look forward to serving you!

Best regards,
The Gloss & Glow Team
"""

            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = appointment['email']
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            if self.gmail_user and self.gmail_password:
                await aiosmtplib.send(
                    msg,
                    hostname="smtp.gmail.com",
                    port=587,
                    start_tls=True,
                    username=self.gmail_user,
                    password=self.gmail_password
                )
                print(f"Confirmation email sent to {appointment['email']}")
            else:
                print("Email credentials not configured")
                
        except Exception as e:
            print(f"Error sending email: {e}")

    def get_all_appointments(self) -> List[Dict[str, Any]]:
        """Get all appointments."""
        return list(self.appointments.values())
