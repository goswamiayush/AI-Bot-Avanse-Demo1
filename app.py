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

# --- 2. ADVANCED CSS (THE "IMESSAGE" OVERHAUL) ---
st.markdown("""
<style>
    /* --- GLOBAL SETTINGS --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        background-color: #F2F2F7; /* iOS System Grey Background */
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    /* Hide Streamlit Clutter */
    #MainMenu, footer, header {visibility: hidden;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    
    /* Fix Padding for Fixed Elements */
    .block-container {
        padding-top: 6rem !important;
        padding-bottom: 12rem !important;
        max-width: 750px;
    }

    /* --- CUSTOM HEADER (VIBRANT) --- */
    .nav-header {
        position: fixed; top: 0; left: 0; width: 100%;
        background: rgba(255, 255, 255, 0.90);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(0,0,0,0.1);
        z-index: 9999;
        padding: 1rem 0;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }
    .logo-container {
        display: flex; align-items: center; gap: 8px;
    }
    .logo-text {
        color: #003366; /* Avanse Navy */
        font-size: 1.4rem; font-weight: 800; letter-spacing: -0.5px;
    }
    .beta-tag {
        background: linear-gradient(135deg, #FFD700 0%, #FDB931 100%); /* Gold Gradient */
        color: #003366; font-size: 0.65rem; font-weight: 700;
        padding: 3px 8px; border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .header-sub {
        font-size: 0.75rem; color: #8E8E93; margin-top: 2px; font-weight: 500;
    }

    /* --- CHAT BUBBLES (TRUE SEPARATION) --- */
    
    /* Reset Streamlit defaults */
    .stChatMessage { background-color: transparent !important; border: none !important; padding: 0 !important; margin-bottom: 1.5rem; }
    div[data-testid="chatAvatarIcon-user"], div[data-testid="chatAvatarIcon-assistant"] { display: none !important; }

    /* USER BUBBLE (Right / Blue) */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        flex-direction: row-reverse;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) div[data-testid="stMarkdownContainer"] {
        background: linear-gradient(135deg, #007AFF 0%, #005ecb 100%); /* iOS Blue */
        color: white;
        padding: 12px 18px;
        border-radius: 20px 20px 4px 20px; /* Sharp bottom-right */
        box-shadow: 0 4px 6px rgba(0, 122, 255, 0.2);
        max-width: 80%;
        margin-left: auto;
        text-align: left;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) p { color: white !important; }

    /* ASSISTANT BUBBLE (Left / White) */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) div[data-testid="stMarkdownContainer"] {
        background-color: #FFFFFF;
        color: #1C1C1E;
        padding: 16px 22px;
        border-radius: 20px 20px 20px 4px; /* Sharp bottom-left */
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid rgba(0,0,0,0.05);
        max-width: 90%;
        margin-right: auto;
    }

    /* --- RICH SOURCE CARDS --- */
    .source-grid {
        display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; padding-top: 12px;
        border-top: 1px solid #F2F2F7;
    }
    .source-card {
        display: flex; align-items: center; gap: 6px;
        background: #F9F9F9; border: 1px solid #E5E5EA;
        border-radius: 8px; padding: 6px 10px;
        text-decoration: none; transition: all 0.2s;
        max-width: 100%;
    }
    .source-card:hover {
        background: #F0F5FF; border-color: #007AFF; transform: translateY(-1px);
    }
    .source-icon { font-size: 14px; }
    .source-text {
        font-size: 0.75rem; color: #333; font-weight: 500;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 150px;
    }

    /* --- SUGGESTIONS (FLOATING PILLS) --- */
    .suggestion-container {
        position: fixed; bottom: 5rem; left: 0; width: 100%;
        background: linear-gradient(to top, #F2F2F7 80%, transparent 100%);
        padding: 15px 0; z-index: 100;
        display: flex; justify-content: center; gap: 10px;
        overflow-x: auto;
    }
    .stButton button {
        background-color: #FFFFFF;
        border: 1px solid #D1D1D6;
        border-radius: 20px;
        color: #003366;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0.5rem 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        background-color: #003366;
        color: white;
        border-color: #003366;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 51, 102, 0.2);
    }
    
    /* --- VIDEO SECTION --- */
    .video-section-title {
        font-size: 0.75rem; font-weight: 700; color: #8E8E93;
        text-transform: uppercase; margin: 15px 0 8px 0; letter-spacing: 0.5px;
    }
    .stVideo { border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }

</style>
""", unsafe_allow_html=True)

# --- 3. HEADER HTML ---
st.markdown("""
<div class="nav-header">
    <div class="logo-container">
        <span class="logo-text">AVANSE AI LABS</span>
        <span class="beta-tag">BETA</span>
    </div>
    <div class="header-sub">International Education Assistant</div>
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
        {"role": "assistant", "content": "Welcome! I'm your **Avanse Education Expert**. \n\nI can help you with **Visa Acceptance Rates**, **University Rankings**, or **Education Loans**. How can I assist you today?"}
    ]
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ["🇺🇸 Visa Chances for USA", "🇩🇪 Cost of MS in Germany", "💰 Education Loan Eligibility"]

# --- 6. INTELLIGENCE LAYER (With Validation) ---
def clean_text(text):
    text = re.sub(r'```json.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'Next Steps:.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    return text.strip()

def validate_video_url(url):
    """
    Strictly checks if a URL is a valid, embeddable YouTube link.
    Prevents the 'Video Unavailable' black box.
    """
    if not url: return False
    # Regex for standard YouTube watch URLs or short URLs
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    match = re.match(youtube_regex, url)
    return bool(match)

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
    raw_videos = data.get("videos", [])
    
    # 3. VIDEO VALIDATION FILTER
    # Only keep videos that pass the regex check
    valid_videos = []
    for v in raw_videos:
        if validate_video_url(v):
            valid_videos.append(v)

    # 4. Fallback: If JSON failed, parse text manually
    if not answer:
        answer = clean_text(text)
    
    if not next_questions:
        # Simple extraction for bullet points looking like questions
        potential_qs = re.findall(r'[1-9\-•]\.?\s*(What|How|Can|Which|Is).*?\?', text)
        if potential_qs:
            next_questions = potential_qs[:3]

    return answer, next_questions, sources, valid_videos

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
            "answer": "Markdown answer. Keep it engaging and concise.",
            "next_questions": ["Short Q1", "Short Q2", "Short Q3"],
            "videos": ["https://www.youtube.com/watch?v=..."] (Include 1-2 YouTube links ONLY if they are highly relevant official guides)
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
        return f"⚠️ Error: {str(e)}", [], [], []

# --- 7. RENDER FUNCTIONS ---

def render_message(msg):
    with st.chat_message(msg["role"]):
        # Main Content
        clean_content = clean_text(msg["content"])
        st.markdown(clean_content)
        
        # Sources (Rich Cards)
        if msg.get("sources"):
            source_html = '<div class="source-grid">'
            for s in msg["sources"][:3]:
                # Shorten title
                title = s["title"][:30] + ".." if len(s["title"]) > 30 else s["title"]
                source_html += f"""
                <a href="{s["url"]}" target="_blank" class="source-card">
                    <span class="source-icon">🔗</span>
                    <span class="source-text">{title}</span>
                </a>
                """
            source_html += '</div>'
            st.markdown(source_html, unsafe_allow_html=True)
            
        # Videos (Conditional Rendering)
        # ONLY render if we have VALID videos. If list is empty, nothing shows.
        if msg.get("videos"):
            st.markdown('<div class="video-section-title">Watch Related</div>', unsafe_allow_html=True)
            cols = st.columns(len(msg["videos"]))
            for i, vid_url in enumerate(msg["videos"]):
                cols[i].video(vid_url)

# --- 8. MAIN UI LOOP ---

# A. Render History
for msg in st.session_state.messages:
    render_message(msg)

# B. Suggestions (Floating Pill Area)
st.markdown('<div class="suggestion-container">', unsafe_allow_html=True)
selected_suggestion = None

if st.session_state.suggestions:
    # Use columns to ensure horizontal layout logic inside container
    count = min(len(st.session_state.suggestions), 3)
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
        with st.status("Analyzing...", expanded=False) as status:
            history_text = format_history(st.session_state.messages)
            answer, next_q, sources, videos = get_gemini_response(st.session_state.messages[-1]["content"], history_text)
            status.update(label="Complete", state="complete")
        
        render_message({
            "role": "assistant", "content": answer, "sources": sources, "videos": videos
        })

    st.session_state.messages.append({
        "role": "assistant", "content": answer, "sources": sources, "videos": videos
    })
    
    if next_q: st.session_state.suggestions = next_q
    st.rerun()
