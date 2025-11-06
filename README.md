# AI Receptionist Assistant - Gloss & Glow Hair Salon

An intelligent AI receptionist system that handles voice-based customer interactions, maintains conversation context, extracts metadata, and schedules appointments with email confirmations.

## 🎯 Project Overview

This AI receptionist serves **Gloss & Glow Hair Salon**, a fictional hair salon offering:
- **Services**: Haircuts, Hair Coloring, Styling, and Spa Treatments
- **Stylists**: Riya (Haircuts & Styling), Maya (Coloring & Highlights), Sarah (Spa Treatments), Alex (Creative Cuts & Color)
- **Hours**: Monday-Saturday, 10 AM - 7 PM

### Key Features
- 🎤 **Voice-to-Voice Interaction**: Real-time speech-to-text and text-to-speech
- 🧠 **Context-Aware Conversations**: Maintains memory across the conversation
- 📊 **Metadata Extraction**: Automatically extracts customer name, service preferences, date, time, stylist, and email
- 📅 **Appointment Scheduling**: Books appointments and generates meeting links
- ✉️ **Email Confirmations**: Sends appointment confirmation emails with details
- 💬 **Multi-Modal Interface**: Supports both voice and text input

## 🏗️ Architecture

### Technology Stack

**Backend (FastAPI)**
- **Framework**: FastAPI with WebSocket support
- **STT Model**: OpenAI Whisper-1 (Speech-to-Text)
- **LLM**: GPT-4o-mini (Conversational AI & Metadata Extraction)
- **TTS Model**: OpenAI TTS-1 with Nova voice (Text-to-Speech)
- **Email**: aiosmtplib for async email delivery
- **Architecture**: Modular route structure with service injection

**Frontend (Streamlit)**
- **Framework**: Streamlit 1.51.0+
- **Audio Recording**: audio-recorder-streamlit
- **WebSocket Client**: websockets 12.0
- **Real-time Communication**: Async WebSocket connections

### Workflow

```
User Voice Input
    ↓
[STT] Whisper-1 converts speech → text
    ↓
[Memory Service] Uses LLM (GPT-4o-mini) to extract metadata intelligently
    ↓  
    ↓
[LLM] GPT-4o-mini generates contextual response
    ↓
[TTS] OpenAI TTS-1 converts response → audio
    ↓
User receives voice + text response
    ↓
[If booking detected] → Schedule appointment → Send email
```

## 📁 Project Structure

```
speedchain-assignment/
│
├── backend/
│   ├── main.py                    # FastAPI app entry point with service injection
│   ├── requirements.txt           # Python dependencies
│   ├── .env.example              # Environment variables template
│   ├── routes/
│   │   ├── __init__.py           # Route package init
│   │   ├── appointments.py       # Appointment scheduling endpoints
│   │   ├── conversation.py       # Conversation history endpoints
│   │   └── websocket.py          # WebSocket handler (voice/text communication)
│   └── services/
│       ├── voice_service.py      # STT & TTS using OpenAI
│       ├── llm_service.py        # LLM conversation & intelligent metadata extraction
│       ├── memory_service.py     # Conversation memory & context management
│       └── appointment_service.py # Scheduling & email notifications
│
├── frontend/
│   ├── app.py                    # Streamlit UI application
│   └── requirements.txt          # Frontend dependencies
│
├── data/
│   ├── conversations.json        # Stored conversation history
│   └── appointments.json         # Appointment records
│
├── .gitignore
└── README.md                     # This file
```

## 🚀 Setup Instructions

### Prerequisites
- Python 3.9+
- OpenAI API Key
- Gmail account (for email notifications)

### 1. Clone Repository
```bash
git clone https://github.com/shryesth/speedchain-assignment.git
cd speedchain-assignment
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add:
# OPENAI_API_KEY=your_openai_api_key
# GMAIL_USER=your_email@gmail.com
# GMAIL_PASSWORD=your_app_password
```

### 3. Frontend Setup

```bash
cd ../frontend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 4. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
# Backend runs on http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
streamlit run app.py
# Frontend runs on http://localhost:8501
```

## 🎮 Usage

1. **Open Frontend**: Navigate to `http://localhost:8501`
2. **Voice Interaction**:
   - Click the microphone button to record your voice
   - Speak your query (e.g., "Hi, I'd like to book a haircut")
   - The AI will respond with both voice and text
3. **Text Interaction**:
   - Type your message in the text input field
   - Click "Send" to get a text response
4. **Quick Booking**:
   - Use the right-side form to directly book an appointment
5. **View History**:
   - All conversations are displayed with playable audio for both user and assistant

## 🧪 Example Conversation Flow

```
User: "Hello, I'd like to book an appointment"
AI: "Hi! I'd be happy to help you book an appointment. What service are you interested in?"

User: "I want a haircut with Riya at 3 PM tomorrow"
AI: "Great choice! Riya is excellent with haircuts. Can I have your name and email to confirm the booking?"

User: "My name is John and my email is john@example.com"
AI: "Perfect, John! I've scheduled your haircut with Riya for tomorrow at 3 PM. You'll receive a confirmation email with the meeting link shortly."
```

## 🧠 Model Choices & Rationale

### STT: OpenAI Whisper-1
- **Why**: High accuracy, multi-language support, robust to accents
- **Performance**: Fast transcription with good quality

### LLM: GPT-4o-mini

- **Why**: Cost-effective, fast responses, good conversational abilities
- **Context**: Maintains conversation history for coherent interactions
- **Dual Role**: Both conversation generation AND intelligent metadata extraction
- **Extraction**: Uses structured JSON output to extract booking details from natural language

### TTS: OpenAI TTS-1 (Nova Voice)

- **Why**: Natural-sounding voice, low latency
- **Voice Choice**: Nova - friendly and professional tone suitable for receptionist

## 💾 Memory & Metadata Management

### Conversation Memory

- Stores complete message history per user session
- Maintains context across multiple interactions
- Persists to `data/conversations.json`

### Metadata Extraction

Uses **LLM-based intelligent extraction** (GPT-4o-mini) with regex fallback:

- **Customer Name**: Extracted from conversation context using NLP
- **Service Type**: Haircut, Coloring, Styling, Spa Treatment (handles multiple services)
- **Stylist Preference**: Riya, Maya, Sarah, Alex
- **Date**: Today, Tomorrow, or specific weekdays
- **Time**: Time slots from 10 AM to 7 PM
- **Email**: Validates and auto-completes domains (e.g., "gmail" → "gmail.com")

**Key Features:**

- Handles speech-to-text variations: "at the rate" → "@", "dot" → "."
- Accumulates information across conversation turns (uses last 10 messages for context)
- Smart email domain completion for incomplete addresses
- Robust to typos and speech recognition errors
- Structured JSON output with field validation

### Appointment Scheduling
- Generates unique appointment IDs
- Creates Google Meet links (demo format)
- Sends confirmation emails with appointment details
- Stores appointments in `data/appointments.json`

## 📧 Email Configuration

To enable email confirmations:

1. Use a Gmail account
2. Generate an App Password:
   - Go to Google Account → Security → 2-Step Verification → App Passwords
   - Generate password for "Mail"
3. Add to `.env`:
   ```
   GMAIL_USER=your_email@gmail.com
   GMAIL_PASSWORD=your_app_password
   ```

## 🔌 API Endpoints

### WebSocket
- `ws://localhost:8000/ws/{client_id}` - Real-time voice/text communication

### REST Endpoints
- `GET /` - Health check
- `POST /schedule-appointment` - Direct appointment booking
- `GET /appointments` - List all appointments
- `GET /conversation-history/{user_id}` - Get user conversation history

## 🛠️ Development

### Architecture Highlights

**Modular Route Structure:**
- Routes separated into dedicated files (`appointments.py`, `conversation.py`, `websocket.py`)
- Service injection pattern for dependency management
- Clean separation of concerns

**Service Layer:**
- `VoiceService`: Handles STT/TTS operations
- `LLMService`: Manages conversations AND metadata extraction
- `MemoryService`: Conversation context and persistence
- `AppointmentService`: Booking logic and email notifications

### Adding New Services
Edit `backend/services/memory_service.py` to add service keywords:
```python
services = ["haircut", "coloring", "your_new_service"]
```

### Adding New Stylists
Add to the stylists list in `memory_service.py` and update the frontend display.

### Customizing TTS Voice
Modify `backend/services/voice_service.py`:
```python
voice="nova"  # Options: alloy, echo, fable, onyx, nova, shimmer
```

## 🐛 Troubleshooting

**WebSocket Connection Issues:**
- Ensure backend is running on port 8000
- Check firewall settings
- Verify OPENAI_API_KEY is set

**Audio Not Playing:**
- Check browser audio permissions
- Ensure audio format compatibility (wav for user, mp3 for AI)

**Email Not Sending:**
- Verify Gmail credentials in `.env`
- Check App Password is correctly generated
- Ensure 2FA is enabled on Gmail account

## 👨‍💻 Developer

**Name**: Shryesth Pandey  
**Repository**: [speedchain-assignment](https://github.com/shryesth/speedchain-assignment)
