from flask import Flask, render_template, request
import requests
from datetime import datetime, timezone
import time
from dotenv import load_dotenv
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime, timedelta

# Umgebungsvariablen laden
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

app = Flask(__name__, template_folder='../templates')

# Verbindung zur MongoDB herstellen
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client.get_database("poe_items")  # Datenbankname
collection = db["unique_items"]  # Collection für gescrapte Daten

# Hilfsfunktion: Prüfen, ob Daten älter als 4 Stunden sind
def is_data_older_than_4_hours():
    last_entry = collection.find_one(sort=[("timestamp", -1)])  # Neuestes Dokument
    if last_entry:
        last_timestamp = last_entry.get("timestamp")
        return datetime.now() - last_timestamp > timedelta(hours=4)
    return True  # Falls keine Daten vorhanden sind

# Funktion: Daten von den URLs scrapen
def scrape_poe_categories():
    urls = [
        "https://poe2scout.com/api/items/accessory?per_page=200&league=Standard",
        "https://poe2scout.com/api/items/armour?per_page=200&league=Standard",
        "https://poe2scout.com/api/items/flask?per_page=200&league=Standard",
        "https://poe2scout.com/api/items/jewel?per_page=200&league=Standard",
        "https://poe2scout.com/api/items/sanctum?per_page=200&league=Standard",
        "https://poe2scout.com/api/items/weapon?per_page=200&league=Standard"
    ]
    
    all_items = {}
    
    try:
        # Collection leeren, bevor neue Daten eingefügt werden
        collection.delete_many({})
        for url in urls:
            category = url.split('/items/')[1].split('?')[0].upper()
            response = requests.get(url)
            data = response.json()
            
            items = []
            for item in data['items']:
                if item['unique'] and 'latest_price' in item:
                    name = item['name']
                    item_type = item['type']
                    nominal_price = item['latest_price']['nominal_price']
                    
                    # Nur benötigte Daten speichern
                    item_data = {
                        "name": name,
                        "type": item_type,
                        "price": nominal_price,
                        "category": category,
                        "timestamp": datetime.now(timezone.utc)  # UTC-Zeit
                    }
                    items.append(item_data)
            
            if items:
                all_items[category] = items
                # Daten in MongoDB speichern
                collection.insert_many(items)
        
        return all_items
        
    except Exception as e:
        print(f"Fehler beim Scrapen: {str(e)}")
        return {'ERROR': [{'line': f'Error: {str(e)}', 'price': 0}]}

# Funktion: Daten aus der MongoDB abrufen und für das Frontend parsen
def get_items_from_db(min_exalted_price, use_type=False):
    items = collection.find({"price": {"$gte": min_exalted_price}}, {"_id": 0})
    parsed_items = {}
    
    for item in items:
        category = item["category"]
        name = item["name"]
        item_type = item["type"]
        price = item["price"]
        
        type_prefix = f'[Type] == "{item_type}" && ' if use_type else ''
        line = f'{type_prefix}[Rarity] == "Unique" # [UniqueName] == "{name}" && [StashItem] == "true" // Exalted: {int(price)}'
        
        if category not in parsed_items:
            parsed_items[category] = []
        parsed_items[category].append({"line": line, "price": price})
    
    # Sortiere die Items nach Preis (absteigend)
    for category in parsed_items:
        parsed_items[category] = sorted(parsed_items[category], key=lambda x: x["price"], reverse=True)
    
    return parsed_items

# Funktion: Berechne das Alter der Daten
def get_data_age():
    try:
        last_entry = collection.find_one(sort=[("timestamp", -1)])  # Neuestes Dokument
        if last_entry:
            last_timestamp = last_entry.get("timestamp")
            if last_timestamp.tzinfo is None:
                # Falls die Zeit keine Zeitzone hat, gehe davon aus, dass sie UTC ist
                last_timestamp = last_timestamp.replace(tzinfo=timezone.utc)
            age = datetime.now(timezone.utc) - last_timestamp  # Aktuelle Zeit in UTC
            hours, remainder = divmod(age.seconds, 3600)
            minutes = remainder // 60
            return f"{hours}h {minutes}min"
        return "No data available"
    except Exception as e:
        print(f"Fehler beim Berechnen des Datenalters: {str(e)}")
        return "Unknown"

# Route: Hauptseite
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        min_exalted = float(request.form.get('min_exalted', 1))
        use_type = 'use_type' in request.form  # Checkbox Status
        
        # Prüfen, ob Daten älter als 4 Stunden sind
        if is_data_older_than_4_hours():
            print("Daten sind älter als 4 Stunden. Scrape neue Daten...")
            scrape_poe_categories()
        
        # Daten aus der MongoDB abrufen und parsen
        items = get_items_from_db(min_exalted, use_type)
        data_age = get_data_age()
        return render_template('index.html', 
                             categories=items, 
                             min_exalted=min_exalted,
                             use_type=use_type,
                             data_age=data_age)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
