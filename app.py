import streamlit as st
from google import genai
from google.genai import types
import json
import re

# --- 1. CONFIGURATION & BRANDING ---
st.set_page_config(
    page_title="Avanse AI Counselor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (Modern & Clean) ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; font-family: 'Inter', sans-serif; }
    
    /* Header */
    .header-container {
        padding: 1rem 0; border-bottom: 2px solid #e0e0e0; margin-bottom: 2rem;
    }
    .header-title { color: #003366; font-weight: 700; font-size: 2rem; }
    .header-subtitle { color: #d4af37; font-weight: 500; font-size: 1rem; }

    /* Chat Bubbles */
    .stChatMessage {
        background-color: white; border: 1px solid #f0f0f0; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02); padding: 1.5rem; margin-bottom: 1rem;
    }
    div[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #f0f7ff; border-left: 5px solid #0056b3;
    }

    /* Source Chips */
    .source-chip {
        display: inline-flex; align-items: center; gap: 5px;
        background-color: #e8f0fe; border: 1px solid #d2e3fc;
        border-radius: 16px; padding: 4px 12px; margin: 4px;
        font-size: 0.8rem; color: #1967d2; text-decoration: none;
        transition: all 0.2s;
    }
    .source-chip:hover {
        background-color: #d2e3fc; text-decoration: none; color: #0d47a1;
    }

    /* Suggestion Buttons */
    .stButton button {
        border-radius: 20px; border: 1px solid #0056b3; color: #0056b3;
        background-color: white; padding: 0.5rem 1rem; font-size: 0.9rem;
    }
    .stButton button:hover {
        background-color: #0056b3; color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- API SETUP ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ API Key missing. Set GEMINI_API_KEY in Streamlit secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your **Avanse Education Counselor**. Ask me about fees, deadlines, or universities!"}
    ]
if "suggestions" not in st.session_state:
    st.session_state.suggestions = [
        "💰 Cost of MS Data Science in USA", 
        "📅 Fall 2025 Deadlines for Canada", 
        "🏆 Top 5 ROI Universities in Germany"
    ]

# --- HELPER: SMART PARSER ---
def extract_json_and_sources(response):
    """
    Robustly extracts JSON, Text, and Sources even if the model output is messy.
    """
    text = response.text if response.text else ""
    sources = []
    
    # 1. Extract Sources from Metadata (Grounding)
    if response.candidates and response.candidates[0].grounding_metadata:
        md = response.candidates[0].grounding_metadata
        if md.grounding_chunks:
            for chunk in md.grounding_chunks:
                if chunk.web:
                    sources.append({"title": chunk.web.title, "url": chunk.web.uri})

    # 2. Try to find JSON block { ... }
    # Look for the last valid JSON object in the text
    json_match = re.search(r'(\{.*\})', text, re.DOTALL)
    
    data = {}
    if json_match:
        try:
            data = json.loads(json_match.group(1))
        except:
            pass # JSON parsing failed, fall back to text parsing

    # 3. Fallback: If JSON failed, parse manually
    answer = data.get("answer")
    next_questions = data.get("next_questions", [])

    if not answer:
        # If no JSON found, assume the whole text is the answer
        # But remove the "next_questions" list if it appears at the bottom
        answer = re.sub(r'next_questions:.*', '', text, flags=re.DOTALL).strip()
        answer = re.sub(r'```json', '', answer).replace('```', '').strip()

    # 4. Fallback for Questions: Regex search if not in JSON
    if not next_questions:
        # Look for ["Q1", "Q2"] pattern
        list_match = re.search(r'\["(.*)"\]', text)
        if list_match:
            try:
                # Reconstruct list from string
                q_str = list_match.group(0)
                next_questions = json.loads(q_str)
            except:
                pass

    return answer, next_questions, sources

def format_history(messages):
    """Limits context to last 3 turns to keep focus sharp."""
    return "\n".join([f"{m['role']}: {m['content']}" for m in messages[-6:]])

# --- CORE LOGIC ---
def get_gemini_response(query, history):
    try:
        # Search Tool
        google_search_tool = types.Tool(google_search=types.GoogleSearch())

        # Strict System Prompt
        system_prompt = f"""
        You are an expert AI Counselor for Avanse Financial Services.
        
        TASK:
        1. Search Google for 2024/2025 data for: "{query}"
        2. Context: {history}
        3. RETURN JSON ONLY. No preamble.
        
        JSON STRUCTURE:
        {{
            "answer": "Markdown answer with BOLD fees/dates...",
            "next_questions": ["Short Follow-up 1", "Short Follow-up 2", "Short Follow-up 3"]
        }}
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=query,
            config=types.GenerateContentConfig(
                temperature=0.3,
                tools=[google_search_tool],
                system_instruction=system_prompt
            )
        )
        
        return extract_json_and_sources(response)

    except Exception as e:
        return f"⚠️ Error: {str(e)}", [], []

# --- UI LAYOUT ---

# Header
st.markdown("""
<div class="header-container">
    <div class="header-title">Avanse AI Counselor</div>
    <div class="header-subtitle">Your Study Abroad Companion • Powered by Avanse AI Innovation lab</div>
</div>
""", unsafe_allow_html=True)

# Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Render Sources for History
        if msg.get("sources"):
            st.markdown("---")
            links_html = "".join([
                f'<a href="{s["url"]}" target="_blank" class="source-chip">🔗 {s["title"][:25]}..</a>' 
                for s in msg["sources"]
            ])
            st.markdown(links_html, unsafe_allow_html=True)

# Suggestions (Placed above input)
st.markdown("### Suggested Next Steps:")
selected_suggestion = None

# Create columns for suggestions
if st.session_state.suggestions:
    # Use index to make keys unique per render
    cols = st.columns(len(st.session_state.suggestions))
    for i, suggestion in enumerate(st.session_state.suggestions):
        if cols[i].button(suggestion, key=f"btn_{len(st.session_state.messages)}_{i}"):
            selected_suggestion = suggestion

# Input
user_input = st.chat_input("Ask about universities, loans, or visas...")
if selected_suggestion:
    user_input = selected_suggestion

# Interaction Loop
if user_input:
    # 1. Add User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

# Processing
if st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.status("🔍 Researching live data...", expanded=True) as status:
            history_text = format_history(st.session_state.messages)
            answer, next_q, sources = get_gemini_response(st.session_state.messages[-1]["content"], history_text)
            status.update(label="Response Ready", state="complete", expanded=False)

        st.markdown(answer)
        
        # Render Sources (Live)
        if sources:
            st.markdown("---")
            links_html = "".join([
                f'<a href="{s["url"]}" target="_blank" class="source-chip">🔗 {s["title"][:25]}..</a>' 
                for s in sources
            ])
            st.markdown(links_html, unsafe_allow_html=True)

    # 2. Update State
    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
    
    # Only update suggestions if we actually got new ones
    if next_q and len(next_q) > 0:
        st.session_state.suggestions = next_q
    
    st.rerun()
