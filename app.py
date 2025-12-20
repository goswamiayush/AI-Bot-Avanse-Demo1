import streamlit as st
from google import genai
from google.genai import types
import json
import re

# --- 1. CONFIGURATION: SLEEK & CENTERED ---
st.set_page_config(
    page_title="Avanse AI",
    page_icon="🎓",
    layout="centered", # <--- This makes it sleek/mobile-like on Desktop
    initial_sidebar_state="collapsed"
)

# --- 2. MODERN "APP-LIKE" CSS ---
st.markdown("""
<style>
    /* IMPORT FONT */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    /* GLOBAL RESET */
    .stApp {
        background-color: #F8F9FB;
        font-family: 'Inter', sans-serif;
    }
    
    /* HIDE STREAMLIT CLUTTER */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* STICKY "GLASS" HEADER */
    .sticky-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid #eaeaea;
        padding: 1rem 0;
        z-index: 999;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    }
    .header-logo {
        color: #003366; /* Avanse Navy */
        font-size: 1.2rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin: 0;
    }
    .header-badge {
        background: linear-gradient(135deg, #d4af37 0%, #f3d467 100%); /* Gold Gradient */
        color: #003366;
        font-size: 0.6rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 12px;
        vertical-align: middle;
        margin-left: 8px;
        text-transform: uppercase;
    }
    
    /* PUSH CONTENT DOWN (To avoid hiding behind sticky header) */
    .block-container {
        padding-top: 5rem !important;
        padding-bottom: 8rem !important; /* Space for input box */
    }

    /* CHAT BUBBLES - MODERN */
    .stChatMessage {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin-bottom: 1.5rem;
    }
    
    /* AVATARS */
    .stChatMessage .st-emotion-cache-1p1m4ay {
        background-color: #003366 !important;
        color: white !important;
    }

    /* ASSISTANT BUBBLE */
    div[data-testid="chatAvatarIcon-assistant"] + div {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 4px 18px 18px 18px;
        padding: 1.2rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        color: #1F2937;
        font-size: 0.95rem;
        line-height: 1.5;
    }

    /* USER BUBBLE */
    div[data-testid="chatAvatarIcon-user"] + div {
        background: linear-gradient(135deg, #003366 0%, #004080 100%);
        color: #FFFFFF !important;
        border-radius: 18px 4px 18px 18px;
        padding: 1rem 1.5rem;
        box-shadow: 0 4px 10px rgba(0, 51, 102, 0.2);
    }
    /* Force user text to be white */
    div[data-testid="chatAvatarIcon-user"] + div p {
        color: #FFFFFF !important;
    }

    /* SOURCE CHIPS */
    .source-container {
        margin-top: 10px;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }
    .source-chip {
        display: inline-flex;
        align-items: center;
        background-color: #F3F4F6;
        border: 1px solid #E5E7EB;
        border-radius: 20px;
        padding: 4px 10px;
        font-size: 0.7rem;
        color: #4B5563;
        text-decoration: none;
        transition: all 0.2s ease;
    }
    .source-chip:hover {
        background-color: #E0E7FF;
        color: #003366;
        border-color: #003366;
        text-decoration: none;
    }

    /* EXPLORE FURTHER (Suggestions) */
    .suggestion-label {
        font-size: 0.75rem;
        color: #6B7280;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        margin-top: 10px;
    }
    .stButton button {
        width: 100%;
        border-radius: 12px;
        border: 1px solid #E5E7EB;
        background-color: white;
        color: #003366;
        padding: 0.6rem 1rem;
        font-size: 0.85rem;
        font-weight: 500;
        text-align: left;
        transition: all 0.2s;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    .stButton button:hover {
        border-color: #d4af37; /* Gold border on hover */
        background-color: #FFFCF2; /* Very light gold tint */
        color: #003366;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    /* INPUT AREA FLOATING */
    .stChatInput {
        position: fixed;
        bottom: 2rem;
        width: 100%;
        max-width: 700px; /* Match centered layout */
        z-index: 100;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER INJECTION ---
st.markdown("""
<div class="sticky-header">
    <div class="header-logo">AVANSE<span class="header-badge">AI Counselor</span></div>
</div>
""", unsafe_allow_html=True)

# --- API SETUP ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ API Key missing.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm your dedicated education expert. Planning to study abroad? Ask me about **Universities**, **Fees**, or **Visa timelines**."}
    ]
if "suggestions" not in st.session_state:
    st.session_state.suggestions = [
        "💰 Cost of MS in USA vs UK", 
        "📅 Fall 2025 Deadlines", 
        "🏆 Top Data Science Universities"
    ]

# --- LOGIC ---
def extract_json_and_sources(response):
    text = response.text if response.text else ""
    sources = []
    
    # Extract Sources
    if response.candidates and response.candidates[0].grounding_metadata:
        md = response.candidates[0].grounding_metadata
        if md.grounding_chunks:
            for chunk in md.grounding_chunks:
                if chunk.web:
                    sources.append({"title": chunk.web.title, "url": chunk.web.uri})

    # Extract JSON
    json_match = re.search(r'(\{.*\})', text, re.DOTALL)
    data = {}
    if json_match:
        try:
            data = json.loads(json_match.group(1))
        except:
            pass 

    answer = data.get("answer")
    next_questions = data.get("next_questions", [])

    if not answer:
        answer = re.sub(r'next_questions:.*', '', text, flags=re.DOTALL).strip()
        answer = re.sub(r'```json', '', answer).replace('```', '').strip()

    return answer, next_questions, sources

def format_history(messages):
    return "\n".join([f"{m['role']}: {m['content']}" for m in messages[-6:]])

def get_gemini_response(query, history):
    try:
        system_prompt = f"""
        You are an expert AI Counselor for Avanse Financial Services.
        
        TASK:
        1. Search Google for 2024/2025 data for: "{query}"
        2. Context: {history}
        3. OUTPUT: JSON ONLY.
        
        JSON STRUCTURE:
        {{
            "answer": "Markdown answer. Use bullet points. Keep it concise.",
            "next_questions": ["Short Follow-up 1", "Short Follow-up 2", "Short Follow-up 3"]
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
        return extract_json_and_sources(response)

    except Exception as e:
        return f"⚠️ Connection Error: {str(e)}", [], []

# --- UI RENDER LOOP ---

# 1. Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            links_html = '<div class="source-container">'
            for s in msg["sources"]:
                links_html += f'<a href="{s["url"]}" target="_blank" class="source-chip">🔗 {s["title"][:20]}..</a>'
            links_html += '</div>'
            st.markdown(links_html, unsafe_allow_html=True)

# 2. "Explore Further" (Dynamic Chips)
st.markdown('<div class="suggestion-label">Explore further</div>', unsafe_allow_html=True)

# We use a container to keep buttons tight
with st.container():
    selected_suggestion = None
    if st.session_state.suggestions:
        # Use columns to make them look like chips
        cols = st.columns(len(st.session_state.suggestions))
        for i, suggestion in enumerate(st.session_state.suggestions):
            if cols[i].button(suggestion, key=f"sugg_{len(st.session_state.messages)}_{i}"):
                selected_suggestion = suggestion

# 3. Input Handling
user_input = st.chat_input("Type your question here...")
if selected_suggestion:
    user_input = selected_suggestion

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

# 4. AI Response Generation
if st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.status("Searching...", expanded=False) as status:
            history_text = format_history(st.session_state.messages)
            answer, next_q, sources = get_gemini_response(st.session_state.messages[-1]["content"], history_text)
            status.update(label="Complete", state="complete")
        
        st.markdown(answer)
        
        # Sources
        if sources:
            links_html = '<div class="source-container">'
            for s in sources:
                links_html += f'<a href="{s["url"]}" target="_blank" class="source-chip">🔗 {s["title"][:20]}..</a>'
            links_html += '</div>'
            st.markdown(links_html, unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
    if next_q:
        st.session_state.suggestions = next_q
    st.rerun()
