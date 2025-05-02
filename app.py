from flask import Flask, render_template, request, jsonify, send_from_directory
from execute_query import run
from app_helper import upload

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'Schemas'
app.config['OUTPUT_FOLDER'] = 'Output'

@app.route('/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_schema', methods=['POST'])
def upload_schema():
    data = request.get_json()
    result = upload(data, app.config['UPLOAD_FOLDER'])

    if isinstance(result, tuple):
        if result[1] == 400:
            return result[0], 400
        else:
            return result[0], 200

@app.route('/run_query', methods=['POST'])
def run_query():
    data = request.form
    result = run(data, app.config['UPLOAD_FOLDER'])

    if isinstance(result, tuple):
        if result[0] == "Invalid JSON":
            return jsonify({"error": result[0]}), 400
    else:
        return result


if __name__ == '__main__':
    app.run(debug=True)
