import os
from flask import jsonify
from werkzeug.utils import secure_filename


def upload(data, upload_folder):
    xml_content = data.get('xml')
    file_name = data.get('file_name')

    if not xml_content or not file_name:
        return jsonify({"error": "Both 'xml' and 'file_name' fields are required."}), 400

    filename = secure_filename(file_name)
    filepath = os.path.join(upload_folder, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(xml_content)

    return jsonify({"message": "Schema uploaded successfully", "path": filepath}), 200