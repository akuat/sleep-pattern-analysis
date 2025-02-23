import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import seaborn as sns
from pathlib import Path

def load_browser_history(filepath):
    """
    Load and parse Chrome browser history from Google Takeout JSON
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract timestamps and URLs
    timestamps = []
    for entry in data['Browser History']:
        time_usec = int(entry['time_usec'])
        # Convert microseconds to datetime
        timestamp = datetime.fromtimestamp(time_usec / 1000000)
        timestamps.append(timestamp)
    
    return pd.DataFrame({'timestamp': timestamps})

def load_youtube_history(filepath):
    """
    Load and parse YouTube history from Google Takeout JSON
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    timestamps = []
    for entry in data:
        # YouTube data typically has a different timestamp format
        time_str = entry['time']
        timestamp = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        timestamps.append(timestamp)
    
    return pd.DataFrame({'timestamp': timestamps})

def infer_sleep_periods(df, gap_threshold=4):
    """
    Infer sleep periods based on gaps in activity
    gap_threshold: minimum hours of inactivity to consider as sleep
    """
    # Sort timestamps
    df = df.sort_values('timestamp')
    
    sleep_periods = []
    for i in range(len(df) - 1):
        gap = df.iloc[i+1]['timestamp'] - df.iloc[i]['timestamp']
        if gap.total_seconds() / 3600 >= gap_threshold:
            sleep_start = df.iloc[i]['timestamp']
            sleep_end = df.iloc[i+1]['timestamp']
            sleep_periods.append({
                'sleep_start': sleep_start,
                'sleep_end': sleep_end,
                'duration_hours': gap.total_seconds() / 3600
            })
    
    return pd.DataFrame(sleep_periods)

def plot_sleep_patterns(sleep_df):
    """
    Create visualizations of sleep patterns
    """
    # Plot 1: Sleep duration over time
    plt.figure(figsize=(12, 6))
    plt.plot(sleep_df['sleep_start'], sleep_df['duration_hours'], marker='o')
    plt.title('Sleep Duration Over Time')
    plt.xlabel('Date')
    plt.ylabel('Hours of Sleep')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('sleep_duration.png')
    plt.close()

    # Plot 2: Sleep start and end times
    plt.figure(figsize=(12, 6))
    sleep_start_hours = [t.hour + t.minute/60 for t in sleep_df['sleep_start']]
    sleep_end_hours = [t.hour + t.minute/60 for t in sleep_df['sleep_end']]
    
    plt.scatter(sleep_df['sleep_start'].dt.date, sleep_start_hours, 
                label='Sleep Start', alpha=0.6)
    plt.scatter(sleep_df['sleep_start'].dt.date, sleep_end_hours, 
                label='Sleep End', alpha=0.6)
    plt.title('Sleep Schedule Pattern')
    plt.xlabel('Date')
    plt.ylabel('Hour of Day')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('sleep_schedule.png')
    plt.close()

    # Plot 3: Distribution of sleep duration
    plt.figure(figsize=(10, 6))
    sns.histplot(data=sleep_df, x='duration_hours', bins=20)
    plt.title('Distribution of Sleep Duration')
    plt.xlabel('Hours of Sleep')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig('sleep_duration_dist.png')
    plt.close()

def analyze_sleep_patterns(chrome_file, youtube_file):
    """
    Main function to analyze sleep patterns from Google Takeout data
    """
    # Load data
    browser_df = load_browser_history(chrome_file)
    youtube_df = load_youtube_history(youtube_file)
    
    # Combine all activity
    all_activity = pd.concat([
        browser_df,
        youtube_df
    ]).sort_values('timestamp')
    
    # Infer sleep periods
    sleep_df = infer_sleep_periods(all_activity)
    
    # Generate statistics
    stats = {
        'average_sleep': sleep_df['duration_hours'].mean(),
        'std_sleep': sleep_df['duration_hours'].std(),
        'median_sleep': sleep_df['duration_hours'].median(),
        'num_days': len(sleep_df),
        'most_common_sleep_hour': sleep_df['sleep_start'].dt.hour.mode().iloc[0],
        'most_common_wake_hour': sleep_df['sleep_end'].dt.hour.mode().iloc[0]
    }
    
    # Create visualizations
    plot_sleep_patterns(sleep_df)
    
    return sleep_df, stats

if __name__ == "__main__":
    # Update these paths to match your Google Takeout files
    chrome_history_path = "Takeout/Chrome/BrowserHistory.json"
    youtube_history_path = "Takeout/YouTube/history/watch-history.json"
    
    sleep_data, statistics = analyze_sleep_patterns(chrome_history_path, youtube_history_path)
    
    print("\nSleep Statistics:")
    print(f"Average sleep duration: {statistics['average_sleep']:.2f} hours")
    print(f"Standard deviation: {statistics['std_sleep']:.2f} hours")
    print(f"Median sleep duration: {statistics['median_sleep']:.2f} hours")
    print(f"Most common sleep hour: {statistics['most_common_sleep_hour']}:00")
    print(f"Most common wake hour: {statistics['most_common_wake_hour']}:00")
    print(f"Number of days analyzed: {statistics['num_days']}")