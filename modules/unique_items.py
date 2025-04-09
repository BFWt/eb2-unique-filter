import requests
from datetime import datetime, timezone, timedelta
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

# Load environment variables for MONGO_URI
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Establish MongoDB connection within the module
# Consider passing the client/db/collection if managing connection centrally
try:
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    db = client.get_database("poe_items")
    collection = db["unique_items"]
except Exception as e:
    print(f"Error connecting to MongoDB in unique_items module: {e}")
    # Handle connection error appropriately, maybe raise an exception
    # For now, set collection to None to avoid errors later if connection fails
    collection = None

# --- Functions moved from api/index.py ---

def is_data_older_than_4_hours():
    """Checks if the latest data in the MongoDB collection is older than 4 hours."""
    if collection is None: # Explicit check for None
        print("MongoDB collection not available in is_data_older_than_4_hours.")
        return True # Assume data needs refresh if DB connection failed

    last_entry = collection.find_one(sort=[("timestamp", -1)])
    if last_entry:
        last_timestamp = last_entry.get("timestamp")
        # Ensure timestamp is timezone-aware (assuming UTC if not)
        if last_timestamp.tzinfo is None:
             last_timestamp = last_timestamp.replace(tzinfo=timezone.utc)
        # Ensure current time is timezone-aware UTC
        now_utc = datetime.now(timezone.utc)
        return now_utc - last_timestamp > timedelta(hours=4)
    return True # No data found, needs refresh

def scrape_poe_categories():
    """Scrapes unique item data from poe2scout API and stores it in MongoDB."""
    if collection is None: # Explicit check for None
        print("MongoDB collection not available in scrape_poe_categories.")
        return {'ERROR': [{'line': 'Error: MongoDB connection failed', 'price': 0}]}

    urls = [
        "https://poe2scout.com/api/items/unique/accessory?perPage=500&league=Dawn%20of%20the%20Hunt",
        "https://poe2scout.com/api/items/unique/armour?perPage=500&league=Dawn%20of%20the%20Hunt",
        "https://poe2scout.com/api/items/unique/flask?perPage=500&league=Dawn%20of%20the%20Hunt",
        "https://poe2scout.com/api/items/unique/jewel?perPage=500&league=Dawn%20of%20the%20Hunt",
        "https://poe2scout.com/api/items/unique/sanctum?perPage=500&league=Dawn%20of%20the%20Hunt",
        "https://poe2scout.com/api/items/unique/weapon?perPage=500&league=Dawn%20of%20the%20Hunt"
    ]
    all_items_scraped = {} # Renamed to avoid conflict

    try:
        collection.delete_many({}) # Clear old data
        print("Scraping new unique item data...")
        for url in urls:
            category = url.split('/unique/')[1].split('?')[0].upper() # Adjusted split logic slightly
            print(f"Scraping category: {category}")
            try:
                response = requests.get(url, timeout=30) # Added timeout
                response.raise_for_status() # Check for HTTP errors
                data = response.json()
            except requests.exceptions.RequestException as req_e:
                print(f"Error fetching URL {url}: {req_e}")
                continue # Skip this URL on error

            items_to_insert = []
            if 'items' in data and isinstance(data['items'], list):
                for item in data['items']:
                    # Check for currentPrice existence and ensure it's not None
                    if isinstance(item, dict) and 'currentPrice' in item and item['currentPrice'] is not None and 'name' in item and 'type' in item:
                        item_data = {
                            "name": item['name'],
                            "type": item['type'],
                            "price": item['currentPrice'],
                            "category": category,
                            "timestamp": datetime.now(timezone.utc)
                        }
                        items_to_insert.append(item_data)
                    # else: # Optional: Log items missing required fields
                    #     print(f"Skipping item due to missing fields or null price: {item.get('name', 'N/A')}")


            if items_to_insert:
                all_items_scraped[category] = items_to_insert # Store locally before DB insert
                collection.insert_many(items_to_insert)
                print(f"Inserted {len(items_to_insert)} items for category {category}")
            else:
                 print(f"No valid items found or inserted for category {category}")


        print("Scraping finished.")
        # Return the structure expected by the original code, though it's not directly used now
        return {cat: [{'name': i['name'], 'type': i['type'], 'price': i['price']} for i in items] for cat, items in all_items_scraped.items()}

    except Exception as e:
        print(f"Error during scraping process: {str(e)}")
        # Return error structure consistent with original code
        return {'ERROR': [{'line': f'Error: {str(e)}', 'price': 0}]}


def get_items_from_db(min_exalted_price, use_type=False):
    """Retrieves unique items from MongoDB based on minimum price and formats them."""
    if collection is None: # Explicit check for None
        print("MongoDB collection not available in get_items_from_db.")
        return {}

    try:
        items_cursor = collection.find({"price": {"$gte": min_exalted_price}}, {"_id": 0})
        parsed_items = {}

        for item in items_cursor:
            category = item.get("category", "UNKNOWN") # Use .get for safety
            name = item.get("name", "Unknown Name")
            item_type = item.get("type", "Unknown Type")
            price = item.get("price", 0)

            type_prefix = f'[Type] == "{item_type}" && ' if use_type else ''
            # Ensure price is integer for the comment
            line = f'{type_prefix}[Rarity] == "Unique" # [UniqueName] == "{name}" && [StashItem] == "true" // Exalted: {int(price)}'

            if category not in parsed_items:
                parsed_items[category] = []
            parsed_items[category].append({"line": line, "price": price})

        # Sort items within each category by price (descending)
        for category in parsed_items:
            parsed_items[category] = sorted(parsed_items[category], key=lambda x: x.get("price", 0), reverse=True)

        return parsed_items
    except Exception as e:
        print(f"Error fetching items from DB: {e}")
        return {}


def get_data_age():
    """Calculates the age of the latest data entry in the MongoDB collection."""
    if collection is None: # Explicit check for None
        print("MongoDB collection not available in get_data_age.")
        return "Unknown (DB Error)"

    try:
        last_entry = collection.find_one(sort=[("timestamp", -1)])
        if last_entry:
            last_timestamp = last_entry.get("timestamp")
            if last_timestamp:
                 # Ensure timestamp is timezone-aware (assuming UTC if not)
                if last_timestamp.tzinfo is None:
                    last_timestamp = last_timestamp.replace(tzinfo=timezone.utc)
                # Ensure current time is timezone-aware UTC
                now_utc = datetime.now(timezone.utc)
                age = now_utc - last_timestamp
                hours, remainder = divmod(age.total_seconds(), 3600)
                minutes = (remainder % 3600) // 60
                return f"{int(hours)}h {int(minutes)}min"
        return "No data available"
    except Exception as e:
        print(f"Error calculating data age: {str(e)}")
        return "Unknown (Error)"
