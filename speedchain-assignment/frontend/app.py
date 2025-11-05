import streamlit as st
import requests
import json
from datetime import datetime
import asyncio
import websockets
from audio_recorder_streamlit import audio_recorder
import base64

st.set_page_config(
    page_title="Gloss & Glow AI Receptionist",
    page_icon="💇‍♀️",
    layout="wide"
)

# Custom CSS
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
    }
    .chat-message {
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
    .user-message {
        background-color: #e1f5fe;
        text-align: right;
    }
    .assistant-message {
        background-color: #f1f8e9;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'client_id' not in st.session_state:
    st.session_state.client_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Backend URL
BACKEND_URL = "http://localhost:8000"
WS_URL = f"ws://localhost:8000/ws/{st.session_state.client_id}"

# Main header
st.markdown('<h1 class="main-header">💇‍♀️ Gloss & Glow AI Receptionist</h1>', unsafe_allow_html=True)

# Salon information
with st.container():
    st.markdown("""
    <div class="salon-info">
        <h3>Welcome to Gloss & Glow Hair Salon! ✨</h3>
        <p><strong>Services:</strong> Haircuts, Hair Coloring, Styling, Spa Treatments</p>
        <p><strong>Our Expert Stylists:</strong></p>
        <ul>
            <li>🌟 Riya - Haircuts & Styling</li>
            <li>🎨 Maya - Hair Coloring & Highlights</li>
            <li>💆 Sarah - Spa Treatments & Hair Care</li>
            <li>✂️ Alex - Creative Cuts & Color</li>
        </ul>
        <p><strong>Hours:</strong> Monday-Saturday, 10 AM - 7 PM</p>
    </div>
    """, unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 Voice & Text Chat")
    
    # Audio recorder
    st.subheader("🎤 Record Your Voice")
    audio_bytes = audio_recorder(
        text="Click to record",
        recording_color="#e8b62c",
        neutral_color="#6aa36f",
        icon_name="microphone",
        icon_size="2x",
        pause_threshold=2.0
    )
    
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        
        # Send audio to backend
        with st.spinner("Processing your voice..."):
            try:
                # Convert to base64 for WebSocket
                audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                
                # Add user message placeholder
                st.session_state.conversation_history.append({
                    "role": "user",
                    "content": "[Voice message]",
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
                # Simulate AI response (replace with actual WebSocket call)
                response = "I heard your message! How can I help you schedule an appointment?"
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
                st.success("✅ Voice message processed!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error processing audio: {e}")
    
    st.markdown("---")
    
    # Text chat
    st.subheader("💬 Or Type Your Message")
    user_input = st.text_input("Type here:", key="text_input")
    
    if st.button("Send Text Message"):
        if user_input:
            # Add to conversation
            st.session_state.conversation_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            
            # Simulate response (replace with actual WebSocket/API call)
            response = f"Thank you for your message! Let me help you with: '{user_input}'"
            st.session_state.conversation_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            st.rerun()
    
    # Display conversation
    st.subheader("📜 Conversation History")
    for msg in st.session_state.conversation_history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>You ({msg['timestamp']}):</strong> {msg['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>AI Receptionist ({msg['timestamp']}):</strong> {msg['content']}
            </div>
            """, unsafe_allow_html=True)

with col2:
    st.header("📅 Quick Booking")
    
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
        
        submitted = st.form_submit_button("📅 Book Appointment")
        
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
                    st.success("✅ Appointment booked! Check your email for confirmation.")
                else:
                    st.error("Failed to book appointment")
            except:
                st.error("Backend not connected")

# Sidebar
with st.sidebar:
    st.header("🔧 System Status")
    
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=2)
        if response.status_code == 200:
            st.success("✅ Backend Connected")
        else:
            st.error("❌ Backend Error")
    except:
        st.warning("⚠️ Backend Offline - Run: `python backend/main.py`")
    
    st.header("📊 Session Info")
    st.write(f"**Client ID:** {st.session_state.client_id}")
    st.write(f"**Messages:** {len(st.session_state.conversation_history)}")
    
    if st.button("🗑️ Clear Conversation"):
        st.session_state.conversation_history = []
        st.success("Cleared!")
        st.rerun()
