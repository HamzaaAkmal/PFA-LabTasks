Task-11 (Lab 12 - Task 1)

This project is a QnA bot using the same pipeline discussed in class:
1) Preprocess text based QnA dataset
2) Embed using Hugging Face MiniLM
3) Store vectors in FAISS
4) Search by similarity
5) Show result in Flask + HTML UI

Topic selected from Lab 10:
- University Admission QnA

Files:
- data/admission_qna.json               -> dataset
- preprocess_and_index.py               -> preprocessing + embeddings + FAISS index build
- app.py                                -> Flask app for similarity search bot
- templates/index.html                  -> UI page
- static/css/style.css                  -> UI styles
- static/js/main.js                     -> UI interaction
- index_store/                          -> generated index and metadata

Run steps:
1. Install requirements
   pip install -r requirements.txt

2. Build vectors and FAISS index
   python preprocess_and_index.py

3. Run flask app
   python app.py

4. Open in browser
   http://127.0.0.1:5011

Note:
- HadithBot.ipynb file is not present in this workspace, so it could not be run here.
- If you add that notebook file, I can run it too.
