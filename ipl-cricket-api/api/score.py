from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/score')
def score():
    match_id = request.args.get('id')
    debug = request.args.get('debug', '0') == '1'

    if not match_id:
        return jsonify({"error": "Missing id parameter"}), 400

    try:
        url = f"https://www.cricbuzz.com/live-cricket-scores/{match_id}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        if debug:
            # Find any element containing a known player name
            text_blocks = []
            for tag in soup.find_all(['div','span','td'], string=True):
                t = tag.get_text(strip=True)
                if any(name in t for name in ['Kohli','Kishan','Head','Sharma','Patel','Klaasen','Pandya']):
                    text_blocks.append({
                        "tag": tag.name,
                        "classes": tag.get('class', []),
                        "parent_classes": tag.parent.get('class', []) if tag.parent else [],
                        "text": t
                    })
            return jsonify({"player_elements": text_blocks[:20]})

        batters = []
        bowlers = []
        return jsonify({"batters": batters, "bowlers": bowlers})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
