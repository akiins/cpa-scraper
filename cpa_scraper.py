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

def clean_member_name(name):
    """Clean up member names, removing prefixes like '.,', etc."""
    if name.startswith(".,"):
        return name[2:].strip()
    return name

def extract_table_data(page):
    try:
        table = page.wait_for_selector("table.slds-table", timeout=60000)
        
        # Extract data from the table
        rows = page.query_selector_all("table.slds-table tbody tr")
        data = []
        
        for row in rows:
            try:
                raw_member_name = row.query_selector("th").inner_text().strip()
                member_name = clean_member_name(raw_member_name)
                
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

def save_to_csv(data, filepath):
    """Save data to CSV file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)
    logger.info(f"Data saved to {filepath}")
    
    return filepath

def poll_for_table_update(page, previous_first_member, max_attempts=10, poll_interval=300):
    """
    Poll the page at short intervals to detect table updates as soon as they happen
    """
    logger.info(f"Polling for table update (previous first member: '{previous_first_member}')")
    
    for attempt in range(max_attempts):
        try:
            first_row = page.query_selector("table.slds-table tbody tr")
            if not first_row:
                logger.warning(f"Poll attempt {attempt+1}/{max_attempts}: No rows found")
                time.sleep(poll_interval / 1000)  # Convert ms to seconds
                continue
            
            first_member = clean_member_name(first_row.query_selector("th").inner_text().strip())
            
            if first_member != previous_first_member:
                logger.info(f"Table updated on attempt {attempt+1}: '{previous_first_member}' -> '{first_member}'")
                return True, first_member
                
            time.sleep(poll_interval / 1000)  # Convert ms to seconds
            
        except Exception as e:
            logger.error(f"Error during polling attempt {attempt+1}: {str(e)}")
            time.sleep(poll_interval / 1000)
    
    logger.warning(f"Table did not update after {max_attempts} polling attempts")
    return False, None

def handle_pagination(page, current_data):
    try:
        first_member_current_page = clean_member_name(current_data[0]['Member Name']) if current_data else None
        
        next_button = page.query_selector("button:has-text('Next')")
        if not next_button:
            logger.warning("Next button not found.")
            return False, None
        
        if "disabled" in next_button.get_attribute("class") or next_button.is_disabled():
            logger.info("Next page button is disabled.")
            return False, None
        
        logger.info("Clicking Next button...")
        next_button.click()
        
        logger.info("Polling for table content update...")
        updated, _ = poll_for_table_update(
            page, 
            first_member_current_page, 
            max_attempts=20,  # More attempts with shorter interval
            poll_interval=300  # 300ms between polls
        )
        
        if not updated:
            logger.warning("Table didn't update during polling, waiting longer...")
            page.wait_for_timeout(2000)
            updated, _ = poll_for_table_update(
                page, 
                first_member_current_page,
                max_attempts=5,
                poll_interval=500
            )
            
            if not updated:
                logger.error("Table update verification failed after extended waiting.")
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
                        help='Maximum number of pages to scrape (to prevent infinite loops)')
    parser.add_argument('--headless', action='store_true', default=True,
                        help='Run browser in headless mode')
    parser.add_argument('--backup-frequency', type=int, default=10,
                        help='Create backup copy after every N pages')
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    url = args.url
    output_dir = args.output_dir
    max_pages = args.max_pages
    headless = args.headless
    backup_frequency = args.backup_frequency
    
    all_data = []
    page_number = 1
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cpa_members_{timestamp}.csv"
    output_filepath = os.path.join(output_dir, filename)
    
    logger.info(f"Starting CPA scraper - Target URL: {url}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Output file: {filename}")
    logger.info(f"Maximum pages: {max_pages}")
    logger.info(f"Headless mode: {headless}")
    
    with sync_playwright() as p:
        try:
            logger.info("Launching browser...")
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
            time.sleep(2) 
            
            while page_number <= max_pages:
                logger.info(f"Extracting data from page {page_number}...")
                page_data = extract_table_data(page)
                
                if not page_data:
                    logger.warning("No data found on the current page.")
                    break
                
                if page_number > 1 and any(new_record['Member Name'] == all_data[-1]['Member Name'] for new_record in page_data[:5]):
                    logger.warning("Warning: Duplicate data detected. Might be stuck on the same page.")
                
                all_data.extend(page_data)
                logger.info(f"Found {len(page_data)} records on page {page_number}. Total records: {len(all_data)}")
                
                save_to_csv(all_data, output_filepath)
                
                if page_number % backup_frequency == 0:
                    backup_filepath = os.path.join(output_dir, f"backup_{filename}")
                    save_to_csv(all_data, backup_filepath)
                    logger.info(f"Created backup copy after {page_number} pages")
                
                success, new_data = handle_pagination(page, page_data)
                if not success:
                    logger.info(f"Reached the last page ({page_number}) or encountered an error.")
                    break
                
                page_number += 1
            
            logger.info(f"Total records collected: {len(all_data)}")
            
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            if all_data:
                logger.info("Saving data collected before error...")
                save_to_csv(all_data, output_filepath)
        finally:
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main() 
