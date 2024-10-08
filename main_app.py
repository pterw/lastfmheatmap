import os
from flask import Flask, request, render_template, jsonify
import asyncio
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import aiohttp
from datetime import datetime
import nest_asyncio
from dotenv import load_dotenv
from matplotlib.patches import Patch

load_dotenv()
nest_asyncio.apply()

app = Flask(__name__)

API_KEY = os.getenv('LASTFM_API_KEY')

async def fetch_page(session, url, params, page):
    params['page'] = page
    async with session.get(url, params=params) as response:
        if response.status == 200:
            data = await response.json()
            return data
        else:
            print(f"Error fetching page {page}: {response.status}")
            return None

async def fetch_all_pages(username):
    url = 'http://ws.audioscrobbler.com/2.0/'
    params = {
        'method': 'user.getRecentTracks',
        'user': username,
        'api_key': API_KEY,
        'format': 'json',
        'limit': 200,
    }

    all_tracks = []
    async with aiohttp.ClientSession() as session:
        first_page_data = await fetch_page(session, url, params, 1)
        if not first_page_data or 'recenttracks' not in first_page_data or 'track' not in first_page_data['recenttracks']:
            return []
        
        total_pages = int(first_page_data['recenttracks']['@attr']['totalPages'])
        print(f"Total pages: {total_pages}")

        all_tracks.extend(first_page_data['recenttracks']['track'])
        for page in range(2, total_pages + 1):
            data = await fetch_page(session, url, params, page)
            if data and 'recenttracks' in data and 'track' in data['recenttracks']:
                all_tracks.extend(data['recenttracks']['track'])

            # Avoid fetching too many pages at once
            if page % 10 == 0:
                await asyncio.sleep(1)

    return all_tracks

def process_scrobble_data(tracks):
    df = pd.DataFrame(tracks)
    if df.empty:
        return pd.DataFrame()

    def extract_date(x):
        if isinstance(x, dict):
            return x.get('#text', None)
        return None

    df['date'] = pd.to_datetime(df['date'].apply(extract_date), format='%d %b %Y, %H:%M')
    df['Day'] = df['date'].dt.date
    daily_counts = df.groupby('Day').size().reset_index(name='Counts')
    return daily_counts

def create_heatmap(daily_counts):
    if not os.path.exists('static'):
        os.makedirs('static')
    
    daily_counts['Day'] = pd.to_datetime(daily_counts['Day'])
    daily_counts['DayOfMonth'] = daily_counts['Day'].dt.day
    daily_counts['Month'] = daily_counts['Day'].dt.to_period('M')
    pivot_table = daily_counts.pivot_table(values='Counts', index='DayOfMonth', columns='Month', fill_value=0)
    full_index = pd.Index(range(1, 32), name='DayOfMonth')
    pivot_table = pivot_table.reindex(full_index)

    # Set NaN for non-existent days in each month
    for day in range(29, 32):
        for month in pivot_table.columns:
            if day > month.days_in_month:
                pivot_table.at[day, month] = np.nan
    
    # Apply log transformation without converting zero counts to NaN
    pivot_table_log = pivot_table.applymap(lambda x: np.log10(x + 1) if not np.isnan(x) else np.nan)

    # Set up the colormap
    cmap = sns.color_palette("rocket_r", as_cmap=True)
    cmap.set_bad(color='gray')  # Non-existent days will be gray

    plt.figure(figsize=(25, 10))
    ax = sns.heatmap(
        pivot_table_log,
        cmap=cmap,
        cbar=True,
        cbar_kws={'label': 'Number of Songs Played', 'shrink': 0.75},
        vmin=0,
        vmax=pivot_table_log.max().max(),
        square=True
    )
    plt.title('Heatmap of Songs Listened to Per Day')
    plt.xlabel('Month')
    plt.ylabel('Day of Month')
    plt.xticks(rotation=45)

    # Adjust colorbar ticks
    cbar = ax.collections[0].colorbar
    max_songs = int(10**pivot_table_log.max().max() - 1)
    cbar.set_ticks([0, pivot_table_log.max().max()])
    cbar.set_ticklabels(['1 song', f'{max_songs} songs'])

    # Move the legend outside the plot area
    legend_elements = [Patch(facecolor='white', edgecolor='black', label='No songs listened to')]
    plt.legend(
        handles=legend_elements,
        loc='upper left',
        bbox_to_anchor=(1.05, 1),
        frameon=False
    )

    # Adjust layout to make room for the legend
    plt.tight_layout(rect=[0, 0, 0.85, 1])

    x_labels = [f"{date.year % 100:02d}-{date.month:02d}" for date in pivot_table_log.columns.to_timestamp()]
    ax.set_xticklabels(x_labels)

    filename = 'static/heatmap.png'
    plt.savefig(filename)
    plt.close()
    return filename

@app.route('/', methods=['GET', 'POST'])
async def index():
    filename = None
    if request.method == 'POST':
        username = request.form['username']

        all_tracks = await fetch_all_pages(username)
        daily_counts = process_scrobble_data(all_tracks)
        filename = create_heatmap(daily_counts)
    return render_template('index.html', filename=filename)

if __name__ == '__main__':
    app.run()
