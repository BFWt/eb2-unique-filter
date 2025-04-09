from flask import Flask, render_template, request
# Import functions from modules
from modules.unique_items import (
    is_data_older_than_4_hours,
    scrape_poe_categories,
    get_items_from_db,
    get_data_age
)
from modules.currency import get_currency_lines, CURRENCY_TYPES
# Import rune components
from modules.runes import RUNE_TYPES, get_rune_lines

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Route: Hauptseite
@app.route('/', methods=['GET', 'POST'])
def index():
    # Initialize variables for template context
    unique_items_data = {}
    currency_lines_data = []
    rune_lines_data = [] # Initialize rune lines
    min_exalted = 1 # Default value
    use_type = False # Default value
    selected_currencies = [] # Default value
    selected_runes = [] # Initialize selected runes
    data_age_str = "Unknown" # Default value

    if request.method == 'POST':
        # --- Unique Items Section ---
        min_exalted = float(request.form.get('min_exalted', 1))
        use_type = 'use_type' in request.form

        # Check unique item data age and scrape if necessary
        try:
            if is_data_older_than_4_hours():
                print("Unique item data is older than 4 hours. Scraping new data...")
                scrape_poe_categories() # This now happens inside the module
            else:
                print("Unique item data is fresh.")
            # Fetch unique items based on form input
            unique_items_data = get_items_from_db(min_exalted, use_type)
            data_age_str = get_data_age()
        except Exception as e:
            print(f"Error handling unique items: {e}")
            # Handle error appropriately, maybe show a message to the user
            data_age_str = "Error fetching data"


        # --- Currency Section ---
        # Get the list of selected currencies from the form
        # Checkboxes that are checked will have their 'name' attribute in request.form
        # We use request.form.getlist to get all checked values for 'currency_types'
        selected_currencies = request.form.getlist('currency_types')
        currency_lines_data = get_currency_lines(selected_currencies)

        # --- Runes Section ---
        selected_runes = request.form.getlist('rune_types')
        rune_lines_data = get_rune_lines(selected_runes)

        # Combine data for rendering (or pass separately)
        # For now, passing separately

        return render_template('index.html',
                             # Unique items related context
                             categories=unique_items_data,
                             min_exalted=min_exalted,
                             use_type=use_type,
                             data_age=data_age_str,
                             # Currency related context
                             all_currency_types=CURRENCY_TYPES, # Pass the full list for rendering checkboxes
                             selected_currencies=selected_currencies, # Pass selected ones to re-check boxes
                             currency_lines=currency_lines_data, # Pass generated lines
                             # Rune related context
                             all_rune_types=RUNE_TYPES, # Pass the structured dict for rendering
                             selected_runes=selected_runes, # Pass selected ones to re-check boxes
                             rune_lines=rune_lines_data) # Pass generated lines

    # --- GET Request ---
    # For a GET request, just render the template with defaults
    # We still need to pass the currency list for the initial render
    try:
        data_age_str = get_data_age() # Get age even on GET request
    except Exception as e:
         print(f"Error getting data age on GET: {e}")
         data_age_str = "Error fetching data age"

    return render_template('index.html',
                         categories=unique_items_data, # Empty dict
                         min_exalted=min_exalted,
                         use_type=use_type,
                         data_age=data_age_str,
                         all_currency_types=CURRENCY_TYPES, # Pass the full list
                         selected_currencies=selected_currencies, # Empty list
                         currency_lines=currency_lines_data, # Empty list
                         # Rune related context (defaults for GET)
                         all_rune_types=RUNE_TYPES, # Pass the structured dict
                         selected_runes=selected_runes, # Empty list
                         rune_lines=rune_lines_data) # Empty list


if __name__ == '__main__':
    # Note: Running with `python -m api.index` is recommended when using modules
    app.run(debug=True)
