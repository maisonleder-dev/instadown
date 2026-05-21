from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp
import traceback
import requests

app = Flask(__name__)
CORS(app)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Referer": "https://www.instagram.com/",
}

def get_video_info(url):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "format": "bestvideo+bestaudio/best",
        "http_headers": HEADERS,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    thumbnail = info.get("thumbnail", "")
    title = info.get("title", "video_instagram")

    video_url = None
    formats = info.get("formats", [])
    if formats:
        best = None
        for f in reversed(formats):
            if f.get("vcodec") != "none" and f.get("acodec") != "none":
                best = f
                break
        if not best:
            best = formats[-1]
        video_url = best.get("url")
    else:
        video_url = info.get("url")

    return title, thumbnail, video_url


@app.route("/api/info", methods=["POST"])
def get_info():
    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "URL manquante"}), 400
    if "instagram.com" not in url:
        return jsonify({"error": "Lien Instagram invalide"}), 400

    try:
        title, thumbnail, video_url = get_video_info(url)
        if not video_url:
            return jsonify({"error": "Impossible de récupérer la vidéo"}), 500

        return jsonify({
            "title": title,
            "thumbnail": thumbnail,
            "video_url": video_url,
        })

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/api/download", methods=["POST"])
def download_video():
    """
    Le backend récupère la vidéo et la streame directement au navigateur.
    Le fichier se télécharge proprement comme sur SnapInsta.
    """
    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "URL manquante"}), 400
    if "instagram.com" not in url:
        return jsonify({"error": "Lien Instagram invalide"}), 400

    try:
        title, thumbnail, video_url = get_video_info(url)

        if not video_url:
            return jsonify({"error": "Impossible de récupérer la vidéo"}), 500

        # Le backend fait la requête vers Instagram et streame la réponse
        r = requests.get(video_url, headers=HEADERS, stream=True, timeout=60)

        filename = title.replace(" ", "_").replace("/", "-")[:60] + ".mp4"

        def generate():
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        return Response(
            generate(),
            content_type="video/mp4",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": r.headers.get("Content-Length", ""),
            }
        )

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)