from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import os, uuid, zipfile, json

app = Flask(__name__)
CORS(app)

API_TOKEN = "SUPER_SECRET_TOKEN"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_BASE = os.path.join(BASE_DIR, "uploads")
IMG_DIR = os.path.join(UPLOAD_BASE, "products")
ZIP_DIR = os.path.join(UPLOAD_BASE, "archives")

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(ZIP_DIR, exist_ok=True)

def auth(req):
    return req.headers.get("Authorization") == f"Bearer {API_TOKEN}"

def base_url():
    return request.host_url.rstrip("/")

# ===================== UPLOAD =====================

@app.route("/upload", methods=["POST"])
def upload():
    if not auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    files = request.files.getlist("images")
    visibility = request.form.get("visibility", "private")

    if not files:
        return jsonify({"error": "No images"}), 400

    album_id = str(uuid.uuid4())
    album_path = os.path.join(IMG_DIR, album_id)
    os.makedirs(album_path)

    urls = []

    for f in files:
        if not f.mimetype.startswith("image/"):
            continue

        img = Image.open(f).convert("RGB")
        img.thumbnail((1200, 1200))

        name = f"{uuid.uuid4()}.webp"
        path = os.path.join(album_path, name)
        img.save(path, "WEBP", quality=80)

        urls.append(f"{base_url()}/image/{album_id}/{name}")

    meta = {
        "visibility": visibility,
        "images": urls
    }

    with open(os.path.join(album_path, "meta.json"), "w") as m:
        json.dump(meta, m)

    zip_path = os.path.join(ZIP_DIR, f"{album_id}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for img_name in os.listdir(album_path):
            if img_name.endswith(".webp"):
                z.write(
                    os.path.join(album_path, img_name),
                    img_name
                )

    return jsonify({
        "album_id": album_id,
        "images": urls,
        "album_url": f"{base_url()}/album/{album_id}",
        "zip_url": f"{base_url()}/archive/{album_id}"
    })

# ===================== IMAGE =====================

@app.route("/image/<album>/<name>")
def image(album, name):
    path = os.path.join(IMG_DIR, album, name)
    if not os.path.exists(path):
        return jsonify({"error": "Not found"}), 404

    return send_file(path, mimetype="image/webp")

# ===================== ALBUM =====================

@app.route("/album/<album>")
def album(album):
    meta_path = os.path.join(IMG_DIR, album, "meta.json")
    if not os.path.exists(meta_path):
        return jsonify({"error": "Not found"}), 404

    with open(meta_path) as f:
        meta = json.load(f)

    if meta["visibility"] == "private":
        return jsonify({"error": "Private album"}), 403

    return jsonify(meta)

# ===================== ZIP =====================

@app.route("/archive/<album>")
def archive(album):
    zip_path = os.path.join(ZIP_DIR, f"{album}.zip")
    if not os.path.exists(zip_path):
        return jsonify({"error": "Not found"}), 404

    return send_file(zip_path, as_attachment=True)

# ===================== RUN =====================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
