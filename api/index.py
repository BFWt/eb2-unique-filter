from flask import Flask, render_template, request
import requests
import time
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='../templates')

CACHE_DIR = 'cache'
CACHE_DURATION = timedelta(hours=1)

def get_cache_path(category):
    return os.path.join(CACHE_DIR, f'{category}.json')

def load_cached_data(category):
    cache_path = get_cache_path(category)
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            cached = json.load(f)
            if datetime.fromisoformat(cached['timestamp']) + CACHE_DURATION > datetime.now():
                return cached['data']
    return None

def save_cache(category, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = get_cache_path(category)
    with open(cache_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'data': data
        }, f)

def fetch_category_data(category, min_exalted_price):
    cached_data = load_cached_data(category)
    if cached_data:
        return cached_data
    
    url = f"https://poe2scout.com/api/items/{category}?per_page=200&league=Standard"
    response = requests.get(url)
    data = response.json()
    save_cache(category, data)
    return data

def scrape_poe_categories(min_exalted_price):
    categories = ['accessory', 'armour', 'flask', 'jewel', 'sanctum', 'weapon']
    all_items = {}
    
    try:
        for category in categories:
            data = fetch_category_data(category, min_exalted_price)
            items = []
            
            for item in data['items']:
                if item['unique'] and 'latest_price' in item:
                    name = item['name']
                    item_type = item['type']
                    exalted_price = item['latest_price']['nominal_price']
                    
                    if exalted_price >= min_exalted_price:
                        items.append({
                            'line': f'[Type] == "{item_type}" && [Rarity] == "Unique" # [StashItem] == "true" // {name} Value: {int(exalted_price)}',
                            'price': exalted_price
                        })
            
            if items:
                category_name = category.upper()
                all_items[category_name] = sorted(items, key=lambda x: x['price'], reverse=True)
        
        return all_items
        
    except Exception as e:
        return {'ERROR': [{'line': f'Error: {str(e)}', 'price': 0}]}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        min_exalted = float(request.form.get('min_exalted', 1))
        items = scrape_poe_categories(min_exalted)
        return render_template('index.html', categories=items, min_exalted=min_exalted)
    return render_template('index.html')

if __name__ == '__main__':
    app.run()
