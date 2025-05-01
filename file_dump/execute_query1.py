import json
from lxml import etree
from prettytable import PrettyTable
from conditional_filtering import resolve_queries
from relational_queries import initialize_sql, run_sql_query, configure_spreadsheet_ds, get_spreadsheet_ds_names, run_spreadsheet_query
from markdown_queries import initialize_xml, run_xml_query
from execution_helper import get_display_fields, get_ds_specific_query, get_all_fields
import os
# Load XML file
schema_xml_file = "Schemas/sample_schema_ayush.xml"
tree = etree.parse(schema_xml_file)
root = tree.getroot()

with open('Queries/query3.json', 'r') as file:
    jsonquery = json.load(file)

# Define the namespace
namespace = {'ns': 'http://iiitb.ac.in/team_5'}

# Extract the name and type attributes
data_dict = {entity.find("ns:name", namespace).text: entity.attrib["type"] for entity in root.findall("ns:entity_type", namespace)}
# print(data_dict)

# Initialize SQL DB configurations
sql_ds_names, sql_db_configs = initialize_sql(root, namespace,jsonquery,data_dict)
xml_ds_names, xml_files, xml_roots = initialize_xml(root, jsonquery, data_dict, namespace)

spreadsheet_ds_names = get_spreadsheet_ds_names(jsonquery, data_dict)
spreadsheet_files = configure_spreadsheet_ds(root, namespace)

specific_query = get_ds_specific_query(jsonquery)
specific_fields = get_all_fields(jsonquery)
# print(specific_fields)

# print(specific_query,specific_fields)

merged_df = []

# Execute queries for each DSName
for entry in specific_query.items():
    ds_name = entry[0]
    conditions = entry[1]
    # print(ds_name, conditions)
    if ds_name in sql_ds_names and ds_name in sql_db_configs:
        df = run_sql_query(conditions, sql_db_configs[ds_name], ds_name, specific_fields[ds_name])
    elif ds_name in xml_ds_names:
        ds_query = specific_query[ds_name]
        df = run_xml_query(conditions, xml_files, ds_name, xml_roots[ds_name], specific_fields[ds_name])
    elif ds_name in spreadsheet_ds_names:
        df = run_spreadsheet_query(ds_name, spreadsheet_files[ds_name], specific_fields[ds_name])

    # print(df)
    #write df to csv
    # df.to_csv(f"{ds_name}.csv", index=False)
    
    merged_df.append(df)

merged_df = resolve_queries(jsonquery, merged_df)
to_display = get_display_fields(jsonquery)

merged_df = merged_df[to_display]
# print(merged_df)

json_output = merged_df.to_json(orient="records", indent=4)

# Save it to a file
with open("output.json", "w") as f:
    f.write(json_output)

table = PrettyTable()
table.field_names = merged_df.columns.tolist()

for row in merged_df.itertuples(index=False):
    table.add_row(row)

print(table)

# save in txt file
with open("output.txt", "w") as f:
    f.write(str(table))
# save in csv
merged_df.to_csv("output.csv", index = False)