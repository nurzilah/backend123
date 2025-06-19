from flask import Blueprint, jsonify, current_app
from pymongo import MongoClient
import urllib.parse


chart = Blueprint("chart", __name__)

# Fungsi bantu: konversi string views ke angka
def parse_views(view_str):
    if not view_str:
        return 0
    view_str = view_str.lower().replace(" views", "")
    multiplier = 1
    if "k" in view_str:
        multiplier = 1_000
        view_str = view_str.replace("k", "")
    elif "m" in view_str:
        multiplier = 1_000_000
        view_str = view_str.replace("m", "")
    try:
        return int(float(view_str) * multiplier)
    except:
        return 0

@chart.route("/top-videos", methods=["GET"])
def get_top_videos():
    client = MongoClient(current_app.config["MONGO_URI"])
    db = client["big_data"]
    collection = db["crawling_yt_revisi1"]

    videos = []
    for doc in collection.find():
        if "views" in doc and doc["views"]:
            views = parse_views(doc["views"])
            videos.append({
                "title": doc.get("title", "")[:50],
                "views": views,
                "url": doc.get("url", "")
            })

    sorted_videos = sorted(videos, key=lambda x: x["views"], reverse=True)[:5]
    return jsonify(sorted_videos), 200

@chart.route('/top-channels', methods=['GET'])
def top_channels():
    # Koneksi ke MongoDB
    client = MongoClient(current_app.config["MONGO_URI"])
    db = client["big_data"]
    collection = db["crawling_yt_revisi1"]

    # Pipeline agregasi MongoDB
    pipeline = [
        {
            "$match": {
                "channel": {"$exists": True, "$ne": ""}
            }
        },
        {
            "$group": {
                "_id": "$channel",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"count": -1}
        },
        {
            "$limit": 10
        }
    ]

    # Jalankan agregasi
    results = list(collection.aggregate(pipeline))

    # Buat response dengan link YouTube
    data = []
    for r in results:
        channel_name = r["_id"]
        encoded_name = urllib.parse.quote_plus(channel_name) if channel_name else ""
        data.append({
            "channel": channel_name,
            "count": r["count"],
            "url": f"https://www.youtube.com/results?search_query={encoded_name}"
        })

    return jsonify(data), 200