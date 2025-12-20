import streamlit as st
from google import genai
from google.genai import types
import json
import re

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="Avanse AI Labs",
    page_icon="🧬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. ADVANCED CSS OVERRIDES ---
st.markdown("""
<style>
    /* --- FONTS & BASICS --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        background-color: #F5F7FA; /* Light Grey-Blue Background */
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit Default Elements */
    #MainMenu, footer, header {visibility: hidden;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    
    /* --- LAYOUT FIXES --- */
    .block-container {
        padding-top: 7rem !important; /* Space for Header */
        padding-bottom: 12rem !important; /* Space for Input & Chips */
        max-width: 800px;
    }

    /* --- CUSTOM HEADER --- */
    .nav-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid #E0E0E0;
        z-index: 9999;
        padding: 1rem 0;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
    }
    .logo-text {
        color: #003366; /* Avanse Navy */
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .beta-badge {
        background: linear-gradient(135deg, #D4AF37 0%, #F3D467 100%); /* Gold */
        color: #003366;
        font-size: 0.6rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* --- CHAT BUBBLES (THE IMESSAGE LOOK) --- */
    
    /* Remove default Streamlit styling */
    .stChatMessage {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin-bottom: 1rem;
    }
    
    /* Hide Avatars */
    div[data-testid="chatAvatarIcon-user"], div[data-testid="chatAvatarIcon-assistant"] {
        display: none !important;
    }

    /* USER BUBBLE (Right / Blue) */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        flex-direction: row-reverse;
        justify-content: flex-end;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) div[data-testid="stMarkdownContainer"] {
        background: linear-gradient(135deg, #003366 0%, #004488 100%);
        color: white;
        padding: 14px 20px;
        border-radius: 20px 20px 2px 20px; /* Sharp bottom-left */
        box-shadow: 0 4px 10px rgba(0, 51, 102, 0.15);
        margin-left: auto; /* Push to right */
        max-width: 85%;
    }
    /* Force text color in user bubble */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) p {
        color: white !important;
    }

    /* ASSISTANT BUBBLE (Left / White) */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) div[data-testid="stMarkdownContainer"] {
        background-color: #FFFFFF;
        color: #1F2937;
        padding: 14px 20px;
        border-radius: 20px 20px 20px 2px; /* Sharp bottom-right */
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        border: 1px solid #E5E7EB;
        margin-right: auto; /* Push to left */
        max-width: 90%;
    }

    /* --- SOURCE CHIPS --- */
    .source-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid rgba(0,0,0,0.05);
    }
    .source-chip {
        display: inline-flex;
        align-items: center;
        background-color: #F3F4F6;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 4px 10px;
        font-size: 0.7rem;
        color: #4B5563;
        text-decoration: none;
        transition: all 0.2s;
    }
    .source-chip:hover {
        background-color: #E0E7FF;
        color: #003366;
        border-color: #003366;
    }

    /* --- SUGGESTION PILLS (Floating above input) --- */
    .suggestion-area {
        position: fixed;
        bottom: 5rem;
        left: 0;
        width: 100%;
        background: linear-gradient(to top, #F5F7FA 80%, transparent 100%);
        padding: 10px 0;
        z-index: 99;
    }
    .stButton button {
        border-radius: 20px;
        border: 1px solid #D1D5DB;
        background-color: white;
        color: #374151;
        font-size: 0.8rem;
        padding: 0.5rem 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.2s;
        width: 100%; /* Full width in column */
    }
    .stButton button:hover {
        border-color: #003366;
        color: #003366;
        background-color: #F0F5FF;
        transform: translateY(-2px);
    }
    
    /* --- VIDEO CARD --- */
    .video-card-container {
        background: #000;
        border-radius: 12px;
        overflow: hidden;
        margin-top: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

</style>
""", unsafe_allow_html=True)

# --- 3. HEADER HTML ---
st.markdown("""
<div class="nav-header">
    <div class="logo-text">
        AVANSE AI LABS<span class="beta-badge">BETA</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 4. API SETUP ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    # Fallback for local testing if secrets not found
    st.error("⚠️ API Key missing. Please set GEMINI_API_KEY.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- 5. STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your **Avanse Education Expert**. \n\nI can help you check anything on International Studies such as **Visa Acceptance Rates**, **University Fees**, or **Loan Eligibility**. What shall we explore?"}
    ]
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ["Visa acceptance rate for USA", "Tuition fees for MS CS in Germany", "Scholarships for Indians"]

# --- 6. INTELLIGENCE LAYER ---
def extract_data(response):
    text = response.text if response.text else ""
    sources = []
    
    # Extract Sources (Grounding)
    if response.candidates and response.candidates[0].grounding_metadata:
        md = response.candidates[0].grounding_metadata
        if md.grounding_chunks:
            for chunk in md.grounding_chunks:
                if chunk.web:
                    sources.append({"title": chunk.web.title, "url": chunk.web.uri})

    # JSON Parsing Logic
    json_match = re.search(r'(\{.*\})', text, re.DOTALL)
    data = {}
    if json_match:
        try:
            data = json.loads(json_match.group(1))
        except:
            pass 

    answer = data.get("answer")
    next_questions = data.get("next_questions", [])
    videos = data.get("videos", [])

    if not answer:
        # Fallback cleanup if JSON fails
        answer = re.sub(r'next_questions:.*', '', text, flags=re.DOTALL).strip()
        answer = re.sub(r'videos:.*', '', answer, flags=re.DOTALL).strip()
        answer = re.sub(r'```json', '', answer).replace('```', '').strip()

    return answer, next_questions, sources, videos

def format_history(messages):
    return "\n".join([f"{m['role']}: {m['content']}" for m in messages[-4:]])

def get_gemini_response(query, history):
    try:
        system_prompt = f"""
        You are an expert Education Counselor for Avanse Financial Services.
        
        TASK:
        1. Search Google for 2024/2025 data: "{query}"
        2. Context: {history}
        3. OUTPUT: JSON ONLY.
        
        JSON SCHEMA:
        {{
            "answer": "A concise, engaging markdown answer. Use bullet points for lists.",
            "next_questions": ["Short Q1", "Short Q2", "Short Q3"],
            "videos": ["https://www.youtube.com/watch?v=..."] (Find 1 relevant YouTube link if possible)
        }}
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=query,
            config=types.GenerateContentConfig(
                temperature=0.3,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                system_instruction=system_prompt
            )
        )
        return extract_data(response)
    except Exception as e:
        return f"⚠️ Connection Error: {str(e)}", [], [], []

# --- 7. RENDER FUNCTIONS ---

def render_message(msg):
    # This renders the "Bubble"
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Sources Footer
        if msg.get("sources"):
            source_html = '<div class="source-container">'
            for s in msg["sources"][:3]:
                # Truncate title
                title = s["title"][:25] + "..." if len(s["title"]) > 25 else s["title"]
                source_html += f'<a href="{s["url"]}" target="_blank" class="source-chip">🔗 {title}</a>'
            source_html += '</div>'
            st.markdown(source_html, unsafe_allow_html=True)
            
        # Video Card
        if msg.get("videos"):
            for vid_url in msg["videos"]:
                if "youtube.com" in vid_url or "youtu.be" in vid_url:
                    # Clean native player
                    st.markdown('<div class="video-card-container">', unsafe_allow_html=True)
                    st.video(vid_url)
                    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. MAIN UI LOOP ---

# A. Render Chat History
for msg in st.session_state.messages:
    render_message(msg)

# B. Suggestions (Floating Pill Area)
# We use a container that pushes up from the bottom
st.markdown('<div class="suggestion-area">', unsafe_allow_html=True)
selected_suggestion = None

if st.session_state.suggestions:
    # Use columns to create a neat row of buttons
    # We limit to 3 max to prevent "spilling"
    safe_suggestions = st.session_state.suggestions[:3]
    cols = st.columns(len(safe_suggestions))
    for i, suggestion in enumerate(safe_suggestions):
        if cols[i].button(suggestion, key=f"sugg_{len(st.session_state.messages)}_{i}"):
            selected_suggestion = suggestion
st.markdown('</div>', unsafe_allow_html=True)

# C. Input Handling
user_input = st.chat_input("Ask a question...")
if selected_suggestion: user_input = selected_suggestion

# D. Processing
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

if st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        # Minimalist "Thinking" indicator
        with st.status("Thinking...", expanded=False) as status:
            history_text = format_history(st.session_state.messages)
            answer, next_q, sources, videos = get_gemini_response(st.session_state.messages[-1]["content"], history_text)
            status.update(label="Done", state="complete")
        
        # Render the result immediately
        render_message({
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "videos": videos
        })

    # Update Session State
    st.session_state.messages.append({
        "role": "assistant", 
        "content": answer, 
        "sources": sources,
        "videos": videos
    })
    
    if next_q: st.session_state.suggestions = next_q
    st.rerun()
