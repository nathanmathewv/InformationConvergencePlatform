import json
import pandas as pd
import os
import glob
from lxml import etree
import mysql.connector
from conditions import resolve_queries
from prettytable import PrettyTable
from conditions import get_ds_specific_query

# Load XML file
xml_file = "sample_schema2.xml"
tree = etree.parse(xml_file)
root = tree.getroot()

with open('query2.json', 'r') as file:
    jsonquery = json.load(file)

# Define the namespace
namespace = {'ns': 'http://iiitb.ac.in/team_5'}

# Extract the name and type attributes
data_dict = {entity.find("ns:name", namespace).text: entity.attrib["type"] for entity in root.findall("ns:entity_type", namespace)}

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

specific_query = get_ds_specific_query(jsonquery)

finaldf = []

# Execute queries for each SQL DSName
for entry in jsonquery["Select"]:
    ds_name = entry["DSName"]
    fields = entry["Fields"]
    if ds_name in sql_ds_names and ds_name in sql_db_configs:
        # Get where clause fields
        conditions = specific_query.get(ds_name, [])
        where_conditions_sql = []

        for block in conditions:
            literals_sql = []
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

                # Add fields used in filtering to SELECT
                for val in [v1, v2]:
                    if not val.startswith("Constant::") and val.startswith(ds_name + "."):
                        col = val.split(".", 1)[1]
                        if col not in fields:
                            fields.append(col)
            if literals_sql:
                where_conditions_sql.append(f"({' AND '.join(literals_sql)})")

        fields_str = ", ".join(set(fields))
        query = f"SELECT {fields_str} FROM {ds_name}"
        if where_conditions_sql:
            query += " WHERE " + " OR ".join(where_conditions_sql)

        print(query)

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

table = PrettyTable()
table.field_names = new_df.columns.tolist()

for row in new_df.itertuples(index=False):
    table.add_row(row)

print(table)

# save in txt file
with open("output.txt", "w") as f:
    f.write(str(table))

# save in csv
new_df.to_csv("final.csv", index = False)



conn.close() 