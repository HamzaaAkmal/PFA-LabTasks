import os
import logging
from datetime import datetime

import cv2
import numpy as np
import easyocr
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO
from flask import Flask, request, jsonify, render_template, send_from_directory

# ── App Setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
MODEL_PATH      = "best.pt"
FONT_BOLD       = os.path.join("fonts", "Poppins", "Poppins-Bold.ttf")
FONT_REGULAR    = os.path.join("fonts", "Poppins", "Poppins-Regular.ttf")
SLIPS_DIR       = os.path.join("static", "slips")
os.makedirs(SLIPS_DIR, exist_ok=True)

# ── Load Models Once ───────────────────────────────────────────────────────────
log.info("Loading YOLO model …")
yolo_model = YOLO(MODEL_PATH)
log.info("Loading EasyOCR reader …")
ocr_reader = easyocr.Reader(["en"], gpu=True)
log.info("Models ready.")


# ── Helpers ────────────────────────────────────────────────────────────────────
def detect_plate(image_np):
    """Run YOLO detection. Returns bounding box (x1,y1,x2,y2) or None."""
    results = yolo_model(image_np, save=False, verbose=False)
    boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
    if len(boxes) == 0:
        return None
    return tuple(boxes[0])  # (x1, y1, x2, y2)


def extract_text(image_np, box):
    """Crop detected plate and run EasyOCR. Returns (plate_text, cropped_img)."""
    x1, y1, x2, y2 = box
    pad = 4
    crop = image_np[
        max(0, y1 - pad): min(image_np.shape[0], y2 + pad),
        max(0, x1 - pad): min(image_np.shape[1], x2 + pad),
    ]
    if crop.size == 0:
        return "Crop Error", crop

    raw = ocr_reader.readtext(crop, detail=1, paragraph=False)
    log.info("EasyOCR raw: %s", raw)

    texts = [
        "".join(filter(str.isalnum, text)).upper()
        for (_, text, conf) in raw
        if conf >= 0.2
    ]
    plate_text = " ".join(t for t in texts if t) or "No text detected"
    return plate_text, crop


def generate_slip(plate_text, entry_time):
    """Draw a parking slip PNG. Returns the saved file path."""
    W, H = 600, 380
    BG       = "#0D0D1A"   # very dark navy (matches dashboard)
    PURPLE   = "#7C3AED"   # vivid purple accent
    PURPLE_L = "#A78BFA"   # light purple for labels
    WHITE    = "#FFFFFF"
    GRAY     = "#94A3B8"
    BORDER   = "#4C1D95"

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        f_title  = ImageFont.truetype(FONT_BOLD,    30)
        f_label  = ImageFont.truetype(FONT_REGULAR, 16)
        f_value  = ImageFont.truetype(FONT_BOLD,    18)
        f_small  = ImageFont.truetype(FONT_REGULAR, 12)
    except Exception:
        f_title = f_label = f_value = f_small = ImageFont.load_default()

    # Border
    draw.rounded_rectangle([12, 12, W - 12, H - 12], radius=14, outline=BORDER, width=2)

    # Purple accent bar at top
    draw.rounded_rectangle([12, 12, W - 12, 60], radius=14, fill=PURPLE)

    # Title
    title = "PARKING RECEIPT"
    bbox  = draw.textbbox((0, 0), title, font=f_title)
    draw.text(((W - (bbox[2] - bbox[0])) / 2, 18), title, font=f_title, fill=WHITE)

    # Divider
    draw.line([(40, 75), (W - 40, 75)], fill=BORDER, width=1)

    # Rows
    rows = [
        ("Vehicle Plate", plate_text),
        ("Entry Time",    entry_time.strftime("%d %b %Y  %H:%M:%S")),
        ("Parking Fee",   "Rs. 30.00"),
        ("Status",        "ACTIVE"),
    ]
    y = 95
    for label, value in rows:
        draw.text((50, y), label, font=f_label, fill=PURPLE_L)
        draw.text((270, y), value, font=f_value, fill=WHITE)
        y += 55

    # Footer
    footer = "Powered by Smart Parking System  •  YOLO + EasyOCR"
    bbox   = draw.textbbox((0, 0), footer, font=f_small)
    draw.text(((W - (bbox[2] - bbox[0])) / 2, H - 30), footer, font=f_small, fill=GRAY)

    # Save
    filename = f"slip_{plate_text.replace(' ', '_')}_{entry_time.strftime('%Y%m%d_%H%M%S')}.png"
    path     = os.path.join(SLIPS_DIR, filename)
    img.save(path)
    log.info("Slip saved: %s", path)
    return filename


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    """Receive image → detect plate → OCR → generate slip → return JSON."""
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Decode image
    file_bytes = np.frombuffer(file.read(), dtype=np.uint8)
    img_bgr    = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if img_bgr is None:
        return jsonify({"error": "Could not decode image"}), 400

    # Detection
    box = detect_plate(img_bgr)
    if box is None:
        return jsonify({"error": "No number plate detected in image"}), 200

    # OCR
    plate_text, crop = extract_text(img_bgr, box)

    # Save annotated image for display
    annotated = img_bgr.copy()
    x1, y1, x2, y2 = box
    cv2.rectangle(annotated, (x1, y1), (x2, y2), (124, 58, 237), 3)
    anno_path = os.path.join(SLIPS_DIR, "annotated_latest.jpg")
    cv2.imwrite(anno_path, annotated)

    # Save cropped plate
    crop_path = os.path.join(SLIPS_DIR, "crop_latest.jpg")
    cv2.imwrite(crop_path, crop)

    # Generate slip
    entry_time  = datetime.now()
    slip_file   = generate_slip(plate_text, entry_time)

    return jsonify({
        "plate":      plate_text,
        "entry_time": entry_time.strftime("%d %b %Y, %H:%M:%S"),
        "fee":        "Rs. 30.00",
        "slip_url":   f"/static/slips/{slip_file}",
        "anno_url":   "/static/slips/annotated_latest.jpg",
        "crop_url":   "/static/slips/crop_latest.jpg",
    })


@app.route("/static/slips/<path:filename>")
def serve_slip(filename):
    return send_from_directory(SLIPS_DIR, filename)


# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
