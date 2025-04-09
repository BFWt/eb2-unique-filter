# List of all currency types
CURRENCY_TYPES = [
    "Arcanist's Etcher",
    "Artificer's Orb",
    "Artificer's Shard",
    "Armourer's Scrap",
    "Blacksmith's Whetstone",
    "Chaos Orb",
    "Chance Shard",
    "Divine Orb",
    "Exalted Orb",
    "Gemcutter's Prism",
    "Gold",
    "Greater Jeweller's Orb",
    "Lesser Jeweller's Orb",
    "Mirror of Kalandra",
    "Orb of Alchemy",
    "Orb of Augmentation",
    "Orb of Annulment",
    "Orb of Chance",
    "Orb of Transmutation",
    "Perfect Jeweller's Orb",
    "Regal Orb",
    "Regal Shard",
    "Scroll of Wisdom",
    "Transmutation Shard",
    "Vaal Orb"
]

def get_currency_lines(selected_currencies):
    """
    Generates filter lines for the selected currency types.

    Args:
        selected_currencies (list): A list of currency names selected via checkboxes.

    Returns:
        list: A list of dictionaries, each containing a 'line' for the filter.
              Returns an empty list if no currencies are selected.
    """
    lines = []
    if not selected_currencies:
        return lines

    for currency_name in selected_currencies:
        if currency_name in CURRENCY_TYPES:
            # The 'price' key is added for consistency with unique items, though not used here.
            lines.append({
                "line": f'[Type] == "{currency_name}" # [StashItem] == "true"',
                "price": 0 # Placeholder price
            })
    return lines
