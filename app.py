import os
from flask import Flask, jsonify, request, abort, render_template
import os
import json
from flask import Response

app = Flask(__name__, template_folder='templates')
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
TEAMS_FILE_TEMPLATE = os.path.join(DATA_DIR, 'teams_{}.json')


def load_teams(year):
    file_path = TEAMS_FILE_TEMPLATE.format(year)
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r') as f:
        return json.load(f)

def save_teams(year, teams):
    file_path = TEAMS_FILE_TEMPLATE.format(year)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(teams, f, indent=2)

@app.route('/teams/<int:year>', methods=['GET', 'POST'])
def teams(year):
    if request.method == 'GET':
        return jsonify(load_teams(year))
    elif request.method == 'POST':
        if not request.is_json:
            abort(400, description="Request must be JSON")
        teams_data = request.get_json()
        if not isinstance(teams_data, list):
            abort(400, description="Teams must be a JSON array")
        # No default year, year must be provided in URL
        save_teams(year, teams_data)
        return Response(status=204)
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if not os.path.exists(config_path):
        return jsonify({'success': False, 'error': 'No config file found'}), 401
    with open(config_path, 'r') as f:
        config = json.load(f)
    conf_user = config.get('admin_user', 'admin')
    conf_pass = config.get('admin_pass', None)
    if conf_pass is None:
        return jsonify({'success': False, 'error': 'No password set in config'}), 401
    if username == conf_user and password == conf_pass:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False}), 401
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DRIVER_MAPPING_FILE_TEMPLATE = os.path.join(DATA_DIR, 'driver_mapping_{}.json')
def load_driver_mapping(year):
    file_path = DRIVER_MAPPING_FILE_TEMPLATE.format(year)
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r') as f:
        return json.load(f)

def save_driver_mapping(year, mapping):
    file_path = DRIVER_MAPPING_FILE_TEMPLATE.format(year)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(mapping, f, indent=2)
@app.route('/driver_mapping/<int:year>', methods=['GET', 'POST'])
def driver_mapping(year):
    if request.method == 'GET':
        return jsonify(load_driver_mapping(year))
    elif request.method == 'POST':
        if not request.is_json:
            abort(400, description="Request must be JSON")
        new_mapping = request.get_json()
        if not isinstance(new_mapping, dict):
            abort(400, description="Mapping must be a JSON object")
        save_driver_mapping(year, new_mapping)
        return Response(status=204)

# Helper to load JSON file for a given type and year
def get_json_path(data_type, year):
    return os.path.join(DATA_DIR, f"{data_type}_{year}.json")

def load_json(data_type, year):
    file_path = get_json_path(data_type, year)
    if not os.path.exists(file_path):
        return {}  # Return empty if file doesn't exist
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json(data_type, year, data):
    file_path = get_json_path(data_type, year)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/schedule/<int:year>', methods=['GET', 'POST'])
def schedule(year):
    if request.method == 'GET':
        data = load_json('schedule', year)
        return jsonify(data)
    elif request.method == 'POST':
        if not request.is_json:
            abort(400, description="Request must be JSON")
        new_data = request.get_json()
        save_json('schedule', year, new_data)
        return Response(status=204)

@app.route('/fantasy_scores/<int:year>', methods=['GET', 'POST'])
def fantasy_scores(year):
    if request.method == 'GET':
        data = load_json('fantasy_scores', year)
        return jsonify(data)
    elif request.method == 'POST':
        if not request.is_json:
            abort(400, description="Request must be JSON")
        
        current_data = load_json('fantasy_scores', year)
        partial_data = request.get_json()
        current_data.update(partial_data)
        save_json('fantasy_scores', year, current_data)
        return Response(status=204)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
