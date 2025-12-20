import streamlit as st
from google import genai
from google.genai import types
import json
import re
import random
import time

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Avanse AI Counselor",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. MODERN CSS & ANIMATIONS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* GLOBAL THEME */
    .stApp {
        background: linear-gradient(180deg, #F8F9FB 0%, #Eef2f6 100%);
        font-family: 'Inter', sans-serif;
        color: #1F2937;
    }
    
    /* HIDE DEFAULT STREAMLIT ELEMENTS */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* GLASSMORPHISM HEADER */
    .sticky-header {
        position: fixed; top: 0; left: 0; width: 100%;
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
        padding: 1rem 0;
        z-index: 999;
        text-align: center;
        transition: all 0.3s ease;
    }
    .header-logo {
        color: #003366;
        font-size: 1.4rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
    }
    .header-badge {
        background: linear-gradient(135deg, #d4af37 0%, #f3d467 100%);
        color: #003366;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 10px rgba(212, 175, 55, 0.3);
    }

    .block-container { padding-top: 6rem !important; padding-bottom: 8rem !important; }

    /* CHAT MESSAGE CARDS */
    .stChatMessage { background-color: transparent !important; border: none !important; }
    
    /* ASSISTANT BUBBLE */
    div[data-testid="chatAvatarIcon-assistant"] + div {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid #FFFFFF;
        border-radius: 4px 20px 20px 20px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
        color: #374151;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* USER BUBBLE */
    div[data-testid="chatAvatarIcon-user"] + div {
        background: linear-gradient(135deg, #003366 0%, #004488 100%);
        color: #FFFFFF !important;
        border-radius: 20px 4px 20px 20px;
        padding: 1rem 1.5rem;
        box-shadow: 0 4px 15px rgba(0, 51, 102, 0.2);
    }
    div[data-testid="chatAvatarIcon-user"] + div p { color: #FFFFFF !important; }

    /* SOURCE CHIPS */
    .source-container { margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px; }
    .source-chip {
        display: inline-flex; align-items: center;
        background-color: #F3F4F6;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 6px 12px;
        font-size: 0.75rem;
        color: #4B5563;
        text-decoration: none;
        transition: all 0.2s;
    }
    .source-chip:hover {
        background-color: #003366;
        color: #ffffff;
        border-color: #003366;
        transform: translateY(-1px);
    }

    /* SUGGESTION BUTTONS */
    .suggestion-label { 
        font-size: 0.8rem; 
        color: #9CA3AF; 
        font-weight: 600; 
        text-transform: uppercase; 
        letter-spacing: 1px;
        margin: 20px 0 10px 0; 
        text-align: center;
    }
    .stButton button {
        width: 100%;
        border-radius: 12px;
        border: 1px solid #E5E7EB;
        background-color: white;
        color: #003366;
        padding: 0.8rem;
        text-align: center;
        font-size: 0.9rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    .stButton button:hover {
        border-color: #d4af37;
        background-color: #fffdf5;
        color: #d4af37;
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(212, 175, 55, 0.15);
    }

    /* CUSTOM LOADING ANIMATION CSS */
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    @keyframes fadeChange {
        0% { opacity: 0; transform: scale(0.9); }
        10% { opacity: 1; transform: scale(1); }
        90% { opacity: 1; transform: scale(1); }
        100% { opacity: 0; transform: scale(0.9); }
    }
    
    /* The toggling icon animation */
    .icon-cycler::after {
        content: '🎓';
        animation: iconCycle 4s infinite;
        font-size: 2rem;
    }
    @keyframes iconCycle {
        0% { content: '🎓'; }
        25% { content: '✈️'; }
        50% { content: '🌍'; }
        75% { content: '🛂'; }
        100% { content: '🎓'; }
    }

    .loader-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        border: 1px solid #eee;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        margin: 10px 0;
    }
    .loader-fact {
        color: #6B7280;
        font-size: 0.9rem;
        margin-top: 10px;
        font-style: italic;
    }
    .loader-title {
        color: #003366;
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 5px;
    }

</style>
""", unsafe_allow_html=True)

# --- 3. FACTS DATA ---
EDUCATION_FACTS = [
    "Did you know? The USA hosts over 1 million international students annually.",
    "Fun Fact: Germany offers tuition-free education at public universities for international students.",
    "Tip: Canada provides a Post-Graduation Work Permit (PGWP) for up to 3 years.",
    "Insight: UK Master's degrees are typically just 1 year long, saving you time and money.",
    "Did you know? Australia allows international students to work 48 hours per fortnight.",
    "Fact: The Ivy League consists of 8 private research universities in the Northeastern US.",
    "Pro Tip: Apply for your F-1 Visa at least 120 days before your course start date.",
    "Stat: STEM degree holders often get extended OPT (work training) periods in the USA."
]

# --- 4. HEADER ---
st.markdown("""
<div class="sticky-header">
    <div class="header-logo">
        AVANSE <span class="header-badge">AI Counselor</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 5. API SETUP ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ API Key missing. Please set GEMINI_API_KEY in secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- 6. STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi there! 👋 I'm your **Avanse Education Expert**.\n\nI can help you with:\n* 🏛️ **University Shortlisting**\n* 💰 **Education Loan Eligibility**\n* 🛂 **Visa Checklists & Timelines**\n\nWhere are you planning to study?"}
    ]
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ["🇺🇸 Cost of MS in USA", "🇬🇧 Top UK Universities", "🛂 US Visa Interview Tips", "💰 Avanse Loan Interest Rates"]

# --- 7. LOGIC FUNCTIONS ---
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
    videos = data.get("videos", [])

    if not answer:
        # Fallback cleanup if JSON fails
        answer = re.sub(r'next_questions:.*', '', text, flags=re.DOTALL).strip()
        answer = re.sub(r'videos:.*', '', answer, flags=re.DOTALL).strip()
        answer = re.sub(r'```json', '', answer).replace('```', '').strip()

    return answer, next_questions, sources, videos

def format_history(messages):
    return "\n".join([f"{m['role']}: {m['content']}" for m in messages[-6:]])

def get_gemini_response(query, history):
    try:
        system_prompt = f"""
        You are an expert AI Counselor for Avanse Financial Services. You help students achieve their study abroad dreams.
        Current Date: {time.strftime("%B %Y")}
        
        TASK:
        1. Search Google for the latest 2025/2026 data regarding: "{query}"
        2. Context: {history}
        3. OUTPUT: Strictly Valid JSON.
        
        JSON STRUCTURE:
        {{
            "answer": "A friendly, professional Markdown answer. Use bolding for key terms. Keep it structured.",
            "next_questions": ["Short Follow-up 1", "Short Follow-up 2", "Short Follow-up 3"],
            "videos": ["https://www.youtube.com/watch?v=...", "https://www.youtube.com/watch?v=..."]
        }}
        
        IMPORTANT:
        - Prioritize official university or embassy data.
        - "videos": Only include high-quality, relevant YouTube links found in search. If none, return [].
        """

        response = client.models.generate_content(
            model='gemini-2.0-flash', # Or gemini-1.5-pro based on availability
            contents=query,
            config=types.GenerateContentConfig(
                temperature=0.3,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                system_instruction=system_prompt
            )
        )
        return extract_json_and_sources(response)

    except Exception as e:
        return f"⚠️ I encountered a connection issue: {str(e)}", [], [], []

# --- 8. UI COMPONENT RENDERING ---
def render_message(role, content, sources=None, videos=None):
    with st.chat_message(role):
        st.markdown(content)
        
        # Modern Source Chips
        if sources:
            links_html = '<div class="source-container">'
            for s in sources:
                # Truncate title cleanly
                title = s["title"][:25] + ".." if len(s["title"]) > 25 else s["title"]
                links_html += f'<a href="{s["url"]}" target="_blank" class="source-chip">🔗 {title}</a>'
            links_html += '</div>'
            st.markdown(links_html, unsafe_allow_html=True)
            
        # Video Accordion
        if videos:
            with st.expander("📺 Watch Related Videos", expanded=False):
                # Use columns for a grid layout if there are multiple videos
                cols = st.columns(min(len(videos), 2))
                for i, vid_url in enumerate(videos):
                    with cols[i % 2]:
                        if "youtube.com" in vid_url or "youtu.be" in vid_url:
                            st.video(vid_url)
                        else:
                            st.markdown(f"[Watch Video]({vid_url})")

# --- 9. MAIN APP LOOP ---

# A. Render Chat History
for msg in st.session_state.messages:
    render_message(msg["role"], msg["content"], msg.get("sources"), msg.get("videos"))

# B. Render Suggestions (Floating or Bottom)
st.markdown('<div class="suggestion-label">✨ Suggested Topics</div>', unsafe_allow_html=True)
selected_suggestion = None

if st.session_state.suggestions:
    # Responsive grid for buttons
    cols = st.columns(len(st.session_state.suggestions))
    for i, suggestion in enumerate(st.session_state.suggestions):
        if cols[i].button(suggestion, key=f"sugg_{len(st.session_state.messages)}_{i}"):
            selected_suggestion = suggestion

# C. Input Handling
user_input = st.chat_input("Ask about universities, loans, or visas...")
if selected_suggestion: user_input = selected_suggestion

if user_input:
    # 1. Append User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

# D. Generation Step
if st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        # --- THE HOOK: Custom Loader with Random Fact ---
        random_fact = random.choice(EDUCATION_FACTS)
        
        loader_placeholder = st.empty()
        loader_placeholder.markdown(f"""
        <div class="loader-card">
            <div class="icon-cycler"></div>
            <div class="loader-title">Researching for you...</div>
            <div class="loader-fact">{random_fact}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- API Call ---
        history_text = format_history(st.session_state.messages)
        answer, next_q, sources, videos = get_gemini_response(st.session_state.messages[-1]["content"], history_text)
        
        # --- Remove Loader & Show Result ---
        loader_placeholder.empty()
        
        # Render the result immediately
        st.markdown(answer)
        
        if sources:
            links_html = '<div class="source-container">'
            for s in sources:
                title = s["title"][:25] + ".." if len(s["title"]) > 25 else s["title"]
                links_html += f'<a href="{s["url"]}" target="_blank" class="source-chip">🔗 {title}</a>'
            links_html += '</div>'
            st.markdown(links_html, unsafe_allow_html=True)
            
        if videos:
            with st.expander("📺 Watch Related Videos", expanded=True):
                cols = st.columns(min(len(videos), 2))
                for i, vid_url in enumerate(videos):
                    with cols[i % 2]:
                         if "youtube.com" in vid_url or "youtu.be" in vid_url:
                            st.video(vid_url)

    # Save to History
    st.session_state.messages.append({
        "role": "assistant", 
        "content": answer, 
        "sources": sources,
        "videos": videos
    })
    
    if next_q: st.session_state.suggestions = next_q
    st.rerun()
