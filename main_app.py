from flask import Flask, request, render_template, jsonify
import asyncio
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import aiohttp
from datetime import datetime
import nest_asyncio
from matplotlib.patches import Patch

nest_asyncio.apply()

app = Flask(__name__)

async def fetch_page(session, url, params, page, retries=3):
    params['page'] = page
    for attempt in range(retries):
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                print(f"Error fetching page {page}: {response.status}")
                await asyncio.sleep(1)
    return None

async def fetch_all_pages(api_key, username):
    url = 'http://ws.audioscrobbler.com/2.0/'
    params = {
        'method': 'user.getRecentTracks',
        'user': username,
        'api_key': api_key,
        'format': 'json',
        'limit': 200,
    }

    async with aiohttp.ClientSession() as session:
        print("Fetching first page...")
        first_page_data = await fetch_page(session, url, params, 1)
        if not first_page_data or 'recenttracks' not in first_page_data or 'track' not in first_page_data['recenttracks']:
            print("No tracks found or invalid data structure.")
            return []

        total_pages = int(first_page_data['recenttracks']['@attr']['totalPages'])
        print(f"Total pages: {total_pages}")

        tasks = [fetch_page(session, url, params, page) for page in range(1, total_pages + 1)]
        pages_data = await asyncio.gather(*tasks)

    all_tracks = []
    for data in pages_data:
        if data and 'recenttracks' in data and 'track' in data['recenttracks']:
            all_tracks.extend(data['recenttracks']['track'])

    return all_tracks

def process_scrobble_data(tracks):
    print("Processing scrobble data...")
    df = pd.DataFrame(tracks)
    if df.empty:
        print("No tracks to process.")
        return pd.DataFrame()

    df['date'] = pd.to_datetime(df['date'].apply(lambda x: x['#text']), format='%d %b %Y, %H:%M')
    df['Day'] = df['date'].dt.date
    daily_counts = df.groupby('Day').size().reset_index(name='Counts')
    print("Processing complete.")
    return daily_counts

def create_heatmap(daily_counts):
    print("Creating heatmap...")
    daily_counts['Day'] = pd.to_datetime(daily_counts['Day'])
    daily_counts['DayOfMonth'] = daily_counts['Day'].dt.day
    daily_counts['Month'] = daily_counts['Day'].dt.to_period('M')
    pivot_table = daily_counts.pivot_table(values='Counts', index='DayOfMonth', columns='Month', fill_value=0)
    full_index = pd.Index(range(1, 32), name='DayOfMonth')
    pivot_table = pivot_table.reindex(full_index)
    pivot_table_log = pivot_table.map(lambda x: np.log10(x + 1) if x > 0 else np.nan)
    
    for day in range(29, 32):
        for month in pivot_table_log.columns:
            if day > month.days_in_month:
                pivot_table_log.at[day, month] = np.nan

    cmap = sns.color_palette("rocket_r", as_cmap=True)
    cmap.set_bad(color='white')

    plt.figure(figsize=(25, 10))  
    ax = sns.heatmap(pivot_table_log, cmap=cmap, cbar=True, cbar_kws={'label': 'Number of Songs Played', 'shrink': 0.75}, mask=pivot_table_log.isna(), vmin=0, vmax=pivot_table_log.max().max(), square=True)
    plt.title('Heatmap of Songs Listened to Per Day')
    plt.xlabel('Month')
    plt.ylabel('Day of Month')
    plt.xticks(rotation=45)

    cbar = ax.collections[0].colorbar
    max_songs = int(10**pivot_table_log.max().max() - 1)
    cbar.set_ticks([0, pivot_table_log.max().max()])
    cbar.set_ticklabels(['1 song', f'{max_songs} songs'])

    legend_elements = [Patch(facecolor='white', edgecolor='black', label='No songs listened to')]
    plt.gca().add_artist(plt.legend(handles=legend_elements, loc='best', bbox_to_anchor=(1.05, 0.6), frameon=False, ncol=1))

    x_labels = [f"{date.year % 100:02d}-{date.month:02d}" for date in pivot_table_log.columns.to_timestamp()]
    ax.set_xticklabels(x_labels)

    plt.tight_layout()
    plt.show()
    print("Heatmap created successfully.")

@app.route('/', methods=['GET', 'POST'])
async def index():
    if request.method == 'POST':
        api_key = request.form['api_key']
        username = request.form['username']
        tracks = await fetch_all_pages(api_key, username)
        daily_counts = process_scrobble_data(tracks)
        create_heatmap(daily_counts)
        return jsonify({'status': 'success', 'message': 'Heatmap created successfully'})
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)