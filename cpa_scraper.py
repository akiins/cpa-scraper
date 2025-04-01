import os
import time
from datetime import datetime
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError

def extract_table_data(page):
    try:
        # Wait for the table to be present with increased timeout
        table = page.wait_for_selector("table.slds-table", timeout=60000)
        
        # Extract data from the table
        rows = page.query_selector_all("table.slds-table tbody tr")
        data = []
        
        for row in rows:
            try:
                member_name = row.query_selector("th").inner_text().strip()
                cols = row.query_selector_all("td")
                if len(cols) >= 3:  # Ensure we have all required columns
                    data.append({
                        'Member Name': member_name,
                        'Designations': cols[0].inner_text().strip(),
                        'Employer': cols[1].inner_text().strip(),
                        'Employer City': cols[2].inner_text().strip()
                    })
            except Exception as e:
                print(f"Error processing row: {str(e)}")
                continue
        
        return data
    except TimeoutError:
        print("Timeout waiting for table to load.")
        return []

def save_to_csv(data, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cpa_members_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)
    
    # Convert data to DataFrame and save to CSV
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)
    print(f"Data saved to {filepath}")

def wait_for_table_update(page, previous_data):
    try:
        # Wait for the table to be visible and stable
        table = page.wait_for_selector("table.slds-table", state="visible", timeout=10000)
        
        # Get the current data
        current_data = extract_table_data(page)
        
        # If we got new data and it's different from previous, return it
        if current_data and current_data != previous_data:
            return current_data
            
        return None
    except Exception as e:
        print(f"Error during table update check: {str(e)}")
        return None

def handle_pagination(page, previous_data):
    try:
        # Look for next page button
        next_button = page.query_selector("button.slds-button.slds-button_neutral")
        if not next_button:
            print("No next page button found.")
            return False, None
            
        # Check if button is disabled
        if "disabled" in next_button.get_attribute("class"):
            print("Next page button is disabled.")
            return False, None
            
        # Click the button
        print("Clicking next page button...")
        next_button.click()
        
        # Wait for table content to update
        print("Waiting for table content to update...")
        new_data = wait_for_table_update(page, previous_data)
        
        if new_data:
            print("Table content updated successfully.")
            return True, new_data
        else:
            print("Table content did not update.")
            return False, None
            
    except Exception as e:
        print(f"Error handling pagination: {str(e)}")
        return False, None

def main():
    url = "https://myportal.cpaontario.ca/s/member-directory"
    output_dir = "output"
    all_data = []
    page_number = 1
    
    with sync_playwright() as p:
        try:
            # Launch browser with additional options
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # Navigate to the page
            print("Navigating to the page...")
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Wait for the page to load
            print("Waiting for page to load...")
            page.wait_for_load_state("domcontentloaded", timeout=60000)
            time.sleep(5)  # Wait for dynamic content
            
            while True:
                # Extract data from current page
                print(f"Extracting data from page {page_number}...")
                page_data = extract_table_data(page)
                if not page_data:
                    print("No data found on the current page.")
                    break
                    
                all_data.extend(page_data)
                print(f"Found {len(page_data)} records on page {page_number}.")
                
                # Handle pagination
                success, new_data = handle_pagination(page, page_data)
                if not success:
                    print("No more pages to process.")
                    break
                
                page_number += 1
                time.sleep(1)  # Short wait between pages
            
            # Save all collected data
            if all_data:
                save_to_csv(all_data, output_dir)
                print(f"Total records collected: {len(all_data)}")
            else:
                print("No data was collected.")
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main() 
