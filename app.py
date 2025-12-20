import streamlit as st
from google import genai
from google.genai import types
import json
import re

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="UniGuide AI", page_icon="🎓", layout="centered")

# Custom CSS
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

client = genai.Client(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I can search for live university fees and deadlines. Try me!"}
    ]
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ["Tuition for MS CS in Germany", "Scholarships for Indians in UK"]

# --- 2. HELPER: CLEAN JSON ---
def clean_json_text(text):
    """
    Removes markdown backticks (```json ... ```) often added by LLMs
    so we can parse it as raw JSON.
    """
    # Remove opening ```json or ```
    text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.IGNORECASE)
    # Remove closing ```
    text = re.sub(r"```$", "", text.strip())
    return text.strip()

# --- 3. CORE LOGIC ---
def get_gemini_response(user_query):
    try:
        # Define Search Tool
        google_search_tool = types.Tool(
            google_search=types.GoogleSearch()
        )

        # Config: REMOVED 'response_mime_type' to fix the 400 Error
        generate_config = types.GenerateContentConfig(
            temperature=0.3,
            tools=[google_search_tool], 
            system_instruction="""
            You are an expert Overseas Education Counselor.
            1. SEARCH: Use Google Search to find the latest 2025 data.
            2. FORMAT: You MUST return a valid JSON object string. Do not add any text outside the JSON.
            3. SCHEMA: 
            {
                "answer": "Your markdown formatted answer here...",
                "next_questions": ["Question 1", "Question 2", "Question 3"]
            }
            """
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=f"User Query: {user_query}. Provide specific fees in INR/USD and deadlines.",
            config=generate_config
        )

        if response.text:
            # Manually clean and parse because we removed the strict JSON mode
            clean_text = clean_json_text(response.text)
            
            try:
                data = json.loads(clean_text)
            except json.JSONDecodeError:
                # Fallback if model fails to give JSON (rare with 2.0 Flash)
                return response.text, [], response.candidates[0].grounding_metadata

            metadata = None
            if response.candidates and response.candidates[0].grounding_metadata:
                metadata = response.candidates[0].grounding_metadata
                
            return data.get("answer", "No answer found."), data.get("next_questions", []), metadata
        else:
            return "No response generated.", [], None

    except Exception as e:
        return f"⚠️ Error: {str(e)}", [], None

# --- 4. UI LAYOUT ---
st.title("🎓 UniGuide AI")
st.caption("Powered by Gemini 2.0 Flash • Live Grounding")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

selected_suggestion = None
if st.session_state.suggestions:
    st.write("Suggestions:")
    cols = st.columns(len(st.session_state.suggestions))
    for i, suggestion in enumerate(st.session_state.suggestions):
        if cols[i].button(suggestion, key=f"sugg_{i}"):
            selected_suggestion = suggestion

user_input = st.chat_input("Ask a question...")
if selected_suggestion: user_input = selected_suggestion

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

if st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.status("🔍 Searching global databases...", expanded=True) as status:
            answer, new_suggestions, metadata = get_gemini_response(st.session_state.messages[-1]["content"])
            status.update(label="Research Complete", state="complete", expanded=False)
            
        st.markdown(answer)
        
        if metadata and metadata.search_entry_point:
            st.caption(f"ℹ️ Verified with Google Search Grounding")

    st.session_state.messages.append({"role": "assistant", "content": answer})
    if new_suggestions:
        st.session_state.suggestions = new_suggestions
    st.rerun()
