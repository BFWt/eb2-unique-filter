from flask import Flask, render_template, request
import requests
import time
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='../templates')

# Global cache dictionary
CACHE = {}
CACHE_DURATION = timedelta(hours=1)

def load_cached_data(category):
    if category in CACHE:
        cached_data, timestamp = CACHE[category]
        if timestamp + CACHE_DURATION > datetime.now():
            return cached_data
    return None

def save_cache(category, data):
    CACHE[category] = (data, datetime.now())

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
    categories = ['accessory', 'armour']
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
