import streamlit as st
from google import genai
from google.genai import types
import json
import re

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Avanse AI Labs",
    page_icon="🧬",
    layout="wide", # Changed to wide to prevent cramping
    initial_sidebar_state="collapsed"
)

# --- 2. THE "REPAIR" CSS ---
st.markdown("""
<style>
    /* RESET & FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        background-color: #F4F6F9; /* High-end Fintech Grey */
        font-family: 'Inter', sans-serif;
    }
    
    /* HIDE DEFAULT ELEMENTS */
    #MainMenu, footer, header {visibility: hidden;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    
    /* LAYOUT PADDING (Fixes Input Overlap & Centering) */
    .block-container {
        padding-top: 6rem !important;
        padding-bottom: 10rem !important;
        max-width: 900px !important; /* Constrain width for readability */
        margin: 0 auto !important;
    }

    /* --- CHAT BUBBLES (UPDATED SELECTORS) --- */
    
    /* 1. Container Fix */
    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin-bottom: 20px !important;
        width: 100% !important;
        display: flex !important;
    }

    /* 2. USER BUBBLE (Right Side - Blue) */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        flex-direction: row-reverse !important;
    }
    
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) div[data-testid="stMarkdownContainer"] {
        background: linear-gradient(135deg, #0056b3 0%, #004494 100%) !important;
        color: white !important;
        padding: 15px 20px !important;
        border-radius: 20px 20px 4px 20px !important;
        box-shadow: 0 4px 10px rgba(0, 86, 179, 0.2) !important;
        margin-left: auto !important;
        margin-right: 10px !important;
        text-align: left !important; /* Force text left inside bubble */
    }
    
    /* Force Text Color White for User */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) p,
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) li {
        color: #ffffff !important;
    }

    /* 3. ASSISTANT BUBBLE (Left Side - White) */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) div[data-testid="stMarkdownContainer"] {
        background-color: #FFFFFF !important;
        color: #1F2937 !important;
        padding: 15px 25px !important;
        border-radius: 20px 20px 20px 4px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
        border: 1px solid #E5E7EB !important;
        margin-right: auto !important;
        margin-left: 10px !important;
        text-align: left !important;
    }

    /* Hide Avatars completely for cleaner look */
    div[data-testid="chatAvatarIcon-user"], div[data-testid="chatAvatarIcon-assistant"] {
        display: none !important;
    }

    /* --- SOURCE & VIDEO CARDS --- */
    
    .card-container {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 15px;
    }
    
    /* Source Pill */
    .source-pill {
        display: flex; align-items: center; gap: 6px;
        background: #FFFFFF; border: 1px solid #E0E0E0;
        border-radius: 30px; padding: 6px 14px;
        text-decoration: none !important;
        color: #333 !important; font-size: 12px; font-weight: 500;
        transition: all 0.2s;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .source-pill:hover {
        border-color: #0056b3; color: #0056b3 !important; transform: translateY(-1px);
    }

    /* Video Thumbnail Card (Prevents Black Box) */
    .video-card {
        background: white; border-radius: 12px;
        border: 1px solid #eee; overflow: hidden;
        width: 220px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-decoration: none !important; transition: transform 0.2s;
        display: block;
    }
    .video-card:hover { transform: scale(1.02); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    .video-thumb {
        width: 100%; height: 120px; object-fit: cover; background: #000;
        display: flex; align-items: center; justify-content: center;
    }
    .play-icon { font-size: 30px; color: white; opacity: 0.8; }
    .video-meta { padding: 10px; }
    .video-title { font-size: 12px; font-weight: 600; color: #333; line-height: 1.4; }
    .video-source { font-size: 10px; color: #888; margin-top: 4px; text-transform: uppercase; }

    /* --- SUGGESTIONS (Bottom Floating) --- */
    .suggestion-dock {
        position: fixed; bottom: 5rem; left: 0; right: 0;
        background: linear-gradient(to top, #F4F6F9 85%, transparent 100%);
        padding: 15px 0; z-index: 100;
        text-align: center;
    }
    .stButton button {
        border-radius: 20px !important;
        border: 1px solid #D0D5DD !important;
        background-color: white !important;
        color: #344054 !important;
        font-size: 13px !important;
        padding: 8px 16px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    .stButton button:hover {
        border-color: #0056b3 !important;
        color: #0056b3 !important;
        background-color: #F0F9FF !important;
    }

</style>
""", unsafe_allow_html=True)

# --- 3. PROFESSIONAL HEADER ---
st.markdown("""
<div style="position:fixed; top:0; left:0; width:100%; background:rgba(255,255,255,0.98); border-bottom:1px solid #E5E7EB; z-index:10000; padding:12px 0; text-align:center; box-shadow: 0 2px 10px rgba(0,0,0,0.02);">
    <div style="display:flex; align-items:center; justify-content:center; gap:10px;">
        <span style="font-size:20px; font-weight:800; color:#003366; letter-spacing:-0.5px;">AVANSE AI LABS</span>
        <span style="background:#FFD700; color:#003366; font-size:10px; font-weight:700; padding:3px 8px; border-radius:6px; letter-spacing:0.5px;">BETA</span>
    </div>
    <div style="font-size:11px; color:#666; margin-top:2px;">Global Education Assistant</div>
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
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your **Avanse Education Expert**. \n\nAsk me about **Visa Acceptance Rates**, **University ROI**, or **Education Loans**."}]
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ["Visa Acceptance for USA", "Cost of MS in Germany", "Scholarships for Indians"]

# --- 5. LOGIC ENGINE (Sanitizer) ---

def sanitize_text(text):
    """
    Removes raw HTML artifacts and code blocks that break the UI.
    """
    # Remove HTML tags that might have leaked
    text = re.sub(r'<[^>]*>', '', text) 
    # Remove JSON blocks
    text = re.sub(r'```json.*?```', '', text, flags=re.DOTALL)
    # Remove metadata headers
    text = re.sub(r'Next Steps:.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    return text.strip()

def get_youtube_id(url):
    """Extracts video ID to create a thumbnail image."""
    regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    match = re.search(regex, url)
    return match.group(1) if match else None

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

    # 2. JSON Parsing
    data = {}
    json_match = re.search(r'(\{.*\})', text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
        except:
            pass 

    # 3. Content Extraction
    answer = data.get("answer")
    if not answer: answer = sanitize_text(text)
    
    next_q = data.get("next_questions", [])
    if not next_q:
        next_q = re.findall(r'[1-9]\.\s*(.*?)\?', text)[:3]

    videos = data.get("videos", [])

    return answer, next_q, sources, videos

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
            "answer": "Markdown answer. Use bullet points.",
            "next_questions": ["Q1", "Q2", "Q3"],
            "videos": ["URL"] (Valid YouTube links only)
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
        return "I'm having trouble connecting right now.", [], [], []

# --- 6. UI RENDERER ---

def render_message(msg):
    with st.chat_message(msg["role"]):
        # 1. Text Content
        st.markdown(sanitize_text(msg["content"]))
        
        # 2. Sources (Pill Style)
        if msg.get("sources"):
            html = '<div class="card-container">'
            for s in msg["sources"][:3]:
                title = s["title"][:25] + "..."
                html += f'<a href="{s["url"]}" target="_blank" class="source-pill">🔗 {title}</a>'
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

        # 3. Video Cards (No Black Boxes)
        if msg.get("videos"):
            valid_vids = []
            for v in msg["videos"]:
                vid_id = get_youtube_id(v)
                if vid_id: valid_vids.append({"url": v, "id": vid_id})
            
            if valid_vids:
                st.markdown('<p style="font-size:11px; font-weight:700; color:#888; margin-top:20px; margin-bottom:5px;">WATCH RELATED</p>', unsafe_allow_html=True)
                
                # Render Grid manually using HTML to avoid Streamlit iframe issues
                vid_html = '<div class="card-container">'
                for v in valid_vids[:2]: # Limit to 2 videos
                    thumb = f"https://img.youtube.com/vi/{v['id']}/mqdefault.jpg"
                    vid_html += f"""
                    <a href="{v['url']}" target="_blank" class="video-card">
                        <div class="video-thumb" style="background-image:url({thumb}); background-size:cover;">
                            <span class="play-icon">▶</span>
                        </div>
                        <div class="video-meta">
                            <div class="video-title">Watch Video Guide</div>
                            <div class="video-source">YouTube</div>
                        </div>
                    </a>
                    """
                vid_html += '</div>'
                st.markdown(vid_html, unsafe_allow_html=True)

# --- 7. MAIN LOOP ---

# History
for msg in st.session_state.messages:
    render_message(msg)

# Suggestions
st.markdown('<div class="suggestion-dock">', unsafe_allow_html=True)
if st.session_state.suggestions:
    # Use standard container to center
    with st.container():
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

# AI Response
if st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.status("Analyzing...", expanded=False):
            # Pass history context
            hist_txt = "\n".join([m["content"] for m in st.session_state.messages[-3:]])
            ans, nq, src, vids = get_gemini_response(st.session_state.messages[-1]["content"], hist_txt)
        
        render_message({"role": "assistant", "content": ans, "sources": src, "videos": vids})
    
    st.session_state.messages.append({"role": "assistant", "content": ans, "sources": src, "videos": vids})
    if nq: st.session_state.suggestions = nq
    st.rerun()

        
