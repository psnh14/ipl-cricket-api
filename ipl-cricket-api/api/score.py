from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        match_id = params.get('id', [None])[0]

        if not match_id:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing id parameter"}).encode())
            return

        try:
            url = f"https://www.cricbuzz.com/live-cricket-scores/{match_id}"
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            # Batting
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

            # Bowling
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

            result = {"batters": batters, "bowlers": bowlers}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
