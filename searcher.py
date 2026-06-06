from apify_client import ApifyClient
import pandas as pd
import os


def find_live_jobs(job_title: str, location: str, apify_api_key: str, max_results: int = 10):
    """
    Commands the OFFICIAL Apify Cloud Actor to execute a Google search and returns 
    the results, safely extraction fields from the Run object instance.
    """
    # Removed the strict trailing slashes so Apify's internal filter doesn't panic
    search_query = (
    f'{job_title} {location} '
    f'(site:naukri.com/job-listings '
    f'OR site:indeed.com/viewjob '
    f'OR site:linkedin.com/jobs/view)')
    
    client = ApifyClient(apify_api_key)
    
    run_input = {
        "queries": search_query,
        "maxPagesPerQuery": 1,
        "resultsPerPage": max_results
    }
    
    jobs_found = []
    
    try:
        # 1. Call the official Apify actor
        run = client.actor("apify/google-search-scraper").call(run_input=run_input)
        
        # 2. Extract the dataset ID safely whether 'run' is an object or a dict
        if isinstance(run, dict):
            dataset_id = run.get("defaultDatasetId")
        else:
            # It's a 'Run' object instance, use attribute access
            dataset_id = getattr(run, "default_dataset_id", None) or getattr(run, "defaultDatasetId", None)
            
        if not dataset_id:
            return "ERROR: Could not locate defaultDatasetId from Apify run configuration."
            
        # 3. Fetch the results from the Actor's cloud dataset
        dataset_items = client.dataset(dataset_id).iterate_items()
        
        for page_data in dataset_items:
            # Extract organic results array from the page payload
            organic_results = page_data.get("organicResults", [])
            
            for result in organic_results:
                link = result.get("url", "")
                snippet = result.get("description", "No description available.")
                
                if link:
                    jobs_found.append({
                        "Job_Desc": snippet,
                        "Application Link": link,
                        "Status": "Pending Review"
                    })
                    
    except Exception as e:
        print(f"[ERROR] Apify Gateway failed: {str(e)}")
        return f"ERROR: {str(e)}"
        
    return jobs_found

def save_to_spreadsheet(jobs_data: list, filename: str = "jobs_database.csv"):
    # 1. Safety check for empty or error data
    if not jobs_data or (isinstance(jobs_data, str) and jobs_data.startswith("ERROR:")):
        return None, 0
        
    # 2. Convert new jobs to a DataFrame
    new_df = pd.DataFrame(jobs_data)
    
    # --- HARMONIZATION: Fix new incoming data ---
    if 'link' not in new_df.columns and 'Application Link' in new_df.columns:
        new_df['link'] = new_df['Application Link']
    
    # 3. Check if we have historical data saved on the server
    if os.path.exists(filename):
        try:
            existing_df = pd.read_csv(filename)
            
            # --- HARMONIZATION: Fix old saved data ---
            if 'Application Link' in existing_df.columns and 'link' not in existing_df.columns:
                existing_df['link'] = existing_df['Application Link']
            if 'Job Title/Search Term' in existing_df.columns and 'title' not in existing_df.columns:
                existing_df['title'] = existing_df['Job Title/Search Term']
                
            # Combine old and new data safely
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        except Exception as e:
            print(f"Error reading old CSV, starting fresh: {e}")
            combined_df = new_df
            existing_df = pd.DataFrame() # Empty fallback
    else:
        # First time running
        combined_df = new_df
        existing_df = pd.DataFrame() # Empty fallback
        
    # --- SAFE DUPLICATE CHECK ---
    if 'link' in combined_df.columns:
        final_df = combined_df.drop_duplicates(subset=['link'], keep='first')
    else:
        # Extreme fallback if 'link' still doesn't exist
        fallback_col = 'Application Link' if 'Application Link' in combined_df.columns else combined_df.columns[0]
        final_df = combined_df.drop_duplicates(subset=[fallback_col], keep='first')
        
    # Calculate how many genuinely new jobs we found
    new_jobs_added = len(final_df) - len(existing_df)
        
    # 4. Save to the server so it remembers for next time
    final_df.to_csv(filename, index=False)
    
    # 5. USER PERSPECTIVE: Convert the final table into raw CSV text format
    csv_for_download = final_df.to_csv(index=False).encode('utf-8')
    
    # max(0, ...) ensures we never return a negative number by accident
    return csv_for_download, max(0, new_jobs_added)