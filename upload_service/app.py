from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
from werkzeug.middleware.proxy_fix import ProxyFix
import os, uuid, zipfile, json

app = Flask(__name__)
CORS(app)

# 🔥 مهم جدًا
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

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
    proto = request.headers.get("X-Forwarded-Proto", request.scheme)
    host = request.headers.get("Host")
    return f"{proto}://{host}"

@app.route("/upload", methods=["POST"])
def upload():
    if not auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    files = request.files.getlist("images")
    visibility = request.form.get("visibility", "public")

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

    meta = {"visibility": visibility, "images": urls}

    with open(os.path.join(album_path, "meta.json"), "w") as m:
        json.dump(meta, m)

    zip_path = os.path.join(ZIP_DIR, f"{album_id}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for img_name in os.listdir(album_path):
            if img_name.endswith(".webp"):
                z.write(os.path.join(album_path, img_name), img_name)

    return jsonify({
        "images": urls,
        "album_url": f"{base_url()}/album/{album_id}",
        "zip_url": f"{base_url()}/archive/{album_id}"
    })

@app.route("/image/<album>/<name>")
def image(album, name):
    return send_file(os.path.join(IMG_DIR, album, name), mimetype="image/webp")

@app.route("/archive/<album>")
def archive(album):
    return send_file(os.path.join(ZIP_DIR, f"{album}.zip"), as_attachment=True)

@app.route("/album/<album>")
def album(album):
    meta_path = os.path.join(IMG_DIR, album, "meta.json")
    if not os.path.exists(meta_path):
        return jsonify({"error": "not found"}), 404

    with open(meta_path) as f:
        meta = json.load(f)

    if meta["visibility"] == "private":
        return jsonify({"error": "private"}), 403

    return jsonify(meta)

if __name__ == "__main__":
    app.run()
