import os
import time
import argparse
import logging
from datetime import datetime
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cpa_scraper.log')
    ]
)

logger = logging.getLogger(__name__)

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
                logger.error(f"Error processing row: {str(e)}")
                continue
        
        return data
    except TimeoutError:
        logger.error("Timeout waiting for table to load.")
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
    logger.info(f"Data saved to {filepath}")
    
    return filepath

def verify_table_update(page, previous_first_member):
    """
    Verify that the table has been updated by checking if the first member name has changed
    """
    try:
        # Wait for the loading indicator to disappear (if there's one)
        page.wait_for_timeout(2000)  # Wait for any animations
        
        # Extract the first member name from the table
        first_row = page.query_selector("table.slds-table tbody tr")
        if not first_row:
            logger.warning("No rows found in table after pagination.")
            return False
        
        first_member = first_row.query_selector("th").inner_text().strip()
        
        # Check if the first member name has changed, indicating the table has updated
        if first_member != previous_first_member:
            logger.info(f"Table updated: First member changed from '{previous_first_member}' to '{first_member}'")
            return True
        else:
            logger.warning(f"Table did not update: First member still '{first_member}'")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying table update: {str(e)}")
        return False

def handle_pagination(page, current_data):
    try:
        # Store the first member name from the current page to verify the update
        first_member_current_page = current_data[0]['Member Name'] if current_data else None
        
        # Use a more specific selector for the Next button as shown in the image
        next_button = page.query_selector("button:has-text('Next')")
        if not next_button:
            logger.warning("Next button not found.")
            return False, None
        
        # Check if button is disabled
        if "disabled" in next_button.get_attribute("class") or next_button.is_disabled():
            logger.info("Next page button is disabled.")
            return False, None
        
        # Click the Next button
        logger.info("Clicking Next button...")
        next_button.click()
        
        # Wait for the table to update (could be various indicators)
        logger.info("Waiting for table content to update...")
        
        # Wait for any loading indicators to disappear
        page.wait_for_timeout(3000)  # Give some time for the update
        
        # Verify the table has updated
        if first_member_current_page and not verify_table_update(page, first_member_current_page):
            # Try again with a longer wait
            logger.warning("Table didn't update immediately, waiting longer...")
            page.wait_for_timeout(5000)
            if not verify_table_update(page, first_member_current_page):
                logger.error("Table update verification failed after retry.")
                return False, None
        
        # Extract the new data
        new_data = extract_table_data(page)
        
        if new_data:
            logger.info(f"Successfully extracted {len(new_data)} records from next page.")
            return True, new_data
        else:
            logger.warning("No data found on next page.")
            return False, None
            
    except Exception as e:
        logger.error(f"Error handling pagination: {str(e)}")
        return False, None

def parse_arguments():
    parser = argparse.ArgumentParser(description='CPA Ontario Member Directory Scraper')
    parser.add_argument('--url', default="https://myportal.cpaontario.ca/s/member-directory",
                        help='URL of the CPA Ontario member directory')
    parser.add_argument('--output-dir', default="output",
                        help='Directory to save output CSV files')
    parser.add_argument('--max-pages', type=int, default=80,
                        help='Maximum number of pages to scrape')
    parser.add_argument('--headless', action='store_true', default=True,
                        help='Run browser in headless mode')
    parser.add_argument('--save-frequency', type=int, default=10,
                        help='Save data to CSV after every N pages')
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    url = args.url
    output_dir = args.output_dir
    max_pages = args.max_pages
    headless = args.headless
    save_frequency = args.save_frequency
    
    all_data = []
    page_number = 1
    
    logger.info(f"Starting CPA scraper - Target URL: {url}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Maximum pages: {max_pages}")
    logger.info(f"Headless mode: {headless}")
    
    with sync_playwright() as p:
        try:
            logger.info("Launching browser...")
            # Launch browser with additional options
            browser = p.chromium.launch(
                headless=headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # Navigate to the page
            logger.info("Navigating to the page...")
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Wait for the page to load
            logger.info("Waiting for page to load...")
            page.wait_for_load_state("domcontentloaded", timeout=60000)
            page.wait_for_selector("table.slds-table", timeout=60000)
            time.sleep(5)  # Wait for dynamic content
            
            while page_number <= max_pages:
                # Extract data from current page
                logger.info(f"Extracting data from page {page_number}...")
                page_data = extract_table_data(page)
                
                if not page_data:
                    logger.warning("No data found on the current page.")
                    break
                
                # Validate data (basic check)
                if any(record in all_data for record in page_data):
                    logger.warning("Warning: Duplicate data detected. Might be stuck on the same page.")
                
                all_data.extend(page_data)
                logger.info(f"Found {len(page_data)} records on page {page_number}. Total records: {len(all_data)}")
                
                # Save incremental data (safer approach)
                if page_number % save_frequency == 0:
                    logger.info(f"Saving incremental data after {page_number} pages...")
                    save_to_csv(all_data, output_dir)
                
                # Handle pagination
                success, new_data = handle_pagination(page, page_data)
                if not success:
                    logger.info(f"Reached the last page ({page_number}) or encountered an error.")
                    break
                
                page_number += 1
                time.sleep(2)  # Wait between pages to avoid overwhelming the server
            
            # Save all collected data
            if all_data:
                final_file = save_to_csv(all_data, output_dir)
                logger.info(f"Total records collected: {len(all_data)}")
                logger.info(f"Final data saved to: {final_file}")
            else:
                logger.warning("No data was collected.")
            
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            # Save any data collected so far
            if all_data:
                logger.info("Saving data collected before error...")
                save_to_csv(all_data, output_dir)
        finally:
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main() 
