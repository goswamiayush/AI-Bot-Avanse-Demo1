import streamlit as st
from google import genai
from google.genai import types
import json

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="UniGuide AI", page_icon="🎓")

st.markdown("""
<style>
    .stChatMessage {border-radius: 15px; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);}
    .stButton button {border-radius: 20px; background-color: #F8F9FA;}
</style>
""", unsafe_allow_html=True)

# --- 2. SETUP NEW GEMINI CLIENT ---
try:
    # Gets API Key from Streamlit Secrets
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # NEW SDK INITIALIZATION
    client = genai.Client(api_key=api_key)
    
except Exception as e:
    st.error(f"⚠️ API Key missing. Set GEMINI_API_KEY in secrets.")
    st.stop()

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your AI Counselor. Ask me about universities, fees, or deadlines."}]
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ["Tuition for MS CS at TU Munich", "Scholarships for Indians in UK", "USA vs Germany for Data Science"]

# --- 3. THE CORE FUNCTION (NEW SDK) ---
def get_gemini_response(user_query):
    """
    Uses the new google-genai SDK to Search + Validate + Format in one go.
    """
    
    # We define the strict structure we want the AI to return.
    # This replaces the need for complex parsing logic.
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "answer": {"type": "STRING", "description": "The detailed answer with fees, dates, and requirements."},
            "validation_status": {"type": "STRING", "description": "Either 'VERIFIED' if official data found, or 'UNCERTAIN' if data is vague."},
            "next_questions": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "3 relevant follow-up questions."
            }
        },
        "required": ["answer", "validation_status", "next_questions"]
    }

    try:
        # CALLING THE NEW API
        response = client.models.generate_content(
            model='gemini-2.5-flash', # Use 1.5-flash for Free Tier (2.0 is paid/preview)
            contents=f"User Question: {user_query}",
            config=types.GenerateContentConfig(
                # Enable Google Search (Grounding)
                tools=[types.Tool(google_search=types.GoogleSearch())],
                
                # Force JSON Output
                response_mime_type="application/json",
                response_schema=response_schema,
                
                # Validation Logic in System Prompt
                system_instruction="""
                You are a strict Overseas Education Counselor.
                1. RESEARCH: You must use the Google Search tool to find 2024/2025 data.
                2. VERIFY: If you cannot find specific numbers (fees, dates) on official university/gov sites, mark validation_status as 'UNCERTAIN'.
                3. ANSWER: Be concise but specific. Convert currencies to INR/USD.
                """
            )
        )
        
        # The new SDK returns a Python object directly if schema is used, 
        # but sometimes raw text JSON. We handle both.
        try:
            data = json.loads(response.text)
        except:
            data = response.parsed

        # Extract Grounding Metadata (Sources)
        sources = []
        if response.candidates[0].grounding_metadata.search_entry_point:
            # We just flag that sources exist; extracting raw HTML links is complex in the new object
            sources = ["Google Search Index"]

        return data, sources

    except Exception as e:
        return {"answer": f"⚠️ Tech Error: {str(e)}", "next_questions": [], "validation_status": "ERROR"}, []

# --- 4. UI LOGIC (Same as before) ---
st.title("🎓 UniGuide AI (New SDK)")

# Clickable Suggestions
if st.session_state.suggestions:
    cols = st.columns(len(st.session_state.suggestions))
    for i, suggestion in enumerate(st.session_state.suggestions):
        if cols[i].button(suggestion, key=f"sugg_{i}"):
            st.session_state.current_input = suggestion

# Input Handling
user_input = st.chat_input("Ask a question...")
if "current_input" in st.session_state:
    user_input = st.session_state.current_input
    del st.session_state.current_input

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.status("🔍 Searching & Validating...", expanded=True):
            data, sources = get_gemini_response(user_input)
            
        # UI: Show Validation Badge
        if data.get("validation_status") == "VERIFIED":
            st.success("✅ Data Verified against Search Results")
        elif data.get("validation_status") == "UNCERTAIN":
            st.warning("⚠️ Data Ambiguous - Check Official Links")
            
        st.markdown(data.get("answer"))
        
        st.session_state.messages.append({"role": "assistant", "content": data.get("answer")})
        st.session_state.suggestions = data.get("next_questions", [])
        st.rerun()
