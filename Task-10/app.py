from flask import Flask, render_template, request, jsonify
import json
import re
from pathlib import Path
from collections import Counter

app = Flask(__name__)

base_dir = Path(__file__).resolve().parent
data_path = base_dir / "data" / "superior_faq.json"


with open(data_path, "r", encoding="utf-8") as f:
    faq_data = json.load(f)


# simple text process for matching
def clean_text(txt):
    txt = txt.lower()
    txt = re.sub(r"[^a-z0-9\s]", " ", txt)
    toks = [t for t in txt.split() if t.strip()]
    return toks


# small nlp idea: keyword overlap score
def find_best_answer(user_msg):
    user_tokens = clean_text(user_msg)
    if len(user_tokens) == 0:
        return "Please type your question about admission, programs, or deadlines."

    user_count = Counter(user_tokens)

    best_item = None
    best_scrore = 0

    for item in faq_data:
        key_tokens = item.get("keywords", []) + clean_text(item.get("question", ""))
        key_count = Counter(key_tokens)

        common = sum((user_count & key_count).values())
        len_bonus = min(len(user_tokens), len(key_tokens)) * 0.02
        total_score = common + len_bonus

        if total_score > best_scrore:
            best_scrore = total_score
            best_item = item

    if best_item and best_scrore >= 1:
        return f"{best_item['answer']}\nSource: {best_item['source']}"

    return (
        "I could not fully match that. Try asking: admissions open, fee structure, "
        "how to apply, contact number, or campus location."
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat_api():
    body = request.get_json(silent=True) or {}
    msg = body.get("message", "")

    respnse = find_best_answer(msg)
    return jsonify({"reply": respnse})


if __name__ == "__main__":
    app.run(debug=True)
