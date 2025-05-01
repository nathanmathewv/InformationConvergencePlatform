from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
import json
import pandas as pd
from lxml import etree

from conditional_filtering import resolve_queries
from relational_queries import initialize_sql, run_sql_query, configure_spreadsheet_ds, get_spreadsheet_ds_names, run_spreadsheet_query
from markdown_queries import initialize_xml, run_xml_query
from execution_helper import get_display_fields, get_ds_specific_query, get_all_fields

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'Schemas'

@app.route('/<path:filename>')
def download_file(filename):
    return send_from_directory('.', filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_schema', methods=['POST'])
def upload_schema():
    data = request.get_json()
    xml_content = data.get('xml')
    file_name = data.get('file_name')

    if not xml_content or not file_name:
        return jsonify({"error": "Both 'xml' and 'file_name' fields are required."}), 400

    filename = secure_filename(file_name)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(xml_content)

    return jsonify({"message": "Schema uploaded successfully", "path": filepath}), 200

@app.route('/run_query', methods=['POST'])
def run_query():
    data = request.form
    schema_file = data['schema_file']
    query_json = data['query_json']

    try:
        jsonquery = json.loads(query_json)
    except:
        return "Invalid JSON", 400

    # Load and parse XML
    schema_path = os.path.join(app.config['UPLOAD_FOLDER'], schema_file)
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

    merged_df.to_csv("output.csv", index=False)
    merged_df.to_json("output.json", orient="records", indent=4)
    print([merged_df.to_html(classes='data')])

    return render_template("result.html", tables=[merged_df.to_html(classes='data')][-1], titles=merged_df.columns.values)

if __name__ == '__main__':
    app.run(debug=True)
