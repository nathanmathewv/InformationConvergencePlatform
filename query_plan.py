import xml.etree.ElementTree as ET
import json
import mysql.connector
import pandas as pd

# Load XML file
xml_file = "sample_schema.xml"
tree = ET.parse(xml_file)
root = tree.getroot()

# Define the namespace
namespace = {'ns': 'http://iiitb.ac.in/team_5'}

# Extract the name and type attributes
data_dict = {entity.find("ns:name", namespace).text: entity.attrib["type"] for entity in root.findall("ns:entity_type", namespace)}

# Load JSON file
json_file = "query.json"
with open(json_file, "r") as f:
    json_data = json.load(f)

# Extract DSNames with type 'SQL'
sql_ds_names = [entry["DSName"] for entry in json_data["Select"] if data_dict.get(entry["DSName"]) == "SQL"]

# Database connection details
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Test@123",
    "database": "companydb"
}

# Establish connection
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Execute queries for each SQL DSName
for entry in json_data["Select"]:
    if entry["DSName"] in sql_ds_names:
        fields = ", ".join(entry["Fields"])
        query = f"SELECT {fields} FROM {entry['DSName']}"
        df = pd.read_sql(query, conn)
        print(df)

# Close connection
conn.close()
