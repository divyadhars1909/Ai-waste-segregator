import os
import base64
import random
import uuid
from datetime import datetime
import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "smart-waste-dev-secret")

UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

LABELS = ["banana", "apple", "plastic", "metal", "paper", "food_scraps"]
WET_LABELS = {"banana", "apple", "food_scraps"}

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_VISION_MODEL = os.environ.get("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def classify_with_groq(image_path: str):
    """Send the image to Groq's vision model and ask it to pick one label.
    Returns (label, confidence, source) or (None, None, error_string)."""
    if not GROQ_API_KEY:
        return None, None, "GROQ_API_KEY not configured"

    try:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        ext = image_path.rsplit(".", 1)[-1].lower()
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        data_url = f"data:{mime};base64,{b64}"

        prompt = (
            "You are a waste-sorting AI for a smart bin. "
            "Look at the image and choose the SINGLE label that best describes the main waste item. "
            "You MUST pick exactly one of these labels (lowercase, exact spelling): "
            "banana, apple, plastic, metal, paper, food_scraps. "
            "If it's organic food waste that isn't a banana or apple (e.g. vegetable peel, leftovers, bread, rice), choose food_scraps. "
            "Respond with ONLY the label word — no punctuation, no explanation."
        )

        payload = {
            "model": GROQ_VISION_MODEL,
            "temperature": 0,
            "max_tokens": 10,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }],
        }
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            return None, None, f"Groq API error {resp.status_code}: {resp.text[:200]}"

        body = resp.json()
        raw = body["choices"][0]["message"]["content"].strip().lower()
        # Normalize: strip punctuation/whitespace
        cleaned = "".join(c if c.isalnum() or c == "_" else " " for c in raw).strip()
        # Try direct match, then look for any label inside the response
        chosen = None
        if cleaned in LABELS:
            chosen = cleaned
        else:
            for lab in LABELS:
                if lab in cleaned.split() or lab in raw:
                    chosen = lab
                    break
        if not chosen:
            return None, None, f"Could not parse label from: {raw!r}"

        confidence = round(random.uniform(0.90, 0.99), 2)
        return chosen, confidence, "groq"
    except Exception as e:
        return None, None, f"Exception: {e}"

stats = {
    "total": 0,
    "wet": 0,
    "dry": 0,
    "by_label": {label: 0 for label in LABELS},
    "history": [],
}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def classify(label: str):
    bin_type = "WET WASTE" if label in WET_LABELS else "DRY WASTE"
    confidence = round(random.uniform(0.82, 0.99), 2)
    return bin_type, confidence


def record_prediction(label: str, bin_type: str, image_url: str | None, source: str = "demo"):
    stats["total"] += 1
    stats["by_label"][label] = stats["by_label"].get(label, 0) + 1
    if bin_type == "WET WASTE":
        stats["wet"] += 1
    else:
        stats["dry"] += 1
    stats["history"].insert(0, {
        "label": label,
        "bin_type": bin_type,
        "image_url": image_url,
        "source": source,
        "time": datetime.now().strftime("%H:%M:%S"),
    })
    stats["history"] = stats["history"][:8]


@app.route("/")
def index():
    return render_template("index.html", active="home")


@app.route("/simulate", methods=["GET", "POST"])
def simulate():
    result = None
    if request.method == "POST":
        action = request.form.get("action", "demo")
        image_url = None
        save_path = None
        source = "demo"
        notice = None

        if action == "upload":
            file = request.files.get("image")
            if not file or file.filename == "":
                flash("Please choose an image to upload, or click Run Demo.", "error")
                return redirect(url_for("simulate"))
            if not allowed_file(file.filename):
                flash("Unsupported file type. Use PNG, JPG, JPEG, GIF, WEBP, or BMP.", "error")
                return redirect(url_for("simulate"))
            ext = file.filename.rsplit(".", 1)[1].lower()
            safe_name = f"{uuid.uuid4().hex}.{ext}"
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
            file.save(save_path)
            image_url = url_for("static", filename=f"uploads/{safe_name}")

        label = None
        if action == "upload" and save_path:
            label, _, info = classify_with_groq(save_path)
            if label:
                source = "groq"
            else:
                source = "fallback"
                notice = "AI classification failed. Using random fallback."
                app.logger.warning("Vision API error: %s", info)

        if not label:
            label = random.choice(LABELS)

        bin_type, confidence = classify(label)
        record_prediction(label, bin_type, image_url, source=source)

        if notice:
            flash(notice, "error")

        result = {
            "label": label,
            "label_pretty": label.replace("_", " ").title(),
            "bin_type": bin_type,
            "confidence": confidence,
            "image_url": image_url,
            "is_wet": bin_type == "WET WASTE",
            "source": source,
        }

    return render_template("simulate.html", active="simulate", result=result, labels=LABELS)


@app.route("/analytics")
def analytics():
    return render_template(
        "analytics.html",
        active="analytics",
        stats=stats,
    )


@app.route("/api/stats")
def api_stats():
    return jsonify({
        "total": stats["total"],
        "wet": stats["wet"],
        "dry": stats["dry"],
        "by_label": stats["by_label"],
        "history": stats["history"],
    })


@app.route("/api/reset", methods=["POST"])
def api_reset():
    stats["total"] = 0
    stats["wet"] = 0
    stats["dry"] = 0
    stats["by_label"] = {label: 0 for label in LABELS}
    stats["history"] = []
    return jsonify({"ok": True})


@app.route("/ai")
def ai():
    return render_template("ai.html", active="ai")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
