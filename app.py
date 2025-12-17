import streamlit as st
import google.generativeai as genai
import time
import json

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(
    page_title="UniGuide AI",
    page_icon="🎓",
    layout="centered"
)

# Custom CSS for a "Beautiful" Interface
st.markdown("""
<style>
    /* Chat Bubble Styling */
    .stChatMessage {
        border-radius: 15px; 
        padding: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    /* Suggestion Button Styling */
    .stButton button {
        border-radius: 20px;
        border: 1px solid #E0E0E0;
        background-color: #F8F9FA;
        color: #424242;
        font-size: 0.85rem;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }
    .stButton button:hover {
        border-color: #6C63FF;
        color: #6C63FF;
        background-color: #F0F0FF;
    }
    /* Header Styling */
    h1 { color: #2C3E50; }
    .caption { color: #7F8C8D; }
</style>
""", unsafe_allow_html=True)

# API Setup (Robust error handling for missing keys)
try:
    # Try getting key from Streamlit Secrets (Production) or local environment
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ API Key missing. Please set GEMINI_API_KEY in Streamlit secrets.")
    st.stop()

genai.configure(api_key=api_key)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your AI Counselor for International Studies. I can check live university data for you. Try asking about tuition fees, deadlines, or scholarships!"}
    ]
if "suggestions" not in st.session_state:
    st.session_state.suggestions = [
        "Tuition fees for MS CS at TU Munich",
        "Scholarships for Indian students in UK",
        "Top 5 universities for Data Science in USA"
    ]

# --- 2. CORE FUNCTIONS ---

def get_gemini_response(user_query):
    """
    1. Performs Grounded Generation (Search)
    2. Validates data
    3. Generates 3 relevant follow-up questions
    """
    
    # Model A: The Researcher + Logic Engine
    # We ask it to return JSON to easily separate the "Answer" from the "Suggestions"
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash-lite',  
        tools='google_search_retrieval',
        system_instruction="""
        You are an expert Overseas Education Counselor for Indian Students.
        1. SEARCH: Always use Google Search to find the latest 2024/2025 data.
        2. VALIDATE: If data is ambiguous, state that clearly.
        3. FORMAT: Output your response in valid JSON format with two keys:
           - "answer": The markdown formatted answer to the user.
           - "next_questions": A list of 3 short, relevant follow-up questions the user might want to ask next.
        """
    )
    
    try:
        response = model.generate_content(
            f"User Query: {user_query}. \nProvide detailed specific info (fees in INR/USD, deadlines)."
        )
        
        # Parse the JSON response
        # Gemini usually outputs JSON inside ```json ... ``` blocks, we need to clean it
        text = response.text
        if "```json" in text:
            text = text.replace("```json", "").replace("```", "")
        
        data = json.loads(text)
        return data["answer"], data["next_questions"], response.candidates[0].grounding_metadata
        
    except Exception as e:
        # Fallback if JSON parsing fails or API errors
        return f"I found some info but hit a technical snag: {str(e)}", [], None

# --- 3. THE UI LAYOUT ---

st.title("🎓 UniGuide AI")
st.caption("Live Research • Validated Data • Interactive Suggestions")

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 4. CLICKABLE SUGGESTIONS LOGIC ---
# We display suggestions above the input box. 
# If a user clicks one, we treat it exactly like a typed input.

selected_suggestion = None

if st.session_state.suggestions:
    st.write("Compare or Explore:")
    cols = st.columns(len(st.session_state.suggestions))
    for i, suggestion in enumerate(st.session_state.suggestions):
        if cols[i].button(suggestion, key=f"sugg_{i}"):
            selected_suggestion = suggestion

# --- 5. MAIN INTERACTION LOOP ---

# Check if input came from a Button click OR the Chat Input box
user_input = st.chat_input("Ask a question...")
if selected_suggestion:
    user_input = selected_suggestion

if user_input:
    # 1. Append User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    # Force a rerun to show the user message immediately before processing
    st.rerun()

# Processing (This runs after the rerun triggers)
if st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.status("🔍 Researching Global Databases...", expanded=True) as status:
            st.write("Connecting to Google Search Index...")
            last_query = st.session_state.messages[-1]["content"]
            
            # CALL THE API
            answer, new_suggestions, metadata = get_gemini_response(last_query)
            
            st.write("Verifying Sources...")
            time.sleep(0.5) # UX polish
            status.update(label="Research Complete", state="complete", expanded=False)
            
        # Display Answer
        st.markdown(answer)
        
        # Display Sources (if available)
        if metadata and metadata.search_entry_point:
             st.caption(f"ℹ️ content grounded in Google Search results")

    # Update State
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.suggestions = new_suggestions # Update the chips for next turn
    st.rerun() # Rerun to display the NEW suggestions at the bottom
