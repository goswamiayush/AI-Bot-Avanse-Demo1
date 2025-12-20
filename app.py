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
        "content": "Namaste! I am your **Avanse Education Expert**.\n\nI can help you with **Education Loans**, **University ROI**, and **Visa Processes**.\n\nHow can I assist you today?"
    }]
if "lead_stage" not in st.session_state:
    st.session_state.lead_stage = "browsing" 
if "lead_data" not in st.session_state:
    st.session_state.lead_data = {}
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ["💰 Loan Eligibility Calculator", "🇺🇸 USA Visa Trends 2025", "📉 Interest Rates for Germany"]

# --- 2. CSS STYLING (Kept the same) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&display=swap');
    :root { --primary: #004aad; --bg-color: #f8f9fa; }
    .stApp { background-color: var(--bg-color); font-family: 'Inter', sans-serif; }
    
    /* Header */
    .header-overlay {
        position: fixed; top: 0; left: 0; width: 100%;
        background: rgba(255,255,255,0.95); backdrop-filter: blur(10px);
        border-bottom: 1px solid #eee; z-index: 999; padding: 15px 0; text-align: center;
    }
    
    /* Chat Bubbles */
    div[data-testid="stChatMessage"] { background: transparent !important; border: none !important; }
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) div[data-testid="stMarkdownContainer"] {
        background: #004aad; color: white; border-radius: 20px 20px 4px 20px; padding: 12px 18px;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) p { color: white !important; }
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) div[data-testid="stMarkdownContainer"] {
        background: white; border: 1px solid #eee; border-radius: 20px 20px 20px 4px; padding: 12px 18px;
    }

    /* Buttons */
    .stButton button { border-radius: 30px !important; border: 1px solid #ddd; transition: all 0.2s; }
    .stButton button:hover { border-color: #004aad; color: #004aad; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-overlay">
    <div style="font-size: 20px; font-weight: 800; color: #004aad;">AVANSE <span style="font-weight:400">AI LABS</span></div>
</div>
<div style="height: 80px;"></div>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def get_youtube_id(url):
    regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    match = re.search(regex, url)
    return match.group(1) if match else None

# CALLBACK FUNCTION: This fixes the "Stuck" issue
def handle_suggestion_click(suggestion_text):
    """Adds the clicked suggestion to chat history immediately."""
    st.session_state.messages.append({"role": "user", "content": suggestion_text})

# --- 4. GEMINI ENGINE ---
try:
    api_key = st.secrets["GEMINI_API_KEY"] 
    client = genai.Client(api_key=api_key)
except:
    st.error("⚠️ API Key missing in Streamlit Secrets.")
    st.stop()

# --- REPLACEMENT FUNCTION ---

def clean_json_text(text):
    """Removes markdown code blocks (e.g. ```json ... ```) to extract raw JSON string."""
    # Remove code block markers
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    return text.strip()

def get_ai_response(query, history):
    system_prompt = """
    You are an Expert Education Counselor for Avanse.
    
    INSTRUCTIONS:
    1. Search Google for the latest 2024/2025 data if needed.
    2. Output your response purely as a JSON object. Do not add conversational filler outside the JSON.
    
    JSON SCHEMA:
    { 
        "answer": "Your formatted answer here (use Markdown for bold/lists).", 
        "trigger_lead_gen": false, 
        "next_questions": ["Short Question 1", "Short Question 2"], 
        "videos": ["YouTube URL"] 
    }
    """
    
    try:
        # call the API without strict JSON enforcement
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=f"History: {history}\nUser Query: {query}",
            config=types.GenerateContentConfig(
                temperature=0.3,
                tools=[types.Tool(google_search=types.GoogleSearch())], # Tool kept
                system_instruction=system_prompt,
                # response_mime_type="application/json"  <-- REMOVED THIS LINE
            )
        )
        
        # Manually clean and parse the text
        raw_text = response.text
        cleaned_text = clean_json_text(raw_text)
        
        return json.loads(cleaned_text)
        
    except json.JSONDecodeError:
        # Fallback if the model returns plain text instead of JSON
        return {
            "answer": response.text, 
            "trigger_lead_gen": False, 
            "next_questions": ["Tell me about loans", "Visa process"],
            "videos": []
        }
    except Exception as e:
        return {"answer": f"I encountered a connection error. ({str(e)})", "trigger_lead_gen": False}

# --- 5. UI LAYOUT ---

# A. Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("videos"):
            for v in msg["videos"][:1]:
                vid_id = get_youtube_id(v)
                if vid_id: st.image(f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg", width=200)

# B. Render Lead Form (Simplified for robustness)
if st.session_state.lead_stage == "capturing":
    with st.chat_message("assistant"):
        with st.form("lead_form"):
            st.subheader("Get Your Funding Report")
            name = st.text_input("Name")
            email = st.text_input("Email")
            if st.form_submit_button("Submit Details"):
                if "@" in email:
                    st.session_state.lead_stage = "completed"
                    st.success("Details received! We will contact you.")
                    st.rerun()
                else:
                    st.error("Invalid Email")

# C. Render Suggestions (THE FIX IS HERE)
if st.session_state.lead_stage == "browsing" and st.session_state.messages[-1]["role"] != "user":
    st.markdown("---")
    cols = st.columns(len(st.session_state.suggestions))
    for i, sugg in enumerate(st.session_state.suggestions):
        # We use on_click callback instead of checking 'if button:'
        cols[i].button(
            sugg, 
            key=f"btn_{len(st.session_state.messages)}_{i}", 
            on_click=handle_suggestion_click, 
            args=(sugg,)
        )

# D. Render Chat Input
if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# --- 6. AI LOGIC TRIGGER ---
# This runs automatically if the last message is from the user
if st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            last_user_msg = st.session_state.messages[-1]["content"]
            history_txt = "\n".join([m['content'] for m in st.session_state.messages[-3:-1]])
            
            data = get_ai_response(last_user_msg, history_txt)
            
            st.markdown(data.get("answer", "No response generated."))
            
            # Update State
            st.session_state.messages.append({
                "role": "assistant", 
                "content": data.get("answer", ""), 
                "videos": data.get("videos", [])
            })
            
            if data.get("next_questions"):
                st.session_state.suggestions = data["next_questions"]
            
            if data.get("trigger_lead_gen"):
                st.session_state.lead_stage = "capturing"
            
            st.rerun()
