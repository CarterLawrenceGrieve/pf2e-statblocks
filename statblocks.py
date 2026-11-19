"""PF2e stat block printer.

Runs a small local web app that searches Archives of Nethys (2e.aonprd.com)
creatures and lays out their stat blocks for printing, several per page.

AoN's search backend refuses browser requests from other sites, so this
script proxies it from localhost. Standard library only.

    python statblocks.py            # opens http://127.0.0.1:8765
    python statblocks.py --port 9000 --no-browser
"""
import argparse
import json
import re
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ES_URL = "https://elasticsearch.aonprd.com/aon/_search"
HERE = Path(__file__).resolve().parent
SEARCH_FIELDS = ["name", "level", "trait", "id", "url", "source", "rarity", "size"]


def es(query: dict) -> dict:
    req = urllib.request.Request(
        ES_URL,
        data=json.dumps(query).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "pf2e-statblock-printer/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def creature_filter():
    return {
        "filter": [{"term": {"category": "creature"}}],
        "must_not": [{"term": {"exclude_from_search": True}}],
    }


def search(q: str, size: int = 25):
    q = q.strip()
    if not q:
        return []
    body = {
        "size": size,
        "_source": SEARCH_FIELDS,
        "query": {
            "bool": {
                **creature_filter(),
                "should": [
                    {"term": {"name.keyword": {"value": q, "boost": 20}}},
                    {"match_phrase_prefix": {"name": {"query": q, "boost": 5}}},
                    {"match": {"name": {"query": q, "operator": "and", "fuzziness": "AUTO"}}},
                ],
                "minimum_should_match": 1,
            }
        },
    }
    hits = es(body)["hits"]["hits"]
    out = [h["_source"] for h in hits]
    # exact (case-insensitive) name matches first
    out.sort(key=lambda s: 0 if s.get("name", "").lower() == q.lower() else 1)
    return out


def creature(cid: str):
    body = {
        "size": 1,
        "_source": ["name", "level", "url", "id", "summary", "markdown"],
        "query": {"bool": {**creature_filter(), "must": [{"ids": {"values": [cid]}}]}},
    }
    hits = es(body)["hits"]["hits"]
    return hits[0]["_source"] if hits else None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # quiet
        pass

    def send(self, code, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        # lets index.html opened from disk (origin "null") call the API
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def json(self, obj, code=200):
        self.send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        try:
            if u.path in ("/", "/index.html"):
                self.send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
            elif u.path == "/api/search":
                self.json(search(qs.get("q", [""])[0]))
            elif u.path == "/api/creature":
                cid = qs.get("id", [""])[0]
                if not re.fullmatch(r"creature-\d+", cid):
                    return self.json({"error": "bad id"}, 400)
                c = creature(cid)
                self.json(c if c else {"error": "not found"}, 200 if c else 404)
            else:
                self.send(404, b"not found", "text/plain; charset=utf-8")
        except (urllib.error.URLError, TimeoutError) as e:
            self.json({"error": f"Archives of Nethys unreachable: {e}"}, 502)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    except OSError:
        srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)  # port busy: take any free one
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    print(f"PF2e stat block printer running at {url}  (Ctrl+C to stop)")
    if not a.no_browser:
        threading.Timer(0.5, webbrowser.open, [url]).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
