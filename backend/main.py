import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from services.voice_service import VoiceService
from services.appointment_service import AppointmentService
from services.memory_service import MemoryService
from services.llm_service import LLMService

# Import routes
from routes import appointments, conversation, websocket

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Receptionist API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
voice_service = VoiceService()
appointment_service = AppointmentService()
memory_service = MemoryService()
llm_service = LLMService()

# Set up service dependencies
memory_service.set_llm_service(llm_service)  # Enable LLM-based metadata extraction

# Inject services into routes
appointments.set_appointment_service(appointment_service)
conversation.set_memory_service(memory_service)
websocket.set_services(voice_service, appointment_service, memory_service, llm_service)

# Include routers
app.include_router(appointments.router)
app.include_router(conversation.router)

@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "message": "AI Receptionist API is running",
        "timestamp": datetime.now().isoformat()
    }

@app.websocket("/ws/{client_id}")
async def websocket_handler(ws: WebSocket, client_id: str):
    """WebSocket endpoint - delegates to websocket route handler."""
    await websocket.websocket_endpoint(ws, client_id)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True
    )
