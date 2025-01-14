from flask import Flask, render_template, request
import requests
from pymongo import MongoClient
from config import MONGODB_URI, DB_NAME
import time

app = Flask(__name__, template_folder='../templates')

# MongoDB Verbindung
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
collection = db.items

def update_items():
    categories = ['accessory', 'armour', 'flask', 'jewel', 'sanctum', 'weapon']
    for category in categories:
        try:
            url = f"https://poe2scout.com/api/items/{category}?league=Standard"
            response = requests.get(url)
            data = response.json()
            collection.update_one(
                {"category": category},
                {"$set": {
                    "items": data['items'],
                    "timestamp": time.time()
                }},
                upsert=True
            )
        except Exception as e:
            print(f"Error updating {category}: {str(e)}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        min_exalted = float(request.form.get('min_exalted', 1))
        all_items = {}
        
        for doc in collection.find():
            category = doc['category'].upper()
            items = []
            for item in doc['items']:
                if item['unique'] and 'latest_price' in item:
                    name = item['name']
                    item_type = item['type']
                    exalted_price = item['latest_price']['nominal_price']
                    
                    if exalted_price >= min_exalted:
                        items.append({
                            'line': f'[Type] == "{item_type}" && [Rarity] == "Unique" # [StashItem] == "true" // {name} Value: {int(exalted_price)}',
                            'price': exalted_price
                        })
            
            if items:
                all_items[category] = sorted(items, key=lambda x: x['price'], reverse=True)
        
        return render_template('index.html', categories=all_items, min_exalted=min_exalted)
    return render_template('index.html')

# Daten alle 10 Minuten aktualisieren
update_items()
