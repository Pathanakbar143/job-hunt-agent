import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

def sync_with_google_sheet(new_df, sheet_url):
    """Connects to a user's Google Sheet, merges new jobs, and updates the cloud file."""
    
    # 1. Authenticate with Google using Streamlit Secrets
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        # Pull the dictionary of credentials from Streamlit secrets
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # 2. Open the user's spreadsheet and get the first tab
        sheet = client.open_by_url(sheet_url).sheet1
        
        # 3. Pull all existing data from their sheet
        existing_data = sheet.get_all_records()
        existing_df = pd.DataFrame(existing_data)
        
        # 4. Harmonize and Merge (Just like your local CSV logic!)
        if not existing_df.empty:
            # Ensure links are formatted correctly to prevent KeyErrors
            if 'Application Link' in existing_df.columns and 'link' not in existing_df.columns:
                existing_df['link'] = existing_df['Application Link']
            
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            final_df = combined_df.drop_duplicates(subset=['link'], keep='first')
        else:
            final_df = new_df
            
        # 5. Clean up the data for Google Sheets (handle NaN/Infinity)
        final_df = final_df.fillna("")
            
        # 6. Wipe the old sheet clean and upload the newly merged data
        sheet.clear()
        sheet.update([final_df.columns.values.tolist()] + final_df.values.tolist())
        
        # Calculate how many brand new jobs were successfully added
        new_jobs_added = len(final_df) - len(existing_df) if not existing_df.empty else len(final_df)
        
        return True, max(0, new_jobs_added)
        
    except Exception as e:
        print(f"Google Sheets API Error: {e}")
        return False, str(e)