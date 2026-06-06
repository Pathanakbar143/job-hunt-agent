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
    
    # 3. Check if we have historical data saved on the server
    if os.path.exists(filename):
        existing_df = pd.read_csv(filename)
        # Combine old and new data
        combined_df = pd.concat([existing_df, new_df])
        # Drop duplicates using the unique job link
        final_df = combined_df.drop_duplicates(subset=['link'], keep='first')
        
        # Calculate how many genuinely new jobs we found
        new_jobs_added = len(final_df) - len(existing_df)
    else:
        # First time running
        final_df = new_df
        new_jobs_added = len(final_df)
        
    # 4. Save to the server so it remembers for next time
    final_df.to_csv(filename, index=False)
    
    # 5. USER PERSPECTIVE: Convert the final table into raw CSV text format
    # The .encode('utf-8') turns it into a format Streamlit can send as a download
    csv_for_download = final_df.to_csv(index=False).encode('utf-8')
    
    return csv_for_download, new_jobs_added