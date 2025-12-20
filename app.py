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

# --- 2. ADVANCED CSS (FIXED SELECTORS) ---
st.markdown("""
<style>
    /* GLOBAL FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    .stApp {
        background-color: #F2F2F7;
        font-family: 'Inter', sans-serif;
    }
    
    /* HIDE DEFAULT ELEMENTS */
    #MainMenu, footer, header {visibility: hidden;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    
    /* LAYOUT PADDING (Fixes Input Overlap) */
    .block-container {
        padding-top: 6rem !important;
        padding-bottom: 10rem !important; /* Increased space for bottom input */
        max-width: 750px;
    }

    /* --- CHAT BUBBLES (UPDATED SELECTORS) --- */
    
    /* 1. Reset Container */
    .stChatMessage {
        background-color: transparent !important;
        border: none !important;
    }

    /* 2. USER BUBBLE (Blue/Right) */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        flex-direction: row-reverse;
        justify-content: flex-end;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) div[data-testid="stMarkdownContainer"] {
        background-color: #007AFF !important;
        color: white !important;
        padding: 12px 18px;
        border-radius: 20px 20px 4px 20px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        max-width: 80%;
        text-align: left;
        margin-left: auto;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) p {
        color: white !important;
    }

    /* 3. ASSISTANT BUBBLE (White/Left) */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) div[data-testid="stMarkdownContainer"] {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        padding: 14px 20px;
        border-radius: 20px 20px 20px 4px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        max-width: 90%;
    }

    /* --- SOURCE CARDS (Grid Layout) --- */
    .source-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid rgba(0,0,0,0.05);
    }
    .source-card {
        background: #F9F9F9;
        border: 1px solid #E5E5EA;
        border-radius: 8px;
        padding: 6px 10px;
        text-decoration: none;
        display: flex;
        align-items: center;
        gap: 5px;
        transition: all 0.2s;
        max-width: 48%; /* 2 per row approx */
    }
    .source-card:hover {
        background: #EBF3FF;
        border-color: #007AFF;
    }
    .source-text {
        font-size: 11px;
        color: #333;
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* --- VIDEO HIDDEN CONTAINER --- */
    /* If video fails, we want it invisible */
    .stVideo {
        margin-top: 10px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }

    /* --- SUGGESTIONS (Floating) --- */
    .suggestion-container {
        position: fixed;
        bottom: 5rem;
        left: 0;
        width: 100%;
        background: linear-gradient(to top, #F2F2F7 90%, transparent 100%);
        padding: 10px 0;
        z-index: 99;
        display: flex;
        justify-content: center;
        gap: 8px;
    }
    .stButton button {
        border-radius: 20px;
        border: 1px solid #C7C7CC;
        background-color: white;
        color: #007AFF;
        font-size: 12px;
        font-weight: 500;
        padding: 6px 14px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stButton button:hover {
        background-color: #007AFF;
        color: white;
        border-color: #007AFF;
    }

</style>
""", unsafe_allow_html=True)

# --- 3. HEADER ---
st.markdown("""
<div style="position:fixed; top:0; left:0; width:100%; background:rgba(255,255,255,0.95); padding:15px; border-bottom:1px solid #ddd; z-index:1000; text-align:center; backdrop-filter:blur(10px);">
    <span style="font-size:18px; font-weight:800; color:#003366;">AVANSE AI LABS</span>
    <span style="background:#FFD700; color:#003366; font-size:9px; font-weight:700; padding:2px 6px; border-radius:4px; margin-left:5px;">BETA</span>
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
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm your Avanse Education Expert."}]
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ["Visa Acceptance USA", "Tuition Fees Germany", "Scholarships"]

# --- 5. LOGIC (Safe Parsing) ---
def clean_text(text):
    text = re.sub(r'```json.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'Next Steps:.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    return text.strip()

def validate_video(url):
    # Strict YouTube Filter
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
        # Fallback question finder
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
        return "Sorry, I couldn't connect.", [], [], []

# --- 6. RENDER LOGIC ---
def render_message(msg):
    with st.chat_message(msg["role"]):
        st.markdown(clean_text(msg["content"]))
        
        # Sources (Safe Render)
        if msg.get("sources"):
            # We build the HTML string carefully to avoid the raw code bug
            html_parts = ['<div class="source-grid">']
            for s in msg["sources"][:3]:
                title = s["title"][:25] + ".."
                # Safe F-String
                html_parts.append(f"""
                    <a href="{s['url']}" target="_blank" class="source-card">
                        <span style="font-size:12px;">🔗</span>
                        <span class="source-text">{title}</span>
                    </a>
                """)
            html_parts.append('</div>')
            st.markdown("".join(html_parts), unsafe_allow_html=True)

        # Videos
        if msg.get("videos"):
            # Only show if list is not empty
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
    cols = st.columns(len(st.session_state.suggestions))
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
