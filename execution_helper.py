def get_display_fields(jsonquery):
    to_display = []

    for entry in jsonquery["Select"]:
        display_fields = entry.get("display", [])
        # concatenate entry["DSName"] with display_fields
        display_fields = [f"{entry['DSName']}.{field}" for field in display_fields]
        to_display += display_fields
    
    return to_display