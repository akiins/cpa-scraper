# CPA Ontario Member Directory Scraper

A web scraper designed to extract member data from the CPA Ontario member directory.

## Overview

This tool uses Playwright to automate the browsing of the CPA Ontario member directory at https://myportal.cpaontario.ca/s/member-directory. It extracts information about CPA members including their names, designations, employers, and locations.

The scraper handles the dynamic pagination of the website, extracting data from each page until it reaches the end or a specified limit.

## Features

- Extracts member data from the CPA Ontario member directory
- Handles dynamic page updates without URL changes
- Saves data incrementally to prevent data loss in case of errors
- Validates data to ensure uniqueness
- Exports data to CSV format with timestamps

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

The script will:

1. Open a browser window (visible when `headless=False`)
2. Navigate to the CPA Ontario member directory
3. Extract data from the table on each page
4. Handle pagination by clicking the "Next" button
5. Save data to the `output` directory in CSV format

## Configuration

You can modify the following parameters in the `main()` function of the script:

- `url`: The URL of the CPA Ontario member directory
- `output_dir`: Directory where CSV files will be saved
- `max_pages`: Maximum number of pages to scrape (to prevent infinite loops)

## Troubleshooting

If the scraper is not correctly navigating through pages:

1. Set `headless=False` in the browser launch options to see what's happening
2. Increase the wait times in the pagination handling
3. Check the console output for error messages

## License

[Include license information here]
