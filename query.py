import json
import pandas as pd
import os
import glob
from lxml import etree
import mysql.connector
from conditions import resolve_queries


# Load XML file
xml_file = "sample_schema.xml"
tree = etree.parse(xml_file)
root = tree.getroot()

with open('query.json', 'r') as file:
    jsonquery = json.load(file)

# Define the namespace
namespace = {'ns': 'http://iiitb.ac.in/team_5'}

# Extract the name and type attributes
data_dict = {entity.find("ns:name", namespace).text: entity.attrib["type"] for entity in root.findall("ns:entity_type", namespace)}

print(data_dict)

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

# Extract DSNames with type 'SQL'
sql_ds_names = [entry["DSName"] for entry in jsonquery["Select"] if data_dict.get(entry["DSName"]) == "SQL"]
xml_ds_names = [entry["DSName"] for entry in jsonquery["Select"] if data_dict.get(entry["DSName"]) == "XML"]


finaldf = []

# Execute queries for each SQL DSName
for entry in jsonquery["Select"]:
    ds_name = entry["DSName"]
    fields = entry["Fields"]
    if ds_name in sql_ds_names and ds_name in sql_db_configs:
        fields = ", ".join(fields)
        query = f"SELECT {fields} FROM {ds_name}"

        # Connect using respective DB config
        conn = mysql.connector.connect(**sql_db_configs[ds_name])
        df = pd.read_sql(query, conn)

        #change column names to datasource.columnname
        df.columns = [f"{ds_name}.{col}" for col in df.columns]

    elif ds_name in xml_ds_names:
        # Assume XML files are in "Datasources/<DSName>" folder
        folder = os.path.join("Datasources", ds_name)
        xml_files = glob.glob(os.path.join(folder, "*.xml"))
        records = []

        print(xml_files)
        
        for xml_file in xml_files:
            try:
                tree = etree.parse(xml_file)
            except Exception as e:
                print(f"Error parsing {xml_file}: {e}")
                continue
            record = {}
            for field in fields:
                value = tree.xpath(f"string(//{field})")
                record[field] = value  # use last part as column name
            #change column names to datasource.columnname
            record = {f"{ds_name}.{k}": v for k, v in record.items()}
            records.append(record)
        # Create DataFrame from records
        df = pd.DataFrame(records)

    finaldf.append(df)

finalfinal = resolve_queries(jsonquery, finaldf)
final1 = []
to_display = []

# Display only specified columns in 'display' if not empty
for entry in jsonquery["Select"]:
    display_fields = entry.get("display", [])
    # concatenate entry["DSName"] with display_fields
    display_fields = [f"{entry['DSName']}.{field}" for field in display_fields]
    to_display = to_display + display_fields

new_df = finalfinal[to_display]

    

print(finalfinal)

# save in csv
new_df.to_csv("final.csv", index = False)



conn.close()