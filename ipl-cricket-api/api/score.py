from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/score')
def score():
    match_id = request.args.get('id')
    if not match_id:
        return jsonify({"error": "Missing id parameter"}), 400

    try:
        # Cricbuzz internal JSON API
        url = f"https://www.cricbuzz.com/api/cricket-scorecard/{match_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": f"https://www.cricbuzz.com/live-cricket-scores/{match_id}"
        }
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()

        debug = request.args.get('debug', '0') == '1'
        if debug:
            # Return raw JSON so we can inspect structure
            return jsonify(data)

        batters = []
        bowlers = []

        for innings in data.get('scoreCard', []):
            bat_team = innings.get('batTeamDetails', {})
            bowl_team = innings.get('bowlTeamDetails', {})

            for k, v in bat_team.get('batsmenData', {}).items():
                batters.append({
                    "name": v.get('batName', ''),
                    "runs": v.get('runs', 0),
                    "balls": v.get('balls', 0)
                })

            for k, v in bowl_team.get('bowlersData', {}).items():
                bowlers.append({
                    "name": v.get('bowlName', ''),
                    "wickets": v.get('wickets', 0),
                    "runs": v.get('runs', 0),
                    "overs": v.get('overs', 0)
                })

        return jsonify({"batters": batters, "bowlers": bowlers})

    except Exception as e:
        return jsonify({"error": str(e), "raw": res.text[:500] if 'res' in dir() else ''}), 500
