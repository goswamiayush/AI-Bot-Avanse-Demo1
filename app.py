import streamlit as st
from google import genai
from google.genai import types
import json
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="UniGuide AI (v2.0)", page_icon="🎓", layout="centered")

# Custom CSS for the "Beautiful" UI
st.markdown("""
<style>
    .stChatMessage {border-radius: 15px; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);}
    .stButton button {border-radius: 20px; background-color: #F8F9FA; border: 1px solid #E0E0E0;}
    .stButton button:hover {border-color: #6C63FF; color: #6C63FF;}
</style>
""", unsafe_allow_html=True)

# API Setup
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ API Key missing. Please set GEMINI_API_KEY in Streamlit secrets.")
    st.stop()

# Initialize the NEW Client (v1.0 SDK)
client = genai.Client(api_key=api_key)

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm running on the new Google GenAI SDK. Ask me about universities, fees, or deadlines!"}
    ]
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ["Tuition for MS CS in Germany", "Scholarships for Indians in UK", "Best ROI universities in USA"]

# --- 2. CORE LOGIC (NEW SDK SYNTAX) ---

def get_gemini_response(user_query):
    """
    Uses the new google-genai SDK to perform Grounded Search + JSON extraction
    """
    try:
        # Define the Search Tool (New Syntax)
        google_search_tool = types.Tool(
            google_search=types.GoogleSearch() 
        )

        # Define the Generation Config (New Syntax)
        generate_config = types.GenerateContentConfig(
            temperature=0.3,
            tools=[google_search_tool],  # Enable Grounding
            response_mime_type="application/json", # Force JSON output
            system_instruction="""
            You are an expert Overseas Education Counselor.
            1. SEARCH: Use Google Search to find the latest 2025 data.
            2. FORMAT: Output valid JSON with keys: "answer" (markdown text) and "next_questions" (list of 3 strings).
            3. VALIDATE: If specific fees/dates are not found, mention that clearly.
            """
        )

        # Generate Content
        # We use 'gemini-2.0-flash' as it is best optimized for the new SDK & Grounding
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=f"User Query: {user_query}. Provide specific fees in INR/USD and deadlines.",
            config=generate_config
        )

        # Parse Response
        if response.text:
            data = json.loads(response.text)
            
            # Extract Grounding Metadata (Citations)
            # The new SDK puts metadata in response.candidates[0].grounding_metadata
            metadata = None
            if response.candidates and response.candidates[0].grounding_metadata:
                metadata = response.candidates[0].grounding_metadata
                
            return data.get("answer", "No answer found."), data.get("next_questions", []), metadata
        else:
            return "No response generated.", [], None

    except Exception as e:
        return f"⚠️ SDK Error: {str(e)}", [], None

# --- 3. UI LAYOUT ---

st.title("🎓 UniGuide AI")
st.caption("Powered by Google Gen AI SDK v1.0 • Gemini 2.0 Flash")

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Suggestion Chips
selected_suggestion = None
if st.session_state.suggestions:
    st.write("Explore:")
    cols = st.columns(len(st.session_state.suggestions))
    for i, suggestion in enumerate(st.session_state.suggestions):
        if cols[i].button(suggestion, key=f"sugg_{i}"):
            selected_suggestion = suggestion

# Input Handling
user_input = st.chat_input("Ask a question...")
if selected_suggestion: user_input = selected_suggestion

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

# Response Generation
if st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.status("🔍 Searching global databases (Gemini 2.0)...", expanded=True) as status:
            
            answer, new_suggestions, metadata = get_gemini_response(st.session_state.messages[-1]["content"])
            
            status.update(label="Research Complete", state="complete", expanded=False)
            
        st.markdown(answer)
        
        # New SDK Grounding Metadata Display
        if metadata and metadata.search_entry_point:
            st.caption(f"ℹ️ Verified with Google Search Grounding")
            # You can extract specific links from metadata.grounding_chunks if needed

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.suggestions = new_suggestions
    st.rerun()
