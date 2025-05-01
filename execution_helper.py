def get_display_fields(jsonquery):
    to_display = []

    for entry in jsonquery["Select"]:
        display_fields = entry.get("Fields", [])
        # concatenate entry["DSName"] with display_fields
        display_fields = [f"{entry['DSName']}.{field}" for field in display_fields]
        to_display += display_fields
    
    return to_display

def get_all_fields(jsonquery):
    all_fields = dict()
    for entry in jsonquery["Select"]:
        ds_name = entry["DSName"]
        fields = entry.get("Fields", [])
        if ds_name not in all_fields:
            all_fields[ds_name] = []
        all_fields[ds_name] += fields
    for entry in jsonquery["Where"]:
        for literal in entry.get("Literals", []):
            v1 = literal["Value1"]
            v2 = literal["Value2"]
            if v1[:10] != "Constant::":
                ds_name = v1[:v1.index(".")]
                v1 = v1.split(".")[-1]
                if ds_name not in all_fields:
                    all_fields[ds_name] = []
                all_fields[ds_name].append(v1)
            if v2[:10] != "Constant::":
                ds_name = v2[:v2.index(".")]
                v2 = v2.split(".")[-1]
                if ds_name not in all_fields:
                    all_fields[ds_name] = []
                all_fields[ds_name].append(v2)
    for key in all_fields.keys():
        all_fields[key] = list(set(all_fields[key]))
    return all_fields

def get_ds_specific_query(jsonquery):
    #go through "Select" and get the DSName of each entry
    ds_names = [entry["DSName"] for entry in jsonquery["Select"]]

    where_conditions = jsonquery.get("Where", [])
    conditions = dict()
    for ds_name in ds_names:
        conditions[ds_name] = []
        for i in where_conditions:
            temp_literals = []
            for literal in i.get("Literals", []):
                v1 = literal["Value1"]
                v2 = literal["Value2"]
                v1_cond = (v1[:10] == "Constant::" or v1[:v1.index(".")] == ds_name)
                v2_cond = (v2[:10] == "Constant::" or v2[:v2.index(".")] == ds_name)
                if(v1_cond and v2_cond):
                    temp_literals.append(literal)
            conditions[ds_name].append({"Literals": temp_literals})
    return conditions
        