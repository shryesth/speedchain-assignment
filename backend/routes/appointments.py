"""Appointment-related routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/appointments", tags=["appointments"])

class AppointmentRequest(BaseModel):
    customer_name: str
    service_type: str
    stylist: str
    date: str
    time: str
    email: str
    phone: str = ""

# Service instance will be injected
appointment_service = None

def set_appointment_service(service):
    """Set the appointment service instance."""
    global appointment_service
    appointment_service = service

@router.post("/schedule")
async def schedule_appointment(appointment: AppointmentRequest):
    """REST endpoint to schedule an appointment."""
    try:
        result = await appointment_service.schedule_appointment(
            customer_name=appointment.customer_name,
            service_type=appointment.service_type,
            stylist=appointment.stylist,
            date=appointment.date,
            time=appointment.time,
            email=appointment.email,
            phone=appointment.phone
        )
        return {"status": "scheduled", "appointment_id": result["appointment_id"]}
    except Exception as e:
        logger.error(f"Failed to schedule appointment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
async def get_appointments():
    """Get all appointments."""
    return appointment_service.get_all_appointments()
