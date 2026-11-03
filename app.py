import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

CLIENT_ID = os.environ.get("SC_CLIENT_ID", "QhVEWrrJKvW4uSU5u5EoI0FTXYUGzy5k")
SC_API = "https://api-v2.soundcloud.com"

def extract_user_id(value: str) -> str:
    if not value:
        return ""
    if ":" in value:
        return value.rsplit(":", 1)[-1]
    return value

@app.route("/health")
def health():
    return jsonify({"ok": True})

@app.route("/likes")
def likes():
    user = request.args.get("user_id") or request.args.get("urn") or ""
    user_id = extract_user_id(user)
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    limit = request.args.get("limit", "200")
    offset = request.args.get("offset", "0")
    url = f"{SC_API}/users/{user_id}/track_likes"
    params = {
        "client_id": CLIENT_ID,
        "limit": limit,
        "offset": offset,
    }

    try:
        r = requests.get(url, params=params, timeout=15)
    except requests.RequestException as e:
        return jsonify({"error": f"upstream error: {e}"}), 502

    if r.status_code != 200:
        return jsonify({"error": f"upstream HTTP {r.status_code}", "body": r.text[:300]}), 502

    try:
        data = r.json()
    except ValueError:
        return jsonify({"error": "upstream returned non-JSON"}), 502

    collection = data.get("collection", [])
    tracks = []
    for item in collection:
        track = item.get("track") if isinstance(item, dict) else None
        if isinstance(track, dict):
            tracks.append(track)

    return jsonify({
        "collection": tracks,
        "has_more": data.get("has_more", False),
        "next_href": data.get("next_href"),
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)