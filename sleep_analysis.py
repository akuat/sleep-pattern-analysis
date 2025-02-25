import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import seaborn as sns
from pathlib import Path
from bs4 import BeautifulSoup
import re
import traceback

def load_browser_history(filepath, days=30):
    """
    Load and parse last month of Chrome history
    """
    print(f"Loading last {days} days of Chrome history...")
    cutoff_date = datetime.now() - timedelta(days=days)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = []
    if isinstance(data, dict):
        entries = data.get('Browser History', [])
    else:
        entries = []
        
    for entry in entries:
        try:
            time_usec = int(entry['time_usec'])
            timestamp = datetime.fromtimestamp(time_usec / 1000000)
            
            # Only include recent entries
            if timestamp >= cutoff_date:
                records.append({
                    'timestamp': timestamp,
                    'source': 'chrome'
                })
        except (KeyError, ValueError) as e:
            continue
    
    print(f"Found {len(records)} Chrome entries in the last {days} days")
    return pd.DataFrame(records)

def load_youtube_history(filepath, days=30):
    """
    Load and parse last month of YouTube history
    Handles timestamps with timezone (EST)
    Uses chunked processing for better memory management
    """
    print(f"Loading last {days} days of YouTube history...")
    cutoff_date = datetime.now() - timedelta(days=days)
    records = []
    
    try:
        print("Reading file in chunks...")
        chunk_size = 1024 * 1024  # 1MB chunks
        chunks_processed = 0
        text_buffer = ""
        
        with open(filepath, 'r', encoding='utf-8') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                    
                text_buffer += chunk
                chunks_processed += 1
                
                if chunks_processed % 500 == 0:
                    print(f"Processed {chunks_processed} chunks...")
                
                # Look for timestamps in format "Feb 23, 2025, 8:28:19 AM EST"
                matches = re.finditer(r'([A-Z][a-z]{2} \d{1,2}, \d{4}, \d{1,2}:\d{2}:\d{2} [AP]M EST)', text_buffer)
                
                for match in matches:
                    try:
                        timestamp_str = match.group(1).replace(" EST", "")
                        timestamp = datetime.strptime(timestamp_str, '%b %d, %Y, %I:%M:%S %p')
                        
                        if timestamp >= cutoff_date:
                            records.append({
                                'timestamp': timestamp,
                                'source': 'youtube'
                            })
                    except ValueError:
                        continue
                
                # Keep only the last incomplete line in the buffer
                last_newline = text_buffer.rfind('\n')
                if last_newline != -1:
                    text_buffer = text_buffer[last_newline + 1:]
        
        print(f"Finished processing {chunks_processed} chunks")
        print(f"Found {len(records)} YouTube entries in the last {days} days")
        return pd.DataFrame(records)
                    
    except FileNotFoundError:
        print(f"Could not find YouTube history file at: {filepath}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error processing YouTube history: {str(e)}")
        traceback.print_exc()
        return pd.DataFrame()

def infer_sleep_periods(df, gap_threshold=4):
    """
    Infer sleep periods based on gaps in activity
    gap_threshold: minimum hours of inactivity to consider as sleep
    """
    # Sort timestamps and remove duplicates
    df = df.sort_values('timestamp').drop_duplicates(subset=['timestamp'])
    
    sleep_periods = []
    for i in range(len(df) - 1):
        gap = df.iloc[i+1]['timestamp'] - df.iloc[i]['timestamp']
        gap_hours = gap.total_seconds() / 3600
        
        # Only consider gaps between 4 and 14 hours as potential sleep periods
        if 4 <= gap_hours <= 14:
            sleep_start = df.iloc[i]['timestamp']
            sleep_end = df.iloc[i+1]['timestamp']
            
            sleep_periods.append({
                'sleep_start': sleep_start,
                'sleep_end': sleep_end,
                'duration_hours': gap_hours,
                'date': sleep_start.date(),
                'start_source': df.iloc[i]['source'],
                'end_source': df.iloc[i+1]['source']
            })
    
    return pd.DataFrame(sleep_periods)

def plot_sleep_patterns(sleep_df, output_dir='.'):
    """
    Create visualizations of sleep patterns
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Plot 1: Sleep duration over time
    plt.figure(figsize=(12, 6))
    plt.plot(sleep_df['date'], sleep_df['duration_hours'], marker='o')
    plt.title('Sleep Duration Over Time')
    plt.xlabel('Date')
    plt.ylabel('Hours of Sleep')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/sleep_duration.png')
    plt.close()

    # Plot 2: Sleep start and end times
    plt.figure(figsize=(12, 6))
    sleep_start_hours = [t.hour + t.minute/60 for t in sleep_df['sleep_start']]
    sleep_end_hours = [t.hour + t.minute/60 for t in sleep_df['sleep_end']]
    
    plt.scatter(sleep_df['date'], sleep_start_hours, 
                label='Sleep Start', alpha=0.6)
    plt.scatter(sleep_df['date'], sleep_end_hours, 
                label='Sleep End', alpha=0.6)
    plt.title('Sleep Schedule Pattern')
    plt.xlabel('Date')
    plt.ylabel('Hour of Day')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.ylim(0, 24)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/sleep_schedule.png')
    plt.close()

    # Plot 3: Distribution of sleep duration
    plt.figure(figsize=(10, 6))
    sns.histplot(data=sleep_df, x='duration_hours', bins=20)
    plt.title('Distribution of Sleep Duration')
    plt.xlabel('Hours of Sleep')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/sleep_duration_dist.png')
    plt.close()

    return {
        'duration_plot': f'{output_dir}/sleep_duration.png',
        'schedule_plot': f'{output_dir}/sleep_schedule.png',
        'distribution_plot': f'{output_dir}/sleep_duration_dist.png'
    }

def analyze_sleep_patterns(chrome_file, days=30):
    """
    Analyze sleep patterns from Chrome history data
    """
    print("Loading Chrome history...")
    browser_df = load_browser_history(chrome_file, days)
    print(f"Found {len(browser_df)} Chrome entries")
    
    # Infer sleep periods
    print("\nAnalyzing sleep patterns...")
    sleep_df = infer_sleep_periods(browser_df)
    
    # Generate statistics
    stats = {
        'average_sleep': sleep_df['duration_hours'].mean(),
        'std_sleep': sleep_df['duration_hours'].std(),
        'median_sleep': sleep_df['duration_hours'].median(),
        'num_days': len(sleep_df),
        'date_range': f"{sleep_df['date'].min()} to {sleep_df['date'].max()}",
        'most_common_sleep_hour': sleep_df['sleep_start'].dt.hour.mode().iloc[0],
        'most_common_wake_hour': sleep_df['sleep_end'].dt.hour.mode().iloc[0],
        'chrome_entries': len(browser_df)
    }
    
    # Create output directory
    output_dir = 'sleep_analysis_output'
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Create visualizations
    print("\nGenerating visualizations...")
    plot_paths = plot_sleep_patterns(sleep_df, output_dir)
    
    return sleep_df, stats, plot_paths

if __name__ == "__main__":
    # Update path to match your Chrome history file
    chrome_history_path = "History.json"
    
    print("\nStarting sleep pattern analysis...")
    sleep_data, statistics, plots = analyze_sleep_patterns(chrome_history_path)
    
    print("\nAnalysis Results:")
    print(f"Date range analyzed: {statistics['date_range']}")
    print(f"Total data points analyzed: {statistics['chrome_entries']}")
    print(f"Sleep patterns detected: {statistics['num_days']} nights")
    print(f"Average sleep duration: {statistics['average_sleep']:.2f} hours")
    print(f"Standard deviation: {statistics['std_sleep']:.2f} hours")
    print(f"Median sleep duration: {statistics['median_sleep']:.2f} hours")
    print(f"Most common sleep hour: {statistics['most_common_sleep_hour']}:00")
    print(f"Most common wake hour: {statistics['most_common_wake_hour']}:00")
    
    print("\nVisualization files created:")
    for name, path in plots.items():
        print(f"- {path}")