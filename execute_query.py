from conditional_filtering import resolve_queries
from relational_queries import initialize_sql, run_sql_query, configure_spreadsheet_ds, get_spreadsheet_ds_names, run_spreadsheet_query
from markdown_queries import initialize_xml, run_xml_query
from execution_helper import get_display_fields, get_ds_specific_query, get_all_fields
import os
import json
from flask import render_template
from lxml import etree

OUTPUT_DIR = "Output"

def run(data, upload_folder):
    schema_file = data['schema_file']
    query_json = data['query_json']

    try:
        jsonquery = json.loads(query_json)
    except:
        return "Invalid JSON", 400

    # Load and parse XML
    schema_path = os.path.join(upload_folder, schema_file)

    tree = etree.parse(schema_path)
    root = tree.getroot()
    namespace = {'ns': 'http://iiitb.ac.in/team_5'}
    data_dict = {entity.find("ns:name", namespace).text: entity.attrib["type"]
                    for entity in root.findall("ns:entity_type", namespace)}

    # Init data sources
    sql_ds_names, sql_db_configs = initialize_sql(root, namespace, jsonquery, data_dict)
    xml_ds_names, xml_files, xml_roots = initialize_xml(root, jsonquery, data_dict, namespace)
    spreadsheet_ds_names = get_spreadsheet_ds_names(jsonquery, data_dict)
    spreadsheet_files = configure_spreadsheet_ds(root, namespace)

    specific_query = get_ds_specific_query(jsonquery)
    specific_fields = get_all_fields(jsonquery)

    merged_df = []

    for ds_name, conditions in specific_query.items():
        if ds_name in sql_ds_names and ds_name in sql_db_configs:
            df = run_sql_query(conditions, sql_db_configs[ds_name], ds_name, specific_fields[ds_name])
        elif ds_name in xml_ds_names:
            df = run_xml_query(conditions, xml_files, ds_name, xml_roots[ds_name], specific_fields[ds_name])
        elif ds_name in spreadsheet_ds_names:
            df = run_spreadsheet_query(ds_name, spreadsheet_files[ds_name], specific_fields[ds_name])
        merged_df.append(df)

    merged_df = resolve_queries(jsonquery, merged_df)
    to_display = get_display_fields(jsonquery)
    merged_df = merged_df[to_display]

    merged_df.to_csv(os.path.join(OUTPUT_DIR,'output.csv'), index=False)
    merged_df.to_json(os.path.join(OUTPUT_DIR,'output.json'), orient="records", indent=4)
    # print([merged_df.to_html(classes='data')])

    return render_template("result.html", tables=[merged_df.to_html(classes='data')][-1], titles=merged_df.columns.values)