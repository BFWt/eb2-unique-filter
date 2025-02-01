from flask import Flask, render_template, request
import requests
import time

app = Flask(__name__, 
    template_folder='../templates')

def scrape_poe_categories(min_exalted_price, use_type=False):
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
        for url in urls:
            category = url.split('/items/')[1].split('?')[0].upper()
            response = requests.get(url)
            data = response.json()
            
            items = []
            for item in data['items']:
                if item['unique'] and 'latest_price' in item:
                    name = item['name']
                    item_type = item['type']
                    nominal_price = item['latest_price']['nominal_price']  # Korrekte Variable
                    
                    if nominal_price >= min_exalted_price:
                        type_prefix = f'[Type] == "{item_type}" ' if use_type else ''
                        items.append({
                            'line': f'{type_prefix}[Rarity] == "Unique" # [UniqueName] == "{name}" && [StashItem] == "true" // Exalted: {int(nominal_price)}',
                            'price': nominal_price
                        })
            
            if items:
                all_items[category] = sorted(items, key=lambda x: x['price'], reverse=True)
        
        return all_items
        
    except Exception as e:
        return {'ERROR': [{'line': f'Error: {str(e)}', 'price': 0}]}


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        min_exalted = float(request.form.get('min_exalted', 1))
        use_type = 'use_type' in request.form  # Checkbox Status
        items = scrape_poe_categories(min_exalted, use_type)
        return render_template('index.html', 
                             categories=items, 
                             min_exalted=min_exalted,
                             use_type=use_type)
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
