# CPA Ontario Member Directory Scraper

This script scrapes the CPA Ontario member directory and saves the data to a CSV file.

## Requirements

- Python 3.8 or higher
- Chrome browser installed
- Required Python packages (listed in requirements.txt)

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the script:
```bash
python cpa_scraper.py
```

The script will:
1. Navigate to the CPA Ontario member directory
2. Extract member information from all pages
3. Save the data to a CSV file in the `output` directory
4. The CSV filename will include a timestamp (format: cpa_members_YYYYMMDD_HHMMSS.csv)

## Output Format

The CSV file will contain the following columns:
- Member Name
- Designations
- Employer
- Employer City

## Notes

- The script runs Chrome in headless mode
- It includes error handling and proper cleanup of resources
- The script automatically handles pagination 
