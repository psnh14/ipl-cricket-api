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
            # Return first 5000 chars of HTML to inspect structure
            return app.response_class(
                response=res.text[:5000],
                status=200,
                mimetype='text/html'
            )

        batters = []
        for row in soup.select("div.cb-col.cb-col-100.cb-ltst-wgt-hdr"):
            name_el = row.select_one("div.cb-col.cb-col-50 a")
            runs_el = row.select("div.cb-col.cb-col-10.text-right")
            if name_el and len(runs_el) >= 2:
                batters.append({
                    "name": name_el.text.strip(),
                    "runs": runs_el[0].text.strip(),
                    "balls": runs_el[1].text.strip()
                })

        bowlers = []
        for row in soup.select("div.cb-col.cb-col-100.cb-scrd-itms"):
            name_el = row.select_one("div.cb-col.cb-col-40 a")
            stats = row.select("div.cb-col.cb-col-10.text-right")
            if name_el and len(stats) >= 4:
                bowlers.append({
                    "name": name_el.text.strip(),
                    "overs": stats[0].text.strip(),
                    "runs": stats[2].text.strip(),
                    "wickets": stats[3].text.strip()
                })

        return jsonify({"batters": batters, "bowlers": bowlers})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
