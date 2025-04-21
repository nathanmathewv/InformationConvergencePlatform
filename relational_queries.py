import mysql.connector
import pandas as pd
import os

def configure_sql_db(namespace,root):
    sql_db_configs = {}
    for entity in root.findall("ns:entity_type", namespace):
        if entity.attrib["type"] == "SQL":
            name = entity.find("ns:name", namespace).text
            db = entity.find("ns:ds/ns:dbconfig", namespace)
            config = {
                "host": db.find("ns:host", namespace).text,
                "user": db.find("ns:user", namespace).text,
                "password": db.find("ns:password", namespace).text,
                "database": db.find("ns:database", namespace).text
            }
            sql_db_configs[name] = config
    
    return sql_db_configs

def get_ds_specific_query(jsonquery,data_dict):
    sql_ds_names = [entry["DSName"] for entry in jsonquery["Select"] if data_dict.get(entry["DSName"]) == "SQL"]
    return sql_ds_names

def initialize_sql(root,namespace,jsonquery,data_dict):
    sql_db_configs = configure_sql_db(namespace,root)
    sql_ds_names = get_ds_specific_query(jsonquery,data_dict)
    
    return sql_ds_names, sql_db_configs

def run_sql_query(conditions, sql_db, ds_name, fields):

    # Get where clause fields
    where_conditions_sql = []

    for block in conditions:
        literals_sql = ["true"]
        for literal in block.get("Literals", []):
            v1, v2 = literal["Value1"], literal["Value2"]
            op = literal["Operator"]
            def format_val(val):
                if val.startswith("Constant::"):
                    return f"'{val.split('::')[1]}'"
                elif val.split(".")[0] == ds_name:
                    return val.split(".")[1]
                return None
            val1 = format_val(v1)
            val2 = format_val(v2)
            if val1 and val2:
                literals_sql.append(f"{val1} {op} {val2}")

        if literals_sql:
            where_conditions_sql.append(f"({' AND '.join(literals_sql)})")

    fields_str = ", ".join(set(fields))
    query = f"SELECT {fields_str} FROM {ds_name}"
    if where_conditions_sql:
        query += " WHERE " + " OR ".join(where_conditions_sql)

    print(query)

    # Connect using respective DB config
    conn = mysql.connector.connect(**sql_db)
    df = pd.read_sql(query, conn)

    #change column names to datasource.columnname
    df.columns = [f"{ds_name}.{col}" for col in df.columns]

    conn.close()

    return df

def configure_spreadsheet_ds(root, namespace):
    spreadsheet_files = {}
    for entity in root.findall("ns:entity_type", namespace):
        if entity.attrib["type"] == "Spreadsheet":
            name = entity.find("ns:name", namespace).text
            file = entity.find("ns:ds/ns:file", namespace).text
            sheet = entity.find("ns:ds/ns:sheet", namespace).text
            spreadsheet_files[name] = {"file": file, "sheet": sheet}
    return spreadsheet_files

def get_spreadsheet_ds_names(jsonquery, data_dict):
    return [entry["DSName"] for entry in jsonquery["Select"] if data_dict.get(entry["DSName"]) == "Spreadsheet"]

def run_spreadsheet_query(ds_name, file_info, fields):
    file_path = os.path.join("Datasources", file_info["file"])
    sheet_name = file_info["sheet"]

    df = pd.read_excel(file_path, sheet_name=sheet_name)

    # Filter only requested fields if they exist
    filtered_fields = [f for f in fields if f in df.columns]
    df = df[filtered_fields]

    # Prefix column names with DSName
    df.columns = [f"{ds_name}.{col}" for col in df.columns]
    
    return df