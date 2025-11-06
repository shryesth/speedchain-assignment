"""WebSocket routes for real-time voice communication."""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Service instances will be injected
voice_service = None
appointment_service = None
memory_service = None
llm_service = None

def set_services(voice, appointment, memory, llm):
    """Set service instances."""
    global voice_service, appointment_service, memory_service, llm_service
    voice_service = voice
    appointment_service = appointment
    memory_service = memory
    llm_service = llm

# Connection manager for WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def send_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def send_audio(self, audio_data: bytes, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_bytes(audio_data)

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time voice communication.
    Handles audio streaming, STT, LLM processing, and TTS.
    """
    await manager.connect(websocket, client_id)
    
    # Initialize conversation with greeting
    greeting = "Hello! Welcome to Gloss and Glow Hair Salon. I'm your AI receptionist. How can I help you today?"
    
    # Add greeting to memory
    memory_service.add_message(client_id, "assistant", greeting)
    
    # Convert greeting to audio and send
    try:
        greeting_audio = await voice_service.text_to_speech(greeting)
        await manager.send_audio(greeting_audio, client_id)
        await manager.send_message({
            "type": "text",
            "role": "assistant",
            "content": greeting
        }, client_id)
    except Exception as e:
        logger.error(f"Error sending greeting: {e}")
    
    try:
        while True:
            # Receive audio data from client
            data = await websocket.receive()
            
            if "bytes" in data:
                # Audio data received
                audio_data = data["bytes"]
                logger.info(f"Received audio data from {client_id}: {len(audio_data)} bytes")
                
                # Convert speech to text
                transcription = await voice_service.speech_to_text(audio_data)
                
                if transcription:
                    logger.info(f"Transcription: {transcription}")
                    
                    # Add user message to memory
                    memory_service.add_message(client_id, "user", transcription)
                    
                    # Extract metadata using LLM (async)
                    metadata = await memory_service.extract_metadata(client_id, transcription)
                    logger.info(f"Extracted metadata from message: {metadata}")
                    
                    # Send transcription to client
                    await manager.send_message({
                        "type": "text",
                        "role": "user",
                        "content": transcription
                    }, client_id)
                    
                    # Get conversation history
                    history = memory_service.get_conversation_history(client_id)
                    
                    # Generate LLM response
                    llm_response = await llm_service.get_response(transcription, history)
                    
                    # Add assistant response to memory
                    memory_service.add_message(client_id, "assistant", llm_response)
                    
                    # Send text response
                    await manager.send_message({
                        "type": "text",
                        "role": "assistant",
                        "content": llm_response
                    }, client_id)
                    
                    # Convert response to speech
                    response_audio = await voice_service.text_to_speech(llm_response)
                    
                    # Send audio response
                    await manager.send_audio(response_audio, client_id)
                    
                    # Check if appointment booking is needed
                    # Use accumulated user metadata, not just current message metadata
                    user_metadata = memory_service.get_user_metadata(client_id)
                    if await llm_service.should_book_appointment(llm_response, user_metadata):
                        logger.info(f"Booking check - Metadata available: {user_metadata}")
                        required_fields = ["customer_name", "service_type", "email", "date", "time"]
                        missing_fields = [f for f in required_fields if f not in user_metadata]
                        
                        if missing_fields:
                            logger.info(f"Missing fields for booking: {missing_fields}")
                        else:
                            logger.info(f"All fields present! Scheduling appointment...")
                            # Book appointment
                            appointment_result = await appointment_service.schedule_appointment(
                                customer_name=user_metadata["customer_name"],
                                service_type=user_metadata["service_type"],
                                stylist=user_metadata.get("preferred_stylist", "Any Available"),
                                date=user_metadata["date"],
                                time=user_metadata["time"],
                                email=user_metadata["email"],
                                phone=user_metadata.get("phone", "")
                            )
                            logger.info(f"Appointment scheduled: {appointment_result}")
                            
                            await manager.send_message({
                                "type": "appointment_confirmed",
                                "data": appointment_result
                            }, client_id)
                    else:
                        logger.info(f"No booking detected in response")
            
            elif "text" in data:
                # Handle text messages (for testing/fallback)
                text_data = data["text"]
                logger.info(f"Received text from {client_id}: {text_data}")
                
                # Process similar to audio
                memory_service.add_message(client_id, "user", text_data)
                metadata = await memory_service.extract_metadata(client_id, text_data)
                logger.info(f"Extracted metadata from message: {metadata}")
                
                history = memory_service.get_conversation_history(client_id)
                llm_response = await llm_service.get_response(text_data, history)
                memory_service.add_message(client_id, "assistant", llm_response)
                
                # Send text response
                await manager.send_message({
                    "type": "text",
                    "role": "assistant",
                    "content": llm_response
                }, client_id)
                
                # Convert response to speech (same as audio messages)
                response_audio = await voice_service.text_to_speech(llm_response)
                
                # Send audio response
                await manager.send_audio(response_audio, client_id)
                
                # Check if appointment booking is needed (same as audio messages)
                user_metadata = memory_service.get_user_metadata(client_id)
                if await llm_service.should_book_appointment(llm_response, user_metadata):
                    logger.info(f"Booking check - Metadata available: {user_metadata}")
                    required_fields = ["customer_name", "service_type", "email", "date", "time"]
                    missing_fields = [f for f in required_fields if f not in user_metadata]
                    
                    if missing_fields:
                        logger.info(f"Missing fields for booking: {missing_fields}")
                    else:
                        logger.info(f"All fields present! Scheduling appointment...")
                        # Book appointment
                        appointment_result = await appointment_service.schedule_appointment(
                            customer_name=user_metadata["customer_name"],
                            service_type=user_metadata["service_type"],
                            stylist=user_metadata.get("preferred_stylist", "Any Available"),
                            date=user_metadata["date"],
                            time=user_metadata["time"],
                            email=user_metadata["email"],
                            phone=user_metadata.get("phone", "")
                        )
                        logger.info(f"Appointment scheduled: {appointment_result}")
                        
                        await manager.send_message({
                            "type": "appointment_confirmed",
                            "data": appointment_result
                        }, client_id)
                else:
                    logger.info(f"No booking detected in response")
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
        manager.disconnect(client_id)
