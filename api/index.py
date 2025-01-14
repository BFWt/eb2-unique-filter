from flask import Flask, render_template, request
import requests
import json
from datetime import datetime, timedelta
import time
import os

app = Flask(__name__, template_folder='../templates')

CACHE_FILE = 'cache/items.json'
CATEGORIES = [
    "accessory",
    "armour",
    "flask",
    "jewel",
    "sanctum",
    "weapon"
]

def load_cached_data():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
            if datetime.now() - datetime.fromisoformat(cache['timestamp']) < timedelta(hours=1):
                return cache['data']
    return None

def save_cache(data):
    os.makedirs('cache', exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'data': data
        }, f)

def fetch_category(category):
    url = f"https://poe2scout.com/api/items/{category}?league=Standard"
    response = requests.get(url)
    time.sleep(2)  # Pause zwischen Anfragen
    return category, response.json()

def update_cache():
    all_items = {}
    for category in CATEGORIES:
        category_upper = category.upper()
        category_data = fetch_category(category)
        if category_data:
            all_items[category_upper] = category_data[1]
    save_cache(all_items)
    return all_items

def get_items(min_exalted_price):
    data = load_cached_data()
    if not data:
        data = update_cache()
    
    filtered_items = {}
    for category, items in data.items():
        category_items = []
        for item in items['items']:
            if item['unique'] and 'latest_price' in item:
                exalted_price = item['latest_price']['nominal_price']
                if exalted_price >= min_exalted_price:
                    category_items.append({
                        'line': f'[Type] == "{item["type"]}" && [Rarity] == "Unique" # [StashItem] == "true" // {item["name"]} Value: {int(exalted_price)}',
                        'price': exalted_price
                    })
        if category_items:
            filtered_items[category] = sorted(category_items, key=lambda x: x['price'], reverse=True)
    
    return filtered_items

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        min_exalted = float(request.form.get('min_exalted', 10))
        items = get_items(min_exalted)
        return render_template('index.html', categories=items, min_exalted=min_exalted)
    return render_template('index.html')

if __name__ == '__main__':
    app.run()
