import os
import asyncio
import pandas as pd
import numpy as np
from flask import Flask, request, render_template, jsonify
import redis
from rq import Queue
from worker import fetch_and_process_data
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Redis connection
redis_url = os.getenv('REDISCLOUD_URL')
conn = redis.from_url(redis_url)
q = Queue(connection=conn)

@app.route('/', methods=['GET', 'POST'])
async def index():
    if request.method == 'POST':
        username = request.form['username']
        color_palette = request.form.get('color_palette', 'rocket_r')

        # Enqueue the data fetching and heatmap generation task
        job = q.enqueue(fetch_and_process_data, username, color_palette)
        
        # Inform the user that the task is in progress
        return jsonify({"message": f"Processing {username}'s data. Job ID: {job.get_id()}"}), 202

    return render_template('index.html')

if __name__ == '__main__':
    app.run()
