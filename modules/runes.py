# List of all rune types grouped by category
RUNE_TYPES = {
    "Lesser": [
        "Lesser Body Rune",
        "Lesser Desert Rune",
        "Lesser Glacial Rune",
        "Lesser Inspiration Rune",
        "Lesser Iron Rune",
        "Lesser Mind Rune",
        "Lesser Rebirth Rune",
        "Lesser Stone Rune",
        "Lesser Storm Rune",
        "Lesser Vision Rune"
    ],
    "Normal": [
        "Body Rune",
        "Desert Rune",
        "Glacial Rune",
        "Inspiration Rune",
        "Iron Rune",
        "Mind Rune",
        "Rebirth Rune",
        "Stone Rune",
        "Storm Rune",
        "Vision Rune"
    ],
    "Greater": [
        "Greater Body Rune",
        "Greater Desert Rune",
        "Greater Glacial Rune",
        "Greater Inspiration Rune",
        "Greater Iron Rune",
        "Greater Mind Rune",
        "Greater Rebirth Rune",
        "Greater Stone Rune",
        "Greater Storm Rune",
        "Greater Vision Rune"
    ],
    "Special": [
        "Greater Rune of Alacrity",
        "Greater Rune of Leadership",
        "Greater Rune of Nobility",
        "Greater Rune of Tithing"
    ]
}

# Flatten the dictionary to get a list of all rune names
ALL_RUNE_NAMES = [rune for category_runes in RUNE_TYPES.values() for rune in category_runes]

def get_rune_lines(selected_runes):
    """
    Generates filter lines for the selected rune types.

    Args:
        selected_runes (list): A list of rune names selected via checkboxes.

    Returns:
        list: A list of dictionaries, each containing a 'line' for the filter.
              Returns an empty list if no runes are selected.
    """
    lines = []
    if not selected_runes:
        return lines

    for rune_name in selected_runes:
        if rune_name in ALL_RUNE_NAMES:
            # The 'price' key is added for consistency, though not used here.
            lines.append({
                "line": f'[Type] == "{rune_name}" # [StashItem] == "true"',
                "price": 0 # Placeholder price
            })
    return lines
