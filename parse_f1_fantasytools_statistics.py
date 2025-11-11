import json

def parse_external_scores(json_data):
    """
    Parses fantasy score data from an external source and transforms it
    into the desired format, returning the result.

    Args:
        json_data (dict): The raw JSON data (as a Python dictionary) to parse.

    Returns:
        dict: The parsed and transformed fantasy score data.
    """
    try:
        # The input is now expected to be a dictionary
        data = json_data
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON data")
        return {}

    fantasy_scores = {}
    race_results = data.get("seasonResult", {}).get("raceResults", {})

    for race_number, race_data in race_results.items():
        if not race_data.get("drivers") and not race_data.get("constructors"):
            continue

        fantasy_scores[race_number] = {
            "drivers": {},
            "constructors": {}
        }

        for driver in race_data.get("drivers", []):
            driver_abbr = driver.get("abbreviation")
            if driver_abbr:
                fantasy_scores[race_number]["drivers"][driver_abbr] = {
                    "fantasy_cost": driver.get("price"),
                    "fantasy_score": driver.get("totalPoints")
                }

        for constructor in race_data.get("constructors", []):
            constructor_abbr = constructor.get("abbreviation")
            if constructor_abbr:
                fantasy_scores[race_number]["constructors"][constructor_abbr] = {
                    "fantasy_cost": constructor.get("price"),
                    "fantasy_score": constructor.get("totalPoints")
                }

    return fantasy_scores

if __name__ == '__main__':
    # Example of reading from file for standalone script execution
    input_filepath = 'data/sample_fantasy_external_score.json'
    try:
        with open(input_filepath, 'r') as f:
            sample_data = json.load(f)
        parsed_data = parse_external_scores(sample_data)
        if parsed_data:
            print(json.dumps(parsed_data, indent=2))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error in main execution: {e}")