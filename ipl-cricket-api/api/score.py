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
            # Find all div classes in the page to identify structure
            all_classes = set()
            for div in soup.find_all('div', class_=True)[:200]:
                for c in div.get('class', []):
                    all_classes.add(c)
            # Also grab a snippet around scorecard
            scrd = soup.find('div', class_=lambda x: x and 'scrd' in x)
            snippet = str(scrd)[:2000] if scrd else "no scrd div found"
            return jsonify({
                "classes_sample": sorted(list(all_classes))[:80],
                "scrd_snippet": snippet
            })

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
