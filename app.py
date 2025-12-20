import streamlit as st
from google import genai
from google.genai import types
import json
import re

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Avanse AI Labs",
    page_icon="🧬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. THE "NUCLEAR" CSS FIX ---
st.markdown("""
<style>
    /* GLOBAL RESET */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    .stApp {
        background-color: #F2F2F7;
        font-family: 'Inter', sans-serif;
    }
    
    /* HIDE DEFAULT ELEMENTS */
    #MainMenu, footer, header {visibility: hidden;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    
    /* INPUT BOX FIX (Prevent Overlap) */
    .block-container {
        padding-top: 6rem !important;
        padding-bottom: 15rem !important; /* Huge padding to ensure input never covers text */
        max-width: 750px;
    }

    /* --- CHAT BUBBLES: AGGRESSIVE OVERRIDE --- */
    
    /* 1. Reset the outer container */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin-bottom: 1.5rem !important;
        display: flex !important;
        flex-direction: column !important;
    }

    /* 2. Hide Default Avatars */
    [data-testid="chatAvatarIcon-user"], [data-testid="chatAvatarIcon-assistant"] {
        display: none !important;
    }

    /* 3. USER BUBBLE (Blue/Right) - USING :HAS SELECTOR */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        align-items: flex-end !important; /* Force Right Align */
    }
    
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] {
        background-color: #007AFF !important;
        color: #ffffff !important;
        padding: 12px 18px !important;
        border-radius: 20px 20px 4px 20px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
        max-width: 80% !important;
        text-align: left !important;
    }
    
    /* Force Text Color White */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) li {
        color: #ffffff !important;
    }

    /* 4. ASSISTANT BUBBLE (White/Left) */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        align-items: flex-start !important; /* Force Left Align */
    }
    
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        padding: 14px 20px !important;
        border-radius: 20px 20px 20px 4px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important;
        max-width: 90% !important;
        border: 1px solid rgba(0,0,0,0.05) !important;
    }

    /* --- SOURCE CARDS (Simple & Safe) --- */
    .source-box {
        display: inline-flex;
        align-items: center;
        background: #F9F9F9;
        border: 1px solid #E5E5EA;
        border-radius: 8px;
        padding: 6px 10px;
        margin: 4px;
        text-decoration: none !important;
        color: #333 !important;
        font-size: 11px;
        transition: all 0.2s;
    }
    .source-box:hover {
        background: #EBF3FF;
        border-color: #007AFF;
    }
    .source-icon { margin-right: 5px; }

    /* --- SUGGESTION PILLS --- */
    .suggestion-container {
        position: fixed;
        bottom: 5rem;
        left: 0;
        width: 100%;
        background: linear-gradient(to top, #F2F2F7 80%, transparent 100%);
        padding: 15px 0;
        z-index: 9999;
        display: flex;
        justify-content: center;
        gap: 8px;
    }
    .stButton button {
        border-radius: 20px !important;
        border: 1px solid #C7C7CC !important;
        background-color: white !important;
        color: #007AFF !important;
        font-size: 12px !important;
        padding: 8px 16px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    .stButton button:hover {
        background-color: #007AFF !important;
        color: white !important;
    }

</style>
""", unsafe_allow_html=True)

# --- 3. HEADER ---
st.markdown("""
<div style="position:fixed; top:0; left:0; width:100%; background:rgba(255,255,255,0.95); padding:1rem; border-bottom:1px solid #E5E5EA; z-index:10000; text-align:center; backdrop-filter:blur(10px);">
    <div style="display:flex; align-items:center; justify-content:center; gap:8px;">
        <span style="font-size:18px; font-weight:800; color:#003366;">AVANSE AI LABS</span>
        <span style="background:#FFD700; color:#003366; font-size:9px; font-weight:700; padding:2px 6px; border-radius:4px;">BETA</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 4. API SETUP ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ API Key missing.")
    st.stop()

client = genai.Client(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your **Avanse Education Expert**."}]
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ["Visa Acceptance USA", "Tuition Fees Germany", "Scholarships"]

# --- 5. LOGIC ENGINE ---
def clean_text(text):
    text = re.sub(r'```json.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'Next Steps:.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    return text.strip()

def validate_video(url):
    if not url: return False
    return "youtube.com" in url or "youtu.be" in url

def extract_data(response):
    text = response.text if response.text else ""
    sources = []
    
    # Grounding
    if response.candidates and response.candidates[0].grounding_metadata:
        md = response.candidates[0].grounding_metadata
        if md.grounding_chunks:
            for chunk in md.grounding_chunks:
                if chunk.web:
                    sources.append({"title": chunk.web.title, "url": chunk.web.uri})

    # JSON Parse
    data = {}
    json_match = re.search(r'(\{.*\})', text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
        except:
            pass 

    answer = data.get("answer")
    if not answer: answer = clean_text(text)
    
    next_q = data.get("next_questions", [])
    if not next_q:
        next_q = re.findall(r'[1-9]\.\s*(.*?)\?', text)[:3]

    raw_vids = data.get("videos", [])
    valid_vids = [v for v in raw_vids if validate_video(v)]

    return answer, next_q, sources, valid_vids

def get_gemini_response(query, history):
    try:
        system_prompt = f"""
        You are an Education Counselor.
        TASK: Search Google for "{query}".
        OUTPUT: JSON ONLY.
        {{
            "answer": "Markdown answer.",
            "next_questions": ["Q1", "Q2", "Q3"],
            "videos": ["URL"] (Only if highly relevant)
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
    except:
        return "Connection Error.", [], [], []

# --- 6. RENDER LOGIC (SAFE HTML) ---
def render_message(msg):
    with st.chat_message(msg["role"]):
        st.markdown(clean_text(msg["content"]))
        
        # Sources (Safe Render Construction)
        if msg.get("sources"):
            # Construct HTML as a single clean string without line breaks causing issues
            html_content = '<div style="margin-top:10px; display:flex; flex-wrap:wrap;">'
            for s in msg["sources"][:3]:
                title = s["title"][:25] + ".."
                url = s["url"]
                # Use single quotes for HTML attributes to avoid f-string conflicts
                html_content += f'<a href="{url}" target="_blank" class="source-box"><span class="source-icon">🔗</span>{title}</a>'
            html_content += '</div>'
            st.markdown(html_content, unsafe_allow_html=True)

        # Videos
        if msg.get("videos"):
            st.markdown("**Watch Related:**")
            cols = st.columns(len(msg["videos"]))
            for i, v in enumerate(msg["videos"]):
                cols[i].video(v)

# --- 7. UI LOOP ---
for msg in st.session_state.messages:
    render_message(msg)

# Suggestions
st.markdown('<div class="suggestion-container">', unsafe_allow_html=True)
if st.session_state.suggestions:
    # Safely handle column creation
    count = len(st.session_state.suggestions)
    if count > 0:
        cols = st.columns(count)
        for i, s in enumerate(st.session_state.suggestions):
            if cols[i].button(s, key=f"btn_{len(st.session_state.messages)}_{i}"):
                st.session_state.messages.append({"role": "user", "content": s})
                st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# Input
if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Processing
if st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.status("Thinking...", expanded=False):
            ans, nq, src, vids = get_gemini_response(st.session_state.messages[-1]["content"], "")
        
        render_message({"role": "assistant", "content": ans, "sources": src, "videos": vids})
        
    st.session_state.messages.append({"role": "assistant", "content": ans, "sources": src, "videos": vids})
    if nq: st.session_state.suggestions = nq
    st.rerun()
