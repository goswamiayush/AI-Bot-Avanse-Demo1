import streamlit as st
from google import genai
from google.genai import types
import json
import re

# --- 1. CONFIGURATION: MOBILE-FIRST ---
st.set_page_config(
    page_title="Avanse AI",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. ADVANCED CSS (iMessage Style) ---
st.markdown("""
<style>
    /* IMPORT IOS FONT */
    @import url('-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif');
    
    /* GLOBAL RESET */
    .stApp {
        background-color: #FFFFFF;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* HIDE STREAMLIT ELEMENTS */
    #MainMenu, footer, header {visibility: hidden;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    
    /* PADDING FOR FIXED HEADER/FOOTER */
    .block-container {
        padding-top: 6rem !important;
        padding-bottom: 10rem !important;
    }

    /* --- CHAT MESSAGE CONTAINERS --- */
    
    /* Remove default Streamlit styling */
    .stChatMessage {
        background-color: transparent !important;
        border: none !important;
    }
    
    /* HIDE AVATARS (iMessage style doesn't use them much) */
    div[data-testid="chatAvatarIcon-user"], div[data-testid="chatAvatarIcon-assistant"] {
        display: none;
    }

    /* --- USER BUBBLE (Blue, Right Aligned) --- */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        flex-direction: row-reverse;
        text-align: right;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) div[data-testid="stMarkdownContainer"] {
        background-color: #007AFF; /* Apple Blue */
        color: white;
        padding: 12px 18px;
        border-radius: 20px 20px 4px 20px; /* Sharp bottom-right */
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    /* Force text color inside user bubble */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) p {
        color: white !important;
    }

    /* --- AI BUBBLE (Gray, Left Aligned) --- */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) div[data-testid="stMarkdownContainer"] {
        background-color: #E5E5EA; /* Apple Gray */
        color: #000000;
        padding: 12px 18px;
        border-radius: 20px 20px 20px 4px; /* Sharp bottom-left */
        max-width: 85%;
        margin-right: auto;
    }

    /* --- HEADER (Glassmorphism) --- */
    .sticky-header {
        position: fixed; top: 0; left: 0; width: 100%;
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(0,0,0,0.05);
        padding: 15px 0;
        z-index: 1000;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .header-title {
        font-size: 17px;
        font-weight: 600;
        color: #000;
        margin: 0;
    }
    .header-status {
        font-size: 11px;
        color: #8E8E93; /* Apple secondary label */
        margin-top: 2px;
    }

    /* --- SUGGESTION CHIPS (Horizontal Scroll) --- */
    .suggestion-container {
        display: flex;
        gap: 8px;
        overflow-x: auto;
        padding: 10px 0;
        margin-bottom: 10px;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none; /* Hide scrollbar Firefox */
    }
    .suggestion-container::-webkit-scrollbar { display: none; } /* Hide scrollbar Chrome */
    
    .stButton button {
        border-radius: 20px;
        border: 1px solid #E5E5EA;
        background-color: #FFFFFF;
        color: #007AFF;
        font-weight: 500;
        font-size: 13px;
        padding: 6px 16px;
        white-space: nowrap;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        transition: all 0.2s;
    }
    .stButton button:hover {
        background-color: #F2F2F7;
        border-color: #007AFF;
        transform: scale(1.02);
    }

    /* --- VIDEO CARDS (Grid View) --- */
    .video-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 15px;
        margin-top: 15px;
    }
    .video-card {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #E5E5EA;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    
    /* --- SOURCE LINKS --- */
    .source-link {
        font-size: 11px;
        color: #8E8E93;
        text-decoration: none;
        margin-right: 10px;
        display: inline-block;
        margin-top: 5px;
    }
    .source-link:hover { color: #007AFF; text-decoration: underline; }

</style>
""", unsafe_allow_html=True)

# --- 3. HEADER UI ---
st.markdown("""
<div class="sticky-header">
    <div class="header-title">Avanse Counselor</div>
    <div class="header-status">Online • AI Assistant</div>
</div>
""", unsafe_allow_html=True)

# --- 4. API & SETUP ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ API Key missing.")
    st.stop()

client = genai.Client(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi there! 👋 I can help you research universities, check visa fees, or find scholarships. What's on your mind?"}
    ]
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ["Compare MS in US vs UK", "Visa acceptance rates 2024", "Scholarships for Indians"]

# --- 5. LOGIC ENGINE ---
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

    # JSON Parsing
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
        answer = re.sub(r'next_questions:.*', '', text, flags=re.DOTALL).strip()
        answer = re.sub(r'videos:.*', '', answer, flags=re.DOTALL).strip()
        answer = re.sub(r'```json', '', answer).replace('```', '').strip()

    return answer, next_questions, sources, videos

def format_history(messages):
    return "\n".join([f"{m['role']}: {m['content']}" for m in messages[-4:]])

def get_gemini_response(query, history):
    try:
        system_prompt = f"""
        You are a helpful education counselor.
        
        TASK:
        1. Search Google for 2024/2025 data: "{query}"
        2. Context: {history}
        3. OUTPUT: JSON ONLY.
        
        JSON SCHEMA:
        {{
            "answer": "Clean markdown answer. Use bolding for numbers/fees.",
            "next_questions": ["Short Q1", "Short Q2", "Short Q3"],
            "videos": ["https://www.youtube.com/watch?v=..."] (Include 1-2 highly relevant YouTube links)
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

# --- 6. RENDER FUNCTIONS ---

def render_chat_message(msg):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Sources (Subtle footer)
        if msg.get("sources"):
            st.markdown("---")
            source_html = ""
            for s in msg["sources"][:3]: # Limit to 3 sources for cleanliness
                source_html += f'<a href="{s["url"]}" target="_blank" class="source-link">{s["title"][:20]}... ↗</a>'
            st.markdown(source_html, unsafe_allow_html=True)
            
        # Videos (Modern Cards)
        if msg.get("videos"):
            st.markdown("**Watch Related:**")
            # Use columns for a "Grid" look
            cols = st.columns(len(msg["videos"]))
            for i, vid in enumerate(msg["videos"]):
                if "youtube" in vid or "youtu.be" in vid:
                    cols[i].video(vid)

# --- 7. MAIN UI LOOP ---

# A. Render History
for msg in st.session_state.messages:
    render_chat_message(msg)

# B. Suggestions (Explore Further)
st.markdown('<div style="font-size: 12px; color: #8E8E93; margin-top: 20px; margin-bottom: 5px; font-weight: 500;">EXPLORE FURTHER</div>', unsafe_allow_html=True)

# Horizontal layout for buttons using columns
selected_suggestion = None
if st.session_state.suggestions:
    # Hack: Streamlit columns usually stack on mobile, but for 3 items it works okay.
    # For true horizontal scroll, we rely on the CSS tweaks above.
    cols = st.columns(len(st.session_state.suggestions))
    for i, suggestion in enumerate(st.session_state.suggestions):
        if cols[i].button(suggestion, key=f"sugg_{len(st.session_state.messages)}_{i}"):
            selected_suggestion = suggestion

# C. Input
user_input = st.chat_input("iMessage...")
if selected_suggestion: user_input = selected_suggestion

# D. Interaction Logic
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

if st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        # No spinner text, just a clean loading state if possible, or minimal text
        with st.status("Reading...", expanded=False) as status:
            history_text = format_history(st.session_state.messages)
            answer, next_q, sources, videos = get_gemini_response(st.session_state.messages[-1]["content"], history_text)
            status.update(label="Sent", state="complete")
        
        st.markdown(answer)
        
        # Render extras immediately for "pop" effect
        if sources:
            source_html = "<br>"
            for s in sources[:3]:
                source_html += f'<a href="{s["url"]}" target="_blank" class="source-link">{s["title"][:20]}... ↗</a>'
            st.markdown(source_html, unsafe_allow_html=True)
            
        if videos:
            st.markdown("**Watch Related:**")
            cols = st.columns(len(videos))
            for i, vid in enumerate(videos):
                cols[i].video(vid)

    st.session_state.messages.append({
        "role": "assistant", 
        "content": answer, 
        "sources": sources,
        "videos": videos
    })
    
    if next_q: st.session_state.suggestions = next_q
    st.rerun()
