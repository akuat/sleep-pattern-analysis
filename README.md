# sleep-pattern-analysis
# Sleep Pattern Analysis from Browser History

This project analyzes personal sleep patterns by examining gaps in Google Chrome browsing activity. Using timestamp data from Google Takeout, the program infers potential sleep periods and creates visualizations to help understand sleep habits.

## Project Overview

This analysis works by:
- Processing Chrome browser history from Google Takeout data
- Identifying periods of inactivity that likely correspond to sleep
- Generating visualizations and statistics about sleep patterns
- Providing insights into sleep duration and timing

## Requirements

- Python 3.x
- Required Python packages:
  - pandas
  - matplotlib
  - seaborn

## Setup and Usage

1. Download your Google Chrome history from Google Takeout
   - Go to [Google Takeout](https://takeout.google.com)
   - Deselect all and select only Chrome
   - Download your data

2. Install required Python packages:
```bash
pip install pandas matplotlib seaborn
```

3. Place your `BrowserHistory.json` file in the project directory

4. Run the analysis:
```bash
python sleep_analysis.py
```

## Output

The script generates three visualizations in the `sleep_analysis_output` directory:
- Sleep duration over time
- Sleep schedule pattern (sleep start and end times)
- Distribution of sleep duration

## Privacy Note

This repository contains only the analysis code. The actual browser history data is excluded from the repository through `.gitignore` to maintain privacy.

## CS 4501 Project

This project was created as part of CS 4501 - Digital Footprint Analysis. The goal was to analyze personal digital traces to understand behavioral patterns.