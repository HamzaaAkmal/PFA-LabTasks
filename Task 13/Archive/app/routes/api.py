from flask import jsonify, request
from app.config import Config
from app.services.container import get_document_service, get_embedding_service, get_exam_service, get_rag_service, get_vector_store_service
from app.utils.file_utils import allowed_file, safe_filename

def register_api_routes(app):
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "200",
            "local_models": {
                "embedding": Config.EMBEDDING_MODEL_NAME
            }
        })

    @app.route("/api/stats", methods=["GET"])
    def stats():
        vs = get_vector_store_service()
        return jsonify(vs.stats())

    @app.route("/api/upload", methods=["POST"])
    def upload_documents():
        doc_service = get_document_service()
        emb_service = get_embedding_service()
        vs_service = get_vector_store_service()

        files = request.files.getlist("files")

        if not files:
            return jsonify({"Oops": "please give at least one file bro"}), 400

        uploaded = []
        all_chunks = []
        all_metadata = []

        for f in files:
            name = f.filename

            if not name:
                continue

            if not allowed_file(name, Config.ALLOWED_EXTENSIONS):
                return jsonify({"Oops": "please upload only pdf, md or txt file not any other file" + name}), 400

            clean = safe_filename(name)

            path = doc_service.save_upload(f, clean)
            text = doc_service.extract_text(path)
            chunks = doc_service.chunk_text(text)

            if not chunks:
                continue

            i = 0
            for c in chunks:
                all_chunks.append(c)

                meta = {
                    "file_name": clean,
                    "chunk_id": i,
                    "text": c,
                    "source_path": str(path)
                }

                all_metadata.append(meta)

                i += 1

            uploaded.append({
                "file": clean,
                "chunks": len(chunks)
            })

        if not all_chunks:
            return jsonify({"Oops": "please upload good file which can be processed"}), 400

        embeddings = emb_service.embed_texts(all_chunks)
        added = vs_service.add(embeddings, all_metadata)

        return jsonify({
            "message": "uploaded",
            "uploaded": uploaded,
            "chunks_added": added,
            "stats": vs_service.stats()
        })

    @app.route("/api/ask", methods=["POST"])
    def ask_question():
        rag = get_rag_service()

        data = request.get_json(silent=True) or {}

        question = data.get("question", "").strip()
        top_k = data.get("top_k", Config.DEFAULT_TOP_K)

        if question == "":
            return jsonify({"Oops": "question missing"}), 400

        answer = rag.answer_question(question, top_k=int(top_k))

        return jsonify(answer)

    @app.route("/api/generate-exam", methods=["POST"])
    def generate_exam():
        exam = get_exam_service()

        data = request.get_json(silent=True) or {}

        topic = data.get("topic", "").strip()
        num = int(data.get("num_questions", 5))

        if num < 1:
            num = 1
        if num > 20:
            num = 20

        questions = exam.generate_questions(topic=topic, count=num)

        if not questions:
            return jsonify({"Oops": "no content provided, upload first"}), 400

        return jsonify({
            "topic": topic if topic else "General",
            "questions": questions
        })