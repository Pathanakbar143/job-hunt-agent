from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import os
import time
from agents.agent import job_agent_app
from utils.pdf_reader import extract_text_from_pdf,clean_text

# Your custom modules
from matcher import analyze_job_fit
from searcher import find_live_jobs, save_to_spreadsheet

load_dotenv()
gemini_key = os.getenv("GOOGLE_API_KEY")
serper_key = os.getenv("APIFY_API_KEY")

st.set_page_config(page_title="AI Job Search Agent", layout="wide")
st.title("🤖 AI Job Search Agent")

# --- SIDEBAR CONFIGURATION ---
# st.sidebar.header("API Configuration")
# gemini_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")
# serper_key = st.sidebar.text_input("Enter Serper.dev API Key", type="password")

# Session state to hold the resume text in memory
if "cleaned_text" not in st.session_state:
    st.session_state.cleaned_text = ""

# --- PHASE 1: KNOWLEDGE BASE (RESUME) ---
st.subheader("Phase 1: Load Knowledge Base")
st.write("Upload your resume so the AI can use it to score jobs against your actual experience.")
uploaded_file = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Processing resume into memory..."):
        with open("temp_resume.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        raw_text = extract_text_from_pdf("temp_resume.pdf")
        st.session_state.cleaned_text = clean_text(raw_text)
        
        st.success("Resume loaded successfully! You can now search for any role.")

# --- PHASE 2: SEARCH PARAMETERS ---
st.divider()
st.subheader("Phase 2: Define Your Target")
st.info("What kind of roles are we hunting for today?")

col1, col2 = st.columns(2)
with col1:
    target_role = st.text_input("Target Job Title", placeholder="e.g., Unity Developer, ML Engineer")
with col2:
    search_location = st.text_input("Target Location", placeholder="e.g., Remote, India")

# --- PHASE 3: AUTONOMOUS JOB HUNTER ---
st.divider()
st.subheader("Phase 3: Autonomous Job Agent")

if st.button("Deploy Agent"):
    # 1. Safety Checks
    if not serper_key or not gemini_key: # (Or your apify/rapidapi key variable)
        st.error("Please provide your API Keys in the sidebar.")
    elif not target_role:
        st.warning("Please enter a target job title to begin searching.")
    elif not st.session_state.cleaned_text:
        st.warning("Please upload your resume in Phase 1 first!")
    else:
        with st.spinner(f"🚀 Deploying Autonomous Agent to hunt for '{target_role}'..."):
            
            # 2. Define the Agent's Starting Memory (State)
            initial_state = {
                "target_role": target_role,
                "location": search_location,
                "resume_text": st.session_state.cleaned_text,
                "gemini_key": gemini_key,
                "apify_key": serper_key, # Pass whatever key you are using for scraping
                "search_attempts": 0,
                "raw_jobs": [],
                "scored_jobs": []
            }
            
            # 3. WAKE UP THE AGENT!
            # The agent will now search, expand the query if needed, and score the jobs autonomously.
            final_state = job_agent_app.invoke(initial_state)
            
            # 4. Extract the final results from the agent's memory
            scored_jobs = final_state.get("scored_jobs", [])
            final_search_term = final_state.get("target_role")
            
            # 5. Display the Results
            if scored_jobs:
                st.success(f"Agent finished! It successfully evaluated {len(scored_jobs)} jobs.")
                
                # If the agent had to expand the query, let the user know!
                if final_search_term != target_role:
                    st.info(f"🔄 The agent couldn't find enough jobs for '{target_role}', so it autonomously expanded the search to: '{final_search_term}'")
                
                # Save to CSV
                csv_file, new_count = save_to_spreadsheet(scored_jobs)
                
                if csv_file is not None:
                    st.download_button(
                        label="📥 Download Your Scored Jobs & Cover Letters (CSV)",
                        data=csv_file,
                        file_name="agent_tracked_jobs.csv",
                        mime="text/csv"
                    )
                
                # Display cleanly in Streamlit
                df = pd.DataFrame(scored_jobs)
                cols = ["title", "company", "Match Score", "location", "Fit Summary"]
                df_display = df[[c for c in cols if c in df.columns]]
                st.dataframe(df_display, width='stretch')
                
            else:
                st.error("The agent completed its workflow but couldn't find any valid jobs to score after multiple attempts.")

                