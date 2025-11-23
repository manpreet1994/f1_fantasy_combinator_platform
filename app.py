import os
from flask import Flask, jsonify, request, abort, render_template
import json
from flask import Response
from flask_cors import CORS
from parse_f1_fantasytools_statistics import parse_external_scores


app = Flask(__name__, template_folder='templates')

# CORS Configuration
origins = [
    "http://localhost:5173",
    "https://manpreet1994.github.io",
]
CORS(app, resources={r"/*": {"origins": origins}})

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
TEAM_MAPPING_FILE_TEMPLATE = os.path.join(DATA_DIR, 'team_mapping_{}.json')
DRIVER_MAPPING_FILE_TEMPLATE = os.path.join(DATA_DIR, 'driver_mapping_{}.json')


def load_team_mapping(year):
    file_path = TEAM_MAPPING_FILE_TEMPLATE.format(year)
    if not os.path.exists(file_path):
        return []  # Return a list for consistency
    with open(file_path, 'r') as f:
        data = json.load(f)
        # Handle legacy list of strings format
        if data and isinstance(data[0], str):
            return [{"name": team, "id": team.upper()[:3]} for team in data]
        return data

def save_team_mapping(year, team_mapping):
    file_path = TEAM_MAPPING_FILE_TEMPLATE.format(year)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    # Ensure teams is a list of objects
    # This is a safeguard, validation should happen in the view
    with open(file_path, 'w') as f:
        json.dump(team_mapping, f, indent=2)

def load_driver_mapping(year):
    file_path = DRIVER_MAPPING_FILE_TEMPLATE.format(year)
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r') as f:
        data = json.load(f)
        # Handle legacy format: {"Driver Name": {"id": "ID", "team": "Team Name"}}
        if data and all(isinstance(k, str) and isinstance(v, dict) and 'id' in v for k, v in data.items()):
            # Check if it's not already in the new format
            first_value = next(iter(data.values()), {})
            if 'name' not in first_value:
                teams_data = load_team_mapping(year)
                team_name_to_id = {team['name']: team['id'] for team in teams_data}
                new_mapping = {}
                for name, details in data.items():
                    team_name = details.get('team', '')
                    new_mapping[details['id']] = {'name': name, 'team_id': team_name_to_id.get(team_name, '')}
                return new_mapping
        return data

def save_driver_mapping(year, mapping):
    file_path = DRIVER_MAPPING_FILE_TEMPLATE.format(year)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(mapping, f, indent=2)

@app.route('/team_mapping/<int:year>', methods=['GET', 'POST'])
def team_mapping(year):
    if request.method == 'GET':
        return jsonify(load_team_mapping(year))
    elif request.method == 'POST':
        if not request.is_json:
            abort(400, description="Request must be JSON")
        team_mapping_data = request.get_json()
        if not isinstance(team_mapping_data, list):
            abort(400, description="Teams must be a JSON list of objects")
        if any(not isinstance(t, dict) or 'name' not in t or 'id' not in t for t in team_mapping_data):
            abort(400, description="Each team must be an object with 'name' and 'id' keys")
        # No default year, year must be provided in URL
        save_team_mapping(year, team_mapping_data)
        return Response(status=204)

@app.route('/login', methods=['POST'])
def handle_login():
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
        if any(not isinstance(v, dict) or 'name' not in v or 'team_id' not in v for v in new_mapping.values()):
            abort(400, description="Each driver must be an object with 'name' and 'team_id' keys")
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

@app.route('/schedule/<int:year>', methods=['GET', 'POST']) #NOSONAR
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

@app.route('/fantasy_scores/<int:year>', methods=['GET', 'POST', 'DELETE'])
def fantasy_scores(year):
    if request.method == 'GET':
        data = load_json('fantasy_scores', year)
        return jsonify(data)
    elif request.method == 'POST':
        if not request.is_json:
            abort(400, description="Request must be JSON")

        # The frontend sends the complete state, so we can just overwrite the old data.
        new_data = request.get_json()
        save_json('fantasy_scores', year, new_data)
        return Response(status=204)
    elif request.method == 'DELETE':
        file_path = get_json_path('fantasy_scores', year)
        if os.path.exists(file_path):
            os.remove(file_path)
            return Response(status=204)
        else:
            # It's not an error if the file is already gone
            return Response(status=204)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tools/parse_scores', methods=['POST'])
def parse_scores_endpoint():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    input_data = request.get_json()

    try:
        # The parsing function expects a dictionary
        parsed_data = parse_external_scores(input_data)
        if not parsed_data:
            return jsonify({"error": "Parsing resulted in empty data. Check input structure."}), 400
        return jsonify(parsed_data)
    except Exception as e:
        # Catching a broad exception to handle any errors during parsing
        return jsonify({"error": f"An error occurred during parsing: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
