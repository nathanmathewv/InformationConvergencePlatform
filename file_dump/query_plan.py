import xml.etree.ElementTree as ET
import json
import mysql.connector
import pandas as pd

# Load XML file
xml_file = "sample_schema_.xml"
tree = ET.parse(xml_file)
root = tree.getroot()

# Define the namespace
namespace = {'ns': 'http://iiitb.ac.in/team_5'}

# Extract the name and type attributes
data_dict = {entity.find("ns:name", namespace).text: entity.attrib["type"] for entity in root.findall("ns:entity_type", namespace)}

# Extract DB configs for all SQL entity_types
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

# Load JSON file
json_file = "query.json"
with open(json_file, "r") as f:
    json_data = json.load(f)

# Extract DSNames with type 'SQL'
sql_ds_names = [entry["DSName"] for entry in json_data["Select"] if data_dict.get(entry["DSName"]) == "SQL"]

# Execute queries for each SQL DSName
for entry in json_data["Select"]:
    ds_name = entry["DSName"]
    if ds_name in sql_ds_names and ds_name in sql_db_configs:
        fields = ", ".join(entry["Fields"])
        query = f"SELECT {fields} FROM {ds_name}"

        # Connect using respective DB config
        conn = mysql.connector.connect(**sql_db_configs[ds_name])
        df = pd.read_sql(query, conn)

        # Display only specified columns in 'display' if not empty
        display_fields = entry.get("display", [])
        if display_fields:
            df = df[display_fields]

        print(f"\nResults from {ds_name}:")
        print(df)
        conn.close()