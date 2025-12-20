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
        background-color: #F5F7FA;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit Default Elements */
    #MainMenu, footer, header {visibility: hidden;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    
    /* --- LAYOUT FIXES --- */
    .block-container {
        padding-top: 6rem !important;
        padding-bottom: 10rem !important; /* Extra space for fixed suggestions */
        max-width: 800px;
    }

    /* --- CUSTOM HEADER --- */
    .nav-header {
        position: fixed; top: 0; left: 0; width: 100%;
        background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(12px);
        border-bottom: 1px solid #E0E0E0; z-index: 9999;
        padding: 0.8rem 0; display: flex; align-items: center; justify-content: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    }
    .logo-text {
        color: #003366; font-size: 1.2rem; font-weight: 800;
        display: flex; align-items: center; gap: 8px;
    }
    .beta-badge {
        background: #F3F4F6; color: #003366; font-size: 0.6rem;
        font-weight: 700; padding: 2px 6px; border-radius: 4px; border: 1px solid #E5E7EB;
    }

    /* --- CHAT BUBBLES --- */
    .stChatMessage { background-color: transparent !important; border: none !important; padding: 0 !important; margin-bottom: 1rem; }
    div[data-testid="chatAvatarIcon-user"], div[data-testid="chatAvatarIcon-assistant"] { display: none !important; }

    /* USER (Right/Blue) */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        flex-direction: row-reverse; justify-content: flex-end;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) div[data-testid="stMarkdownContainer"] {
        background: #004488; color: white; padding: 12px 18px;
        border-radius: 18px 18px 2px 18px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-left: auto; max-width: 80%;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) p { color: white !important; }

    /* ASSISTANT (Left/White) */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) div[data-testid="stMarkdownContainer"] {
        background-color: #FFFFFF; color: #1F2937; padding: 12px 18px;
        border-radius: 18px 18px 18px 2px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #E5E7EB;
        margin-right: auto; max-width: 90%;
    }

    /* --- SUGGESTION AREA (Fixed Bottom) --- */
    .suggestion-area {
        position: fixed; bottom: 4.5rem; left: 0; width: 100%;
        background: linear-gradient(to top, #F5F7FA 90%, transparent 100%);
        padding: 10px 0; z-index: 99;
        display: flex; justify-content: center;
    }
    /* Buttons */
    .stButton button {
        border-radius: 20px; border: 1px solid #D1D5DB; background-color: white;
        color: #374151; font-size: 0.8rem; padding: 0.4rem 1rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05); transition: all 0.2s;
    }
    .stButton button:hover {
        border-color: #003366; color: #003366; background-color: #F0F5FF; transform: translateY(-1px);
    }
    
    /* --- VIDEO CARDS --- */
    .video-label { font-size: 0.75rem; font-weight: 700; color: #6B7280; text-transform: uppercase; margin-bottom: 8px; margin-top: 15px;}
    
</style>
""", unsafe_allow_html=True)

# --- 3. HEADER ---
st.markdown("""
<div class="nav-header">
    <div class="logo-text">AVANSE AI LABS<span class="beta-badge">BETA</span></div>
</div>
""", unsafe_allow_html=True)

# --- 4. API SETUP ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ API Key missing.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- 5. STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your **Avanse Education Expert**. I can help with **Visa Chances**, **Loan Eligibility**, or **Top Universities**."}
    ]
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ["Visa acceptance rate USA", "Cost of MS in Germany", "Scholarships for Indians"]

# --- 6. INTELLIGENCE LAYER ---
def clean_text(text):
    """Aggressively removes Next Steps or JSON artifacts from the visible answer"""
    # Remove the JSON block if visible
    text = re.sub(r'```json.*?```', '', text, flags=re.DOTALL)
    # Remove "Next Steps:" or "Suggested Questions:" headers that might leak
    text = re.sub(r'\*\*Next Steps.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Next Steps:.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    return text.strip()

def extract_data(response):
    text = response.text if response.text else ""
    sources = []
    
    # 1. Grounding Sources
    if response.candidates and response.candidates[0].grounding_metadata:
        md = response.candidates[0].grounding_metadata
        if md.grounding_chunks:
            for chunk in md.grounding_chunks:
                if chunk.web:
                    sources.append({"title": chunk.web.title, "url": chunk.web.uri})

    # 2. Extract JSON
    data = {}
    json_match = re.search(r'(\{.*\})', text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
        except:
            pass 

    answer = data.get("answer")
    next_questions = data.get("next_questions", [])
    videos = data.get("videos", [])

    # 3. Fallback: If JSON failed, parse text manually
    if not answer:
        answer = clean_text(text)
    
    # 4. Fallback: If Next Questions empty, find questions in text
    if not next_questions:
        # Regex to find lines starting with "1. What..." or "- How..."
        potential_qs = re.findall(r'[1-9\-•]\.?\s*(What|How|Can|Which|Is).*?\?', text)
        if potential_qs:
            next_questions = potential_qs[:3] # Take top 3
        else:
            # Default backup if totally failed
            next_questions = ["Compare Universities", "Visa Fees", "Education Loan Process"]

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
            "answer": "Markdown answer. DO NOT include 'Next Steps' text here.",
            "next_questions": ["Short Q1", "Short Q2", "Short Q3"],
            "videos": ["https://www.youtube.com/watch?v=..."] (Include 1 valid YouTube link only if highly relevant)
        }}
        """
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=query,
            config=types.GenerateContentConfig(
                temperature=0.3,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                system_instruction=system_prompt
            )
        )
        return extract_data(response)
    except Exception as e:
        return f"⚠️ Error: {str(e)}", [], [], []

# --- 7. RENDER FUNCTIONS ---

def render_message(msg):
    with st.chat_message(msg["role"]):
        # Clean the content again just to be safe
        clean_content = clean_text(msg["content"])
        st.markdown(clean_content)
        
        # Sources
        if msg.get("sources"):
            st.markdown("---")
            source_html = ""
            for s in msg["sources"][:3]:
                title = s["title"][:20] + ".." if len(s["title"]) > 20 else s["title"]
                source_html += f'<a href="{s["url"]}" target="_blank" style="font-size:11px; color:#666; text-decoration:none; margin-right:10px; background:#f0f0f0; padding:2px 6px; border-radius:4px;">🔗 {title}</a>'
            st.markdown(source_html, unsafe_allow_html=True)
            
        # Videos (Strict Check)
        if msg.get("videos"):
            valid_videos = [v for v in msg["videos"] if "youtube.com" in v or "youtu.be" in v]
            if valid_videos:
                st.markdown('<div class="video-label">Watch Related</div>', unsafe_allow_html=True)
                # Display only the first valid video to keep it sleek
                st.video(valid_videos[0])

# --- 8. UI LOOP ---

# A. Render History
for msg in st.session_state.messages:
    render_message(msg)

# B. Suggestions (Fixed Bottom)
st.markdown('<div class="suggestion-area">', unsafe_allow_html=True)
selected_suggestion = None

if st.session_state.suggestions:
    # Safely handle columns to avoid grid errors
    count = min(len(st.session_state.suggestions), 3) # Max 3 buttons
    if count > 0:
        cols = st.columns(count)
        for i in range(count):
            if cols[i].button(st.session_state.suggestions[i], key=f"sugg_{len(st.session_state.messages)}_{i}"):
                selected_suggestion = st.session_state.suggestions[i]
st.markdown('</div>', unsafe_allow_html=True)

# C. Input
user_input = st.chat_input("Ask about universities, loans, or visas...")
if selected_suggestion: user_input = selected_suggestion

# D. Logic
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

if st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.status("Analysing...", expanded=False) as status:
            history_text = format_history(st.session_state.messages)
            answer, next_q, sources, videos = get_gemini_response(st.session_state.messages[-1]["content"], history_text)
            status.update(label="Complete", state="complete")
        
        render_message({
            "role": "assistant", "content": answer, "sources": sources, "videos": videos
        })

    st.session_state.messages.append({
        "role": "assistant", "content": answer, "sources": sources, "videos": videos
    })
    
    # Force update suggestions if valid ones exist
    if next_q and len(next_q) > 0:
        st.session_state.suggestions = next_q
    
    st.rerun()
