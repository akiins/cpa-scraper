# CPA Ontario Member Directory Scraper

A web scraper designed to extract member data from the CPA Ontario member directory.

## Overview

This tool uses Playwright to automate the browsing of the CPA Ontario member directory at https://myportal.cpaontario.ca/s/member-directory. It extracts information about CPA members including their names, designations, employers, and locations.

The scraper handles the dynamic pagination of the website, extracting data from each page until it reaches the end or a specified limit.

## Features

- Extracts member data from the CPA Ontario member directory
- Cleans member names (removes prefixes like ".,")
- Saves to a single CSV file
- Creates backup copies at specified intervals
- Validates data to ensure uniqueness

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

## Installation

1. Clone this repository:

   ```
   git clone <repository-url>
   cd cpa-scraper
   ```

2. Create and activate a virtual environment:

   ```
   # On macOS/Linux
   python -m venv venv
   source venv/bin/activate

   # On Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Install Playwright browsers:
   ```
   playwright install
   ```

## Usage

Run the scraper with:

```
python cpa_scraper.py
```

## Command Line Options

The script accepts several command-line options:

```
python cpa_scraper.py --help
```

Available options:

- `--url URL`: The URL of the CPA Ontario member directory
- `--output-dir DIR`: Directory where CSV files will be saved (default: "output")
- `--max-pages N`: Maximum number of pages to scrape (default: 80)
- `--headless`: Run browser in headless mode (default: True)
- `--backup-frequency N`: Create backup copy after every N pages (default: 10)

Examples:

```
# Run with visible browser for debugging
python cpa_scraper.py --headless=False

# Scrape only first 5 pages
python cpa_scraper.py --max-pages 5

# Create backup copies more frequently
python cpa_scraper.py --backup-frequency 5
```

## Output Files

The script creates two types of files in the output directory:

1. **Main data file**: `cpa_members_TIMESTAMP.csv` - Contains all scraped data, continuously updated as new pages are processed
2. **Backup file**: `backup_cpa_members_TIMESTAMP.csv` - Created at intervals specified by `backup-frequency`

Both files use the same timestamp generated at the start of the script run.

## Data Cleaning

The script automatically cleans member names by removing prefixes like ".,". For example:

- "., Abdul Basit" becomes "Abdul Basit"
- "., Akanksha" becomes "Akanksha"

## Troubleshooting

If the scraper is not correctly navigating through pages:

1. Set `--headless=False` in the command line options to see what's happening
2. Check the log file (`cpa_scraper.log`) for detailed information
3. Increase the polling attempts or interval if needed
