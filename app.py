import streamlit as st
from google import genai
from google.genai import types
import json
import re
import time
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURATION & STATE ---
st.set_page_config(
    page_title="Avanse Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant", 
        "content": "Namaste! I am your **Avanse Education Expert**.\n\nI can help you with **Education Loans**, **University ROI**, and **Visa Processes** for countries like USA, UK, Canada, and Germany.\n\nHow can I assist your study abroad journey today?"
    }]
if "lead_stage" not in st.session_state:
    st.session_state.lead_stage = "browsing" # browsing, capturing, verifying, completed
if "lead_data" not in st.session_state:
    st.session_state.lead_data = {}
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ["💰 Loan Eligibility Calculator", "🇺🇸 USA Visa Trends 2025", "📉 Interest Rates for Germany"]

# --- 2. PREMIUM CSS (iOS / Glassmorphism Design) ---
st.markdown("""
<style>
    /* GLOBAL FONTS & COLORS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&display=swap');
    
    :root {
        --primary: #004aad; /* Avanse Blue */
        --secondary: #ff6b00; /* Accent Orange */
        --bg-color: #f8f9fa;
        --glass: rgba(255, 255, 255, 0.85);
        --shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
    }

    .stApp {
        background-color: var(--bg-color);
        font-family: 'Inter', sans-serif;
    }

    /* HEADER */
    .header-overlay {
        position: fixed; top: 0; left: 0; width: 100%;
        background: rgba(255,255,255,0.9);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(0,0,0,0.05);
        z-index: 9999; padding: 15px 0; text-align: center;
    }
    .header-title { font-size: 20px; font-weight: 800; color: var(--primary); letter-spacing: -0.5px; }
    .header-subtitle { font-size: 11px; color: #666; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; }

    /* CHAT BUBBLES - iMessage Style */
    div[data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 10px 0 !important; }
    
    /* User Bubble */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) div[data-testid="stMarkdownContainer"] {
        background: linear-gradient(135deg, #004aad 0%, #003380 100%);
        color: white !important;
        border-radius: 20px 20px 4px 20px;
        padding: 14px 20px;
        box-shadow: 0 4px 15px rgba(0, 74, 173, 0.2);
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) p { color: white !important; }

    /* Assistant Bubble */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) div[data-testid="stMarkdownContainer"] {
        background: white;
        color: #1a1a1a;
        border-radius: 20px 20px 20px 4px;
        padding: 14px 24px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
        border: 1px solid rgba(0,0,0,0.05);
    }

    /* LEAD FORM CARD (Glassmorphism) */
    .lead-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border: 1px solid white;
        border-radius: 20px;
        padding: 25px;
        box-shadow: var(--shadow);
        margin: 20px 0;
        animation: slideIn 0.5s ease;
    }

    @keyframes slideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

    /* INPUT FIELDS */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 12px !important;
        border: 1px solid #e0e0e0 !important;
        padding: 10px !important;
        font-size: 14px !important;
    }
    .stTextInput input:focus { border-color: var(--primary) !important; box-shadow: 0 0 0 2px rgba(0,74,173,0.1) !important; }

    /* BUTTONS */
    .stButton button {
        border-radius: 30px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    /* Primary CTA */
    div[data-testid="stHorizontalBlock"] button {
        background: white; border: 1px solid #ddd; color: #444;
    }
    div[data-testid="stHorizontalBlock"] button:hover {
        border-color: var(--primary); color: var(--primary);
    }

    /* SOURCES & VIDEO */
    .source-pill {
        display: inline-block; background: #f1f3f5; color: #555;
        font-size: 11px; padding: 4px 12px; border-radius: 20px;
        margin-right: 6px; margin-bottom: 6px; text-decoration: none;
    }
    .source-pill:hover { background: #e9ecef; color: var(--primary); }

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-overlay">
    <div class="header-title">AVANSE <span style="font-weight:400">AI LABS</span></div>
    <div class="header-subtitle">Smart Student Lending</div>
</div>
<div style="height: 80px;"></div> """, unsafe_allow_html=True)

# --- 3. UTILITIES & VALIDATION ---

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    # Basic check for 10-15 digits
    pattern = r'^\+?[0-9]{10,15}$'
    return re.match(pattern, phone) is not None

def get_youtube_id(url):
    regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    match = re.search(regex, url)
    return match.group(1) if match else None

def send_email_mock(email, name, content_type):
    """Simulates sending an email via SMTP"""
    with st.spinner(f"Sending {content_type} to {email}..."):
        time.sleep(1.5) # Simulate network delay
    return True

# --- 4. GEMINI ENGINE ---

try:
    # SECURELY ACCESS API KEY
    api_key = st.secrets["GEMINI_API_KEY"] 
    client = genai.Client(api_key=api_key)
except:
    st.error("⚠️ System Error: API Key not found. Please check secrets.")
    st.stop()

def get_ai_response(query, history):
    system_prompt = """
    You are the Senior Education Loan Counselor for Avanse Financial Services.
    
    TONE: Professional, Empathetic, Encouraging, and Data-Driven.
    
    OBJECTIVES:
    1. Answer questions about studying abroad (Visas, Costs, Universities).
    2. Suggest Avanse's loan products subtly (100% finance, quick sanction).
    3. SEARCH: Use Google Search for 2024/2025 statistics.
    
    OUTPUT FORMAT (JSON ONLY):
    {
        "answer": "Markdown formatted answer with bullet points.",
        "trigger_lead_gen": boolean (Set true if user shows high intent: asks for quote, loan application, or detailed cost breakdown),
        "next_questions": ["Short Q1", "Short Q2"],
        "videos": ["YouTube URL 1"]
    }
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=f"History: {history}\nUser Query: {query}",
            config=types.GenerateContentConfig(
                temperature=0.3,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                system_instruction=system_prompt,
                response_mime_type="application/json"
            )
        )
        
        # Parse Response
        try:
            res_json = json.loads(response.text)
        except:
            # Fallback if raw text
            res_json = {"answer": response.text, "trigger_lead_gen": False, "next_questions": [], "videos": []}
            
        # Extract Sources
        sources = []
        if response.candidates[0].grounding_metadata and response.candidates[0].grounding_metadata.grounding_chunks:
             for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
                if chunk.web:
                    sources.append({"title": chunk.web.title, "url": chunk.web.uri})
                    
        return res_json, sources
        
    except Exception as e:
        return {"answer": "I'm currently updating my database. Please ask again in a moment.", "trigger_lead_gen": False}, []

# --- 5. COMPONENT: LEAD CAPTURE FORM (Maker-Checker) ---

def lead_capture_ui():
    if st.session_state.lead_stage == "completed":
        st.success(f"✅ We have your details, {st.session_state.lead_data.get('name')}! An agent will contact you shortly.")
        return

    st.markdown('<div class="lead-card">', unsafe_allow_html=True)
    
    if st.session_state.lead_stage == "browsing" or st.session_state.lead_stage == "capturing":
        st.subheader("🚀 Get Your Personalized Funding Report")
        st.write("Unlock expert guidance and 100% financing options.")
        
        with st.form("lead_gen_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Full Name", value=st.session_state.lead_data.get("name", ""))
            phone = col2.text_input("Phone Number (+91)", value=st.session_state.lead_data.get("phone", ""))
            email = st.text_input("Email Address", value=st.session_state.lead_data.get("email", ""))
            
            c1, c2 = st.columns(2)
            degree = c1.selectbox("Target Degree", ["Masters (MS/MBA)", "Bachelors", "Ph.D", "Diploma"])
            country = c2.selectbox("Target Country", ["USA", "UK", "Canada", "Germany", "Australia", "Other"])
            
            submitted = st.form_submit_button("Review Details")
            
            if submitted:
                # Validation Logic
                errors = []
                if len(name) < 2: errors.append("Name is too short.")
                if not validate_email(email): errors.append("Invalid Email Address.")
                if not validate_phone(phone): errors.append("Invalid Phone Number.")
                
                if errors:
                    for e in errors: st.error(e)
                else:
                    # Move to Checker Stage
                    st.session_state.lead_data = {
                        "name": name, "email": email, "phone": phone,
                        "degree": degree, "country": country,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.lead_stage = "verifying"
                    st.rerun()

    elif st.session_state.lead_stage == "verifying":
        st.subheader("📋 Confirm Your Details")
        st.info("Please verify the information below to receive your guide.")
        
        data = st.session_state.lead_data
        
        # Display Data (Checker View)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Name:** {data['name']}")
            st.markdown(f"**Email:** {data['email']}")
            st.markdown(f"**Phone:** {data['phone']}")
        with col2:
            st.markdown(f"**Degree:** {data['degree']}")
            st.markdown(f"**Country:** {data['country']}")
        
        btn_col1, btn_col2 = st.columns([1, 1])
        if btn_col1.button("✏️ Edit"):
            st.session_state.lead_stage = "capturing"
            st.rerun()
            
        if btn_col2.button("✅ Submit & Get Guide"):
            # Simulate Email Sending
            success = send_email_mock(data['email'], data['name'], "Avanse Study Guide 2025")
            if success:
                st.session_state.lead_stage = "completed"
                st.balloons()
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. MAIN CHAT LOGIC ---

# Sidebar - Admin View (Simulated)
with st.sidebar:
    st.title("Admin Console")
    st.info("Staff View Only")
    if st.session_state.lead_stage == "completed":
        st.success("🎉 New Lead Captured!")
        st.json(st.session_state.lead_data)
    else:
        st.write("No active lead yet.")
        
    if st.button("Reset Demo"):
        st.session_state.lead_stage = "browsing"
        st.session_state.lead_data = {}
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()

# Container for Chat History
chat_container = st.container()

# Render History
with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # Show Sources if available
            if msg.get("sources"):
                html = "<div style='margin-top:5px;'>"
                for s in msg["sources"][:3]:
                    html += f"<a href='{s['url']}' target='_blank' class='source-pill'>🔗 {s['title'][:30]}...</a>"
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)
                
            # Show Videos if available
            if msg.get("videos"):
                cols = st.columns(len(msg["videos"][:2]))
                for idx, v_url in enumerate(msg["videos"][:2]):
                    vid_id = get_youtube_id(v_url)
                    if vid_id:
                        cols[idx].image(f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg", use_container_width=True)
                        cols[idx].caption(f"[Watch on YouTube]({v_url})")

# Render Lead Form if triggered or manually opened
if st.session_state.lead_stage != "browsing" and st.session_state.lead_stage != "completed":
    lead_capture_ui()

# Suggestion Dock
st.markdown("---")
if st.session_state.lead_stage == "browsing":
    cols = st.columns(len(st.session_state.suggestions))
    for i, sugg in enumerate(st.session_state.suggestions):
        if cols[i].button(sugg, key=f"sug_{i}"):
            # Handle suggestion click
            st.session_state.messages.append({"role": "user", "content": sugg})
            st.rerun()

# Input Handling
if prompt := st.chat_input("Ask about loans, visas, or universities..."):
    # 1. User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Get AI Response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing financial data..."):
            # Context window (last 3 messages)
            history_txt = "\n".join([m['content'] for m in st.session_state.messages[-3:]])
            
            data, sources = get_ai_response(prompt, history_txt)
            
            # Display response
            st.markdown(data["answer"])
            
            # Check intent for Lead Gen
            if data.get("trigger_lead_gen", False) and st.session_state.lead_stage == "browsing":
                st.session_state.lead_stage = "capturing"
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": data["answer"], 
                    "sources": sources,
                    "videos": data.get("videos")
                })
                st.rerun()
                
    # 3. Update State
    st.session_state.messages.append({
        "role": "assistant", 
        "content": data["answer"], 
        "sources": sources,
        "videos": data.get("videos", [])
    })
    
    if data.get("next_questions"):
        st.session_state.suggestions = data["next_questions"]
    
    st.rerun()
