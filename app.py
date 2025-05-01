from flask import Flask, request, jsonify
import os
import json
import pandas as pd
from lxml import etree
from prettytable import PrettyTable
from werkzeug.utils import secure_filename

from conditional_filtering import resolve_queries
from relational_queries import initialize_sql, run_sql_query, configure_spreadsheet_ds, get_spreadsheet_ds_names, run_spreadsheet_query
from markdown_queries import initialize_xml, run_xml_query
from execution_helper import get_display_fields, get_ds_specific_query, get_all_fields

app = Flask(__name__)

UPLOAD_FOLDER = 'Schemas'
ALLOWED_EXTENSIONS = {'xml'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/run_query', methods=['POST'])
def run_query():
    try:
        jsonquery = request.json.get("query")
        schema_path = request.json.get("schema_path")

        if not os.path.exists(schema_path):
            return jsonify({"error": "Schema file not found."}), 400

        tree = etree.parse(schema_path)
        root = tree.getroot()
        namespace = {'ns': 'http://iiitb.ac.in/team_5'}

        data_dict = {entity.find("ns:name", namespace).text: entity.attrib["type"]
                     for entity in root.findall("ns:entity_type", namespace)}

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
            else:
                continue
            merged_df.append(df)

        merged_df = resolve_queries(jsonquery, merged_df)
        to_display = get_display_fields(jsonquery)
        merged_df = merged_df[to_display]

        json_output = merged_df.to_json(orient="records", indent=4)

        return json_output, 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload_schema', methods=['POST'])
def upload_schema():
    try:
        data = request.get_json()

        xml_content = data.get('xml')
        file_name = data.get('file_name')

        if not xml_content or not file_name:
            return jsonify({"error": "Both 'xml' and 'file_name' fields are required."}), 400

        if not file_name.endswith('.xml'):
            return jsonify({"error": "file_name must end with .xml"}), 400

        filename = secure_filename(file_name)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Write the XML content to the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml_content)

        return jsonify({"message": "Schema uploaded successfully", "path": filepath}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
