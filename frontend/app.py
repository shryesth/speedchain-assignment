import streamlit as st
import requests
import json
from datetime import datetime
import asyncio
import websockets
from audio_recorder_streamlit import audio_recorder

st.set_page_config(
    page_title="Gloss and Glow AI Receptionist",
    page_icon=":scissors:",
    layout="wide"
)

st.markdown("""
<style>
.main-header {
    text-align: center;
    color: #ff69b4;
    font-size: 3em;
    margin-bottom: 20px;
}
.salon-info {
    background-color: #f0f8ff;
    padding: 20px;
    border-radius: 10px;
    margin: 20px 0;
    color: #1a1a1a;
}
.chat-message {
    padding: 10px;
    margin: 5px 0;
    border-radius: 5px;
    color: #1a1a1a;
}
.user-message {
    background-color: #e1f5fe;
    text-align: right;
    color: #0d47a1;
    border-left: 4px solid #2196f3;
}
.assistant-message {
    background-color: #f1f8e9;
    color: #2e7d32;
    border-left: 4px solid #66bb6a;
}
</style>
""", unsafe_allow_html=True)

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "client_id" not in st.session_state:
    st.session_state.client_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

BACKEND_URL = "http://localhost:8000"
WS_URL = f"ws://localhost:8000/ws/{st.session_state.client_id}"

async def send_text_to_backend(user_text):
    try:
        # Increase timeouts for LLM processing
        async with websockets.connect(
            WS_URL,
            ping_timeout=60,
            close_timeout=20,
            ping_interval=20
        ) as websocket:
            # First, receive and skip the initial greeting
            try:
                for _ in range(3):
                    greeting_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    if isinstance(greeting_msg, str):
                        try:
                            data = json.loads(greeting_msg)
                            if data.get("type") == "text" and "Welcome" in data.get("content", ""):
                                continue
                        except:
                            pass
            except asyncio.TimeoutError:
                pass
            
            # Now send the text message
            await websocket.send(json.dumps({"text": user_text}))
            
            responses = []
            timeout_count = 0
            max_timeouts = 5  # Increased to wait longer for LLM processing
            
            while timeout_count < max_timeouts:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=20.0)  # Increased timeout for LLM
                    
                    # Check if message is binary (audio) or text (JSON)
                    if isinstance(message, bytes):
                        # Skip binary audio data
                        continue
                    
                    # Try to parse as JSON
                    try:
                        data = json.loads(message)
                        responses.append(data)
                        
                        # If we got the assistant response (not the greeting), we can break
                        if data.get("type") == "text" and data.get("role") == "assistant":
                            if "Welcome" not in data.get("content", ""):
                                break
                            
                    except json.JSONDecodeError:
                        continue
                        
                except asyncio.TimeoutError:
                    timeout_count += 1
            
            # Extract the assistant response
            for resp in reversed(responses):
                if resp.get("type") == "text" and resp.get("role") == "assistant":
                    # Skip greeting
                    if "Welcome" not in resp.get("content", ""):
                        return resp.get("content", "")
            
            return None
            
    except Exception as e:
        st.error(f"Connection error: {str(e)[:100]}")
        return None

async def send_audio_to_backend(audio_bytes):
    try:
        async with websockets.connect(
            WS_URL, 
            ping_timeout=60,      # Keep connection alive for 60 seconds
            close_timeout=20,     # Wait 20 seconds before force-closing
            max_size=10*1024*1024, # 10MB max message size
            ping_interval=20      # Send ping every 20 seconds to keep alive
        ) as websocket:
            try:
                # Wait for greeting messages (text + audio)
                for _ in range(3):  # Greeting usually has 2-3 messages
                    greeting_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    if isinstance(greeting_msg, str):
                        try:
                            data = json.loads(greeting_msg)
                            # Skip greeting messages
                            if data.get("type") == "text" and "Welcome" in data.get("content", ""):
                                continue
                        except:
                            pass
            except asyncio.TimeoutError:
                pass  # No greeting or already consumed
            
            # Now send audio as binary
            await websocket.send(audio_bytes)
            
            responses = []
            user_transcript = None
            assistant_response = None
            response_audio = None
            
            # Wait for multiple messages with much longer timeout for LLM processing
            for i in range(10):  # Try up to 10 times (200 seconds total)
                try:
                    # Wait up to 20 seconds per message (LLM extraction + response takes time)
                    message = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                    
                    # Check if message is binary (audio) or text (JSON)
                    if isinstance(message, bytes):
                        # Only capture audio AFTER we have the assistant response text
                        # This ensures we get the audio that matches the current response
                        if assistant_response:
                            response_audio = message
                            # We have everything, exit
                            break
                        continue
                    
                    # Try to parse as JSON
                    try:
                        data = json.loads(message)
                        responses.append(data)
                        
                        # Collect transcript and response
                        if data.get("type") == "text":
                            if data.get("role") == "user":
                                user_transcript = data.get("content", "")
                            elif data.get("role") == "assistant":
                                # Skip greeting if it comes through
                                if "Welcome" not in data.get("content", ""):
                                    assistant_response = data.get("content", "")
                                # Continue to get audio after this
                                
                    except json.JSONDecodeError:
                        continue
                        
                except asyncio.TimeoutError:
                    # If we have transcript and response but no audio yet, keep waiting
                    if user_transcript and assistant_response and not response_audio and i < 8:
                        continue
                    # If we have at least the response text, return what we have
                    elif assistant_response:
                        break
                    # Otherwise, keep trying
                    continue
            
            return user_transcript, assistant_response, response_audio
            
    except websockets.exceptions.ConnectionClosed as e:
        st.warning(f"Connection closed early: {str(e)[:100]}")
        return None, None, None
    except Exception as e:
        st.error(f"Connection error: {str(e)[:100]}")
        return None, None, None

st.markdown('<h1 class="main-header">Gloss and Glow AI Receptionist</h1>', unsafe_allow_html=True)

with st.container():
    st.markdown("""
    <div class="salon-info">
        <h3>Welcome to Gloss and Glow Hair Salon!</h3>
        <p><strong>Services:</strong> Haircuts, Hair Coloring, Styling, Spa Treatments</p>
        <p><strong>Our Expert Stylists:</strong></p>
        <ul>
            <li>Riya - Haircuts and Styling</li>
            <li>Maya - Hair Coloring and Highlights</li>
            <li>Sarah - Spa Treatments and Hair Care</li>
            <li>Alex - Creative Cuts and Color</li>
        </ul>
        <p><strong>Hours:</strong> Monday-Saturday, 10 AM - 7 PM</p>
    </div>
    """, unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.header("Voice and Text Chat")
    
    # st.info("💡 **Using AI-Powered Extraction**: Our system uses advanced AI to understand your requests, even with speech variations like 'at the rate' for '@' or 'dot' for '.'")
    
    st.subheader("Record Your Voice")
    try:
        audio_bytes = audio_recorder(
            text="Click to record",
            recording_color="#e8b62c",
            neutral_color="#6aa36f",
            icon_name="microphone",
            icon_size="2x",
            pause_threshold=2.0
        )
    except Exception as e:
        st.warning(f"Audio recorder issue: {str(e)[:100]}")
        audio_bytes = None
    
    if audio_bytes:
        with st.spinner("🎤 Processing your voice... (This may take 10-15 seconds)"):
            try:
                # Show progress
                status_placeholder = st.empty()
                status_placeholder.info("🔄 Step 1/4: Transcribing audio...")
                
                # Send audio to backend
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                user_transcript, assistant_response, response_audio = loop.run_until_complete(send_audio_to_backend(audio_bytes))
                loop.close()
                
                if user_transcript:
                    status_placeholder.info("✅ Step 2/4: Transcription complete! Extracting information...")
                    # Add user transcript to conversation with audio
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    st.session_state.conversation_history.append({
                        "role": "user",
                        "content": user_transcript,
                        "timestamp": timestamp,
                        "audio": audio_bytes  # Store user's recorded audio
                    })
                
                if assistant_response:
                    status_placeholder.info("✅ Step 3/4: Generating AI response...")
                    # Add assistant response to conversation with audio
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    st.session_state.conversation_history.append({
                        "role": "assistant",
                        "content": assistant_response,
                        "timestamp": timestamp,
                        "audio": response_audio  # Store assistant's TTS audio
                    })
                    status_placeholder.success("✅ Step 4/4: Voice message processed successfully!")
                    st.balloons()
                else:
                    status_placeholder.error("❌ Failed to get response from backend. Please try again.")
                
            except Exception as e:
                st.error(f"❌ Error processing audio: {str(e)[:200]}")
                st.info("💡 Tip: Make sure the backend is running and try recording again.")
    
    st.markdown("---")
    
    st.subheader("Or Type Your Message")
    text_col, button_col = st.columns([4, 1])
    
    with text_col:
        user_input = st.text_input("Type here:")
    
    with button_col:
        send_clicked = st.button("Send")
    
    if send_clicked and user_input:
        st.session_state.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        
        with st.spinner("AI Receptionist is thinking..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(send_text_to_backend(user_input))
            loop.close()
            
            if response:
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                st.success("Response received!")
            else:
                st.error("Failed to get response from backend")
    
    st.subheader("Conversation History")
    for idx, msg in enumerate(st.session_state.conversation_history):
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>You ({msg['timestamp']}):</strong> {msg['content']}
            </div>
            """, unsafe_allow_html=True)
            
            # Play user's audio if available
            if msg.get("audio"):
                st.audio(msg["audio"], format="audio/wav")
                
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>AI Receptionist ({msg['timestamp']}):</strong> {msg['content']}
            </div>
            """, unsafe_allow_html=True)
            
            # Play assistant's audio if available
            if msg.get("audio"):
                st.audio(msg["audio"], format="audio/mp3")

with col2:
    st.header("Quick Booking")
    
    with st.form("appointment_form"):
        customer_name = st.text_input("Your Name*")
        email = st.text_input("Email*")
        phone = st.text_input("Phone")
        
        service = st.selectbox("Service*", [
            "Haircut",
            "Hair Coloring",
            "Styling",
            "Spa Treatment"
        ])
        
        stylist = st.selectbox("Preferred Stylist", [
            "Any Available",
            "Riya",
            "Maya",
            "Sarah",
            "Alex"
        ])
        
        date = st.date_input("Date")
        time = st.selectbox("Time", [
            "10:00 AM", "11:00 AM", "12:00 PM",
            "2:00 PM", "3:00 PM", "4:00 PM",
            "5:00 PM", "6:00 PM"
        ])
        
        submitted = st.form_submit_button("Book Appointment")
        
        if submitted and customer_name and email:
            try:
                response = requests.post(
                    f"{BACKEND_URL}/schedule-appointment",
                    json={
                        "customer_name": customer_name,
                        "service_type": service,
                        "stylist": stylist,
                        "date": str(date),
                        "time": time,
                        "email": email,
                        "phone": phone
                    }
                )
                
                if response.status_code == 200:
                    st.success("Appointment booked! Check your email for confirmation.")
                else:
                    st.error("Failed to book appointment")
            except Exception as e:
                st.error(f"Backend not connected: {str(e)[:100]}")

with st.sidebar:
    st.header("System Status")
    
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=2)
        if response.status_code == 200:
            st.success("Backend Connected")
        else:
            st.error("Backend Error")
    except:
        st.warning("Backend Offline - Run: python backend/main.py")
    
    st.header("Session Info")
    st.write(f"**Client ID:** {st.session_state.client_id}")
    st.write(f"**Messages:** {len(st.session_state.conversation_history)}")
    
    if st.button("Clear Conversation"):
        st.session_state.conversation_history = []
        st.success("Cleared!")
