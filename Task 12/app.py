import json
from pathlib import Path

import faiss
import numpy as np
from flask import Flask, jsonify, render_template, request
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent
STORE_DIR = BASE_DIR / "index_store"
INDEX_FILE = STORE_DIR / "qna.index"
META_FILE = STORE_DIR / "qna_meta.json"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

app = Flask(__name__)

model = None
index = None
meta = []


def load_bot_data():
    global model, index, meta

    if not INDEX_FILE.exists() or not META_FILE.exists():
        raise FileNotFoundError(
            "Index files not found. Run preprocess_and_index.py first."
        )

    model = SentenceTransformer(MODEL_NAME)
    index = faiss.read_index(str(INDEX_FILE))

    with open(META_FILE, "r", encoding="utf-8") as f:
        meta = json.load(f)


def search_qna(user_query, top_k=3):
    q_vec = model.encode([user_query], convert_to_numpy=True, normalize_embeddings=True)
    q_vec = q_vec.astype(np.float32)

    scores, idxs = index.search(q_vec, top_k)

    out = []
    for score, i in zip(scores[0], idxs[0]):
        if i < 0 or i >= len(meta):
            continue

        out.append(
            {
                "question": meta[i]["question"],
                "answer": meta[i]["answer"],
                "score": float(score),
            }
        )

    return out


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    body = request.get_json(silent=True) or {}
    user_q = body.get("question", "").strip()

    if not user_q:
        return jsonify({"reply": "Please type your question.", "matches": []})

    matches = search_qna(user_q, top_k=3)

    if not matches:
        return jsonify(
            {
                "reply": "Sorry, I could not find a close match in my dataset.",
                "matches": [],
            }
        )

    best = matches[0]
    reply = best["answer"]

    return jsonify({"reply": reply, "matches": matches})


if __name__ == "__main__":
    load_bot_data()
    app.run(debug=True, port=5011)
