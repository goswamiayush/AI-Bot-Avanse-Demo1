import streamlit as st
from google import genai
from google.genai import types
import json
import re

# --- 1. CONFIGURATION: SLEEK & CENTERED ---
st.set_page_config(
    page_title="Avanse AI",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. MODERN CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    .stApp { background-color: #F8F9FB; font-family: 'Inter', sans-serif; }
    
    /* HIDE CLUTTER */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* STICKY HEADER */
    .sticky-header {
        position: fixed; top: 0; left: 0; width: 100%;
        background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px);
        border-bottom: 1px solid #eaeaea; padding: 1rem 0;
        z-index: 999; text-align: center;
    }
    .header-logo { color: #003366; font-size: 1.2rem; font-weight: 700; margin: 0; }
    .header-badge {
        background: linear-gradient(135deg, #d4af37 0%, #f3d467 100%);
        color: #003366; font-size: 0.6rem; font-weight: 700;
        padding: 3px 8px; border-radius: 12px; margin-left: 8px; vertical-align: middle;
    }
    
    .block-container { padding-top: 5rem !important; padding-bottom: 8rem !important; }

    /* CHAT BUBBLES */
    .stChatMessage { background-color: transparent !important; border: none !important; }
    
    /* ASSISTANT */
    div[data-testid="chatAvatarIcon-assistant"] + div {
        background-color: #FFFFFF; border: 1px solid #E5E7EB;
        border-radius: 4px 18px 18px 18px; padding: 1.2rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02); color: #1F2937;
    }

    /* USER */
    div[data-testid="chatAvatarIcon-user"] + div {
        background: linear-gradient(135deg, #003366 0%, #004080 100%);
        color: #FFFFFF !important; border-radius: 18px 4px 18px 18px;
        padding: 1rem 1.5rem;
    }
    div[data-testid="chatAvatarIcon-user"] + div p { color: #FFFFFF !important; }

    /* SOURCE CHIPS */
    .source-container { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px; }
    .source-chip {
        display: inline-flex; align-items: center; background-color: #F3F4F6;
        border: 1px solid #E5E7EB; border-radius: 20px; padding: 4px 10px;
        font-size: 0.7rem; color: #4B5563; text-decoration: none;
    }
    .source-chip:hover { background-color: #E0E7FF; color: #003366; border-color: #003366; }

    /* SUGGESTIONS */
    .suggestion-label { font-size: 0.75rem; color: #6B7280; font-weight: 600; text-transform: uppercase; margin: 10px 0; }
    .stButton button {
        width: 100%; border-radius: 12px; border: 1px solid #E5E7EB;
        background-color: white; color: #003366; padding: 0.6rem;
        text-align: left; font-size: 0.85rem;
    }
    .stButton button:hover { border-color: #d4af37; background-color: #FFFCF2; }

    /* VIDEO CONTAINER */
    .video-label { font-size: 0.8rem; font-weight: 600; color: #333; margin-top: 15px; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div class="sticky-header">
    <div class="header-logo">AVANSE<span class="header-badge">AI Counselor</span></div>
</div>
""", unsafe_allow_html=True)

# --- API ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ API Key missing.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm your dedicated education expert. Ask me about **Universities**, **Fees**, or **Visa timelines**."}
    ]
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ["💰 Cost of MS in USA vs UK", "📅 Fall 2025 Deadlines", "🏆 Top Data Science Universities"]

# --- LOGIC ---
def extract_json_and_sources(response):
    text = response.text if response.text else ""
    sources = []
    
    # Grounding Sources
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
    videos = data.get("videos", []) # Extract videos

    if not answer:
        answer = re.sub(r'next_questions:.*', '', text, flags=re.DOTALL).strip()
        answer = re.sub(r'videos:.*', '', answer, flags=re.DOTALL).strip()
        answer = re.sub(r'```json', '', answer).replace('```', '').strip()

    return answer, next_questions, sources, videos

def format_history(messages):
    return "\n".join([f"{m['role']}: {m['content']}" for m in messages[-6:]])

def get_gemini_response(query, history):
    try:
        # Prompt explicitly asks for VIDEO links
        system_prompt = f"""
        You are an expert AI Counselor for Avanse Financial Services to guide ineterested candidate for international studies. Consider todays date to make results relevant.
        
        TASK:
        1. Search Google for 2025/2026 data for: "{query}"
        2. Context: {history}
        3. OUTPUT: JSON ONLY.
        
        JSON STRUCTURE:
        {{
            "answer": "Markdown answer. Use bullet points. Keep it concise.",
            "next_questions": ["Short Follow-up 1", "Short Follow-up 2", "Short Follow-up 3"],
            "videos": ["https://www.youtube.com/watch?v=example1", "https://www.youtube.com/watch?v=example2"]
        }}
        
        IMPORTANT:
        - Only include "videos" if you find valid YouTube links in the search results relevant to the topic.
        - If no videos found, leave the array empty [].
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=query,
            config=types.GenerateContentConfig(
                temperature=0.3,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                system_instruction=system_prompt
            )
        )
        return extract_json_and_sources(response)

    except Exception as e:
        return f"⚠️ Connection Error: {str(e)}", [], [], []

# --- RENDER HELPER ---
def render_message(role, content, sources=None, videos=None):
    with st.chat_message(role):
        st.markdown(content)
        
        # Sources
        if sources:
            links_html = '<div class="source-container">'
            for s in sources:
                links_html += f'<a href="{s["url"]}" target="_blank" class="source-chip">🔗 {s["title"][:20]}..</a>'
            links_html += '</div>'
            st.markdown(links_html, unsafe_allow_html=True)
            
        # Video Embeds (Modern Accordion)
        if videos:
            with st.expander("📺 Watch Related Videos", expanded=False):
                cols = st.columns(len(videos))
                for i, vid_url in enumerate(videos):
                    # Basic validation to ensure it's a video link
                    if "youtube.com" in vid_url or "youtu.be" in vid_url:
                        st.video(vid_url)
                    else:
                        st.markdown(f"[Watch Video]({vid_url})")

# --- UI LOOP ---

# 1. History
for msg in st.session_state.messages:
    render_message(msg["role"], msg["content"], msg.get("sources"), msg.get("videos"))

# 2. Suggestions
st.markdown('<div class="suggestion-label">Explore further</div>', unsafe_allow_html=True)
with st.container():
    selected_suggestion = None
    if st.session_state.suggestions:
        cols = st.columns(len(st.session_state.suggestions))
        for i, suggestion in enumerate(st.session_state.suggestions):
            if cols[i].button(suggestion, key=f"sugg_{len(st.session_state.messages)}_{i}"):
                selected_suggestion = suggestion

# 3. Input
user_input = st.chat_input("Type your question here...")
if selected_suggestion: user_input = selected_suggestion

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

# 4. Generation
if st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.status("Searching...", expanded=False) as status:
            history_text = format_history(st.session_state.messages)
            answer, next_q, sources, videos = get_gemini_response(st.session_state.messages[-1]["content"], history_text)
            status.update(label="Complete", state="complete")
        
        # Render the response immediately
        st.markdown(answer)
        if sources:
            links_html = '<div class="source-container">'
            for s in sources:
                links_html += f'<a href="{s["url"]}" target="_blank" class="source-chip">🔗 {s["title"][:20]}..</a>'
            links_html += '</div>'
            st.markdown(links_html, unsafe_allow_html=True)
        if videos:
            with st.expander("📺 Watch Related Videos", expanded=True): # Expanded by default for "Wow" factor
                for vid_url in videos:
                    if "youtube.com" in vid_url or "youtu.be" in vid_url:
                        st.video(vid_url)

    # Save State
    st.session_state.messages.append({
        "role": "assistant", 
        "content": answer, 
        "sources": sources,
        "videos": videos
    })
    
    if next_q: st.session_state.suggestions = next_q
    st.rerun()
