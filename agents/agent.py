from typing import TypedDict, List
from langgraph.graph import StateGraph, END
import streamlit as st
from utils.extractor import extract_real_title
# Import your existing tools
from searcher import find_live_jobs
from matcher import analyze_job_fit
from local_scorer import calculate_local_match_score

# 1. Define the Agent's Memory (State)
class JobAgentState(TypedDict):
    target_role: str
    location: str
    resume_text: str
    gemini_key: str
    apify_key: str  # Or apify_key depending on what you used
    search_attempts: int
    raw_jobs: List[dict]
    scored_jobs: List[dict]

# 2. Define the Nodes (Actions)

def search_for_jobs(state: JobAgentState):
    """Hits the API to find jobs based on the current target_role."""
    print(f"🕵️‍♂️ Searching for: {state['target_role']}...")
    
    jobs = find_live_jobs(
        state["target_role"], 
        state["location"], 
        state["apify_key"], 
        max_results=5
    )
    
    # Update the state memory
    if jobs != "API_ERROR" and jobs:
        state["raw_jobs"] = jobs
    else:
        state["raw_jobs"] = []
        
    state["search_attempts"] += 1
    return state

def expand_search_query(state: JobAgentState):
    """If no jobs are found, the AI rewrites the search query to try again."""
    print("🔄 Not enough jobs found. Expanding search query...")
    
    # In a full production app, you would use an LLM here to generate synonyms.
    # For now, we will do a simple fallback logic to demonstrate the graph loop.
    old_role = state["target_role"]
    state["target_role"] = f"{old_role} OR Software Engineer" 
    
    return state

def score_found_jobs(state: JobAgentState):
    """Runs the LangChain matcher on the successfully found jobs."""
    print("🎯 Scoring jobs...")
    scored = []
    print("Raw Jobs in State :- ",state["raw_jobs"])
    for job in state["raw_jobs"]:
        # 1. Pull data using the EXACT keys from the Apify scraper
        job_desc = job.get("Job_Desc", "")

        # ==========================================
        
        # job_link = job.get("Application Link", "No link provided")
        # fallback_title = job.get("job_title", "Unknown Role")

        # 2. Reconstruct the real title from the URL 
        # real_title = job.get("job_title") #extract_real_title(job_link, fallback_title)

        # 3. Standardize the dictionary keys so Pandas/Streamlit don't crash
        # job["link"] = job_link
        # job["title"] = real_title  
        # job["company"] = job.get("company_name","Company Not Listed") 
        # ==========================================
        
        print("Job Description for Scoring :- ",job_desc)
        if job_desc:
            # --- Phase 3 Local Vector Scoring ---
            math_score = calculate_local_match_score(state["resume_text"],job_desc)
            job["Match Score"] = f"{math_score}%"

            # --- Phase 1: LangChain (Fit Summary & Cover Letter only) ---
            report = analyze_job_fit(state["resume_text"], job_desc, state["gemini_key"])
            job["Fit Summary"] = report.fit_analysis
            job["Cover Letter Draft"] = report.cover_letter
            job["Title"] = report.job_title   # Use extracted title if available
            job["Company"] = report.company_name   # Use extracted company
        else:
            job["Match Score"] = "N/A"
            
        scored.append(job)
        
    state["scored_jobs"] = scored
    return state

# 3. Define the Routing Logic
def route_after_search(state: JobAgentState):
    """Decides if we should score the jobs, or try searching again."""
    
    # If we found jobs, proceed to scoring
    if len(state["raw_jobs"]) > 0:
        return "score_jobs"
        
    # If we found 0 jobs, but we haven't tried 3 times yet, try expanding the query
    elif state["search_attempts"] < 3:
        return "expand_query"
        
    # If we failed 3 times, give up and end the graph
    else:
        return END
    
# 4. Build and Compile the Graph
workflow = StateGraph(JobAgentState)

# Add the nodes
workflow.add_node("search_jobs", search_for_jobs)
workflow.add_node("expand_query", expand_search_query)
workflow.add_node("score_jobs", score_found_jobs)

# Define the starting point
workflow.set_entry_point("search_jobs")

# Add the conditional edges (The Brain)
workflow.add_conditional_edges(
    "search_jobs",
    route_after_search,
    {
        "score_jobs": "score_jobs",
        "expand_query": "expand_query",
        END: END
    }
)

# If it expands the query, it MUST go back to search again
workflow.add_edge("expand_query", "search_jobs")

# If it scores the jobs, the workflow is finished
workflow.add_edge("score_jobs", END)

# Compile it into a runnable application!
job_agent_app = workflow.compile()