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

# --- CUSTOM AVANSE THEME CSS ---
st.markdown("""
<style>
    /* Main Background & Font */
    .stApp {
        background-color: #f8f9fa;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Styling */
    .header-container {
        padding: 1rem 0;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    .header-title {
        color: #003366; /* Deep Navy Blue */
        font-weight: 700;
        font-size: 2rem;
    }
    .header-subtitle {
        color: #d4af37; /* Gold Accent */
        font-weight: 500;
        font-size: 1rem;
    }

    /* Chat Message Bubbles */
    .stChatMessage {
        background-color: white;
        border: 1px solid #f0f0f0;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* User Message Override */
    div[data-testid="stChatMessage"] {
        background-color: #ffffff;
    }
    div[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #f0f7ff; /* Light Blue for User */
        border-left: 5px solid #0056b3;
    }

    /* Suggestion Buttons */
    .stButton button {
        border-radius: 25px;
        border: 1px solid #0056b3;
        color: #0056b3;
        background-color: white;
        padding: 0.5rem 1.2rem;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,86,179,0.1);
    }
    .stButton button:hover {
        background-color: #0056b3;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,86,179,0.2);
    }

    /* Source Link Chips */
    .source-chip {
        display: inline-block;
        background-color: #f1f3f4;
        border: 1px solid #dadce0;
        border-radius: 16px;
        padding: 4px 12px;
        margin-right: 8px;
        margin-top: 8px;
        font-size: 0.75rem;
        color: #3c4043;
        text-decoration: none;
        transition: background 0.2s;
    }
    .source-chip:hover {
        background-color: #e8eaed;
        color: #0056b3;
        border-color: #0056b3;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        margin-top: 4rem;
        color: #888;
        font-size: 0.8rem;
        border-top: 1px solid #eee;
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- API SETUP ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ API Key missing. Please set GEMINI_API_KEY in Streamlit secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your **Avanse Education Counselor**. I can help you with latest university fees, admission deadlines, and funding options. What are you looking for today?"}
    ]
if "suggestions" not in st.session_state:
    st.session_state.suggestions = [
        "💰 Cost of MS Data Science in USA",
        "📅 Fall 2025 Deadlines for Canada",
        "🏆 Top 5 Universities for ROI in Germany"
    ]

# --- HELPER FUNCTIONS ---

def clean_json_text(text):
    """Cleans LLM output to ensure valid JSON parsing."""
    text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"```$", "", text.strip())
    return text.strip()

def format_history_for_context(messages):
    """Converts chat object to a string for the model's context window."""
    history_str = ""
    for msg in messages[-5:]: # Keep last 5 turns to manage context window
        role = "User" if msg["role"] == "user" else "Counselor"
        history_str += f"{role}: {msg['content']}\n"
    return history_str

def get_gemini_response(user_query, chat_history):
    try:
        # Define Grounding Tool
        google_search_tool = types.Tool(
            google_search=types.GoogleSearch()
        )

        # Context-Aware Prompt
        system_prompt = f"""
        You are an expert AI Counselor for **Avanse Financial Services**.
        
        YOUR GOAL:
        Help Indian students with international education (Universities, Fees, Loans, Visas).
        
        INSTRUCTIONS:
        1. **SEARCH**: Always use Google Search to find the latest 2024/2025 data.
        2. **CONTEXT**: Use the chat history to understand the user's intent.
        3. **FORMAT**: Return ONLY a JSON object.
        4. **SOURCES**: If you quote a fee or date, ensure it is from a reliable source.
        
        CHAT HISTORY:
        {chat_history}
        
        JSON SCHEMA:
        {{
            "answer": "Markdown formatted answer with bold key facts...",
            "next_questions": ["Follow-up Q1 (Contextual)", "Follow-up Q2", "Follow-up Q3"]
        }}
        """

        # Generate
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=f"User Query: {user_query}. Provide specific details.",
            config=types.GenerateContentConfig(
                temperature=0.3,
                tools=[google_search_tool],
                system_instruction=system_prompt
            )
        )

        # Parse Logic
        if response.text:
            clean_text = clean_json_text(response.text)
            try:
                data = json.loads(clean_text)
            except:
                # Fallback if JSON fails
                return response.text, [], None

            # Extract Sources from Metadata
            sources = []
            if response.candidates[0].grounding_metadata and response.candidates[0].grounding_metadata.grounding_chunks:
                for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
                    if chunk.web:
                        sources.append({"title": chunk.web.title, "url": chunk.web.uri})
            
            return data.get("answer", "No info found."), data.get("next_questions", []), sources
        
        return "No response generated.", [], None

    except Exception as e:
        return f"⚠️ System Error: {str(e)}", [], None

# --- UI LAYOUT ---

# 1. Header
st.markdown("""
<div class="header-container">
    <div class="header-title">Avanse AI Counselor</div>
    <div class="header-subtitle">Your Study Abroad Companion • Powered by Avanse Innovation</div>
</div>
""", unsafe_allow_html=True)

# 2. Main Chat Area
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Display Sources if available (Only for assistant)
        if msg.get("sources"):
            st.markdown("---")
            st.caption("📚 **Verified Sources:**")
            source_html = ""
            for src in msg["sources"]:
                # Limit title length for UI cleanliness
                short_title = (src['title'][:30] + '..') if len(src['title']) > 30 else src['title']
                source_html += f'<a href="{src["url"]}" target="_blank" class="source-chip">{short_title} 🔗</a>'
            st.markdown(source_html, unsafe_allow_html=True)

# 3. Suggestions Area (Contextual)
# We place this *above* the input box for better UX
st.markdown("### Suggested Next Steps:")
selected_suggestion = None
if st.session_state.suggestions:
    cols = st.columns(len(st.session_state.suggestions))
    for i, suggestion in enumerate(st.session_state.suggestions):
        if cols[i].button(suggestion, key=f"sugg_{len(st.session_state.messages)}_{i}"):
            selected_suggestion = suggestion

# 4. Input Area
user_input = st.chat_input("Ask about universities, loans, or visas...")
if selected_suggestion: 
    user_input = selected_suggestion

# 5. Logic Loop
if user_input:
    # Add User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

# Processing (runs after rerun)
if st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.status("🔍 Researching live data...", expanded=True) as status:
            
            # Prepare Context
            history_text = format_history_for_context(st.session_state.messages)
            
            # Call AI
            answer, new_suggestions, sources = get_gemini_response(st.session_state.messages[-1]["content"], history_text)
            
            status.update(label="Response Ready", state="complete", expanded=False)
            
        st.markdown(answer)
        
        # Render Sources Immediately
        if sources:
            st.markdown("---")
            st.caption("📚 **Verified Sources:**")
            source_html = ""
            for src in sources:
                short_title = (src['title'][:30] + '..') if len(src['title']) > 30 else src['title']
                source_html += f'<a href="{src["url"]}" target="_blank" class="source-chip">{short_title} 🔗</a>'
            st.markdown(source_html, unsafe_allow_html=True)

    # Save to History
    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
    
    # Update Suggestions if valid ones came back
    if new_suggestions and len(new_suggestions) > 0:
        st.session_state.suggestions = new_suggestions
    
    st.rerun()

# 6. Footer
st.markdown("""
<div class="footer">
    Designed by <b>Avanse Financial Services AI Team</b><br>
    <i>Note: AI-generated responses can be inaccurate. Please verify with official university websites.</i>
</div>
""", unsafe_allow_html=True)
