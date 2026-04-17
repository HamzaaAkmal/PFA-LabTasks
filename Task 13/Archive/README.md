# Smart Learning and Exam Prep Assistant (Local RAG)

A modular local Retrieval-Augmented Generation (RAG) application built with Flask and a static frontend. The project indexes uploaded study material and supports both contextual Q&A and exam-style question generation without external AI API calls.

## Contents

- [Overview](#overview)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Run Locally](#run-locally)
- [API Endpoints](#api-endpoints)
- [Font Setup](#font-setup)
- [Operational Notes](#operational-notes)

## Overview

Core capabilities:

- Upload study files (`.pdf`, `.txt`, `.md`).
- Extract and chunk text for indexing.
- Generate local embeddings with `all-MiniLM-L6-v2`.
- Retrieve relevant context using cosine similarity over persisted vectors.
- Answer questions from indexed material.
- Generate exam-style practice questions from retrieved content.

## Technology Stack

- Backend: Flask (modular blueprint + service layer)
- Frontend: Static HTML/CSS/JavaScript (API-driven)
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2` (local)
- PDF parsing: `pypdf`
- Vector retrieval: local NumPy cosine similarity over persisted embeddings

## Architecture

The architecture is documented using image-based diagrams.

### System Architecture

![System Architecture](System%20Architecture.png)

### Runtime Data Flow

![Runtime Data Flow](Runtime%20Data%20Flow%20.png)

## Project Structure

```text
app/
  __init__.py
  config.py
  routes/
    api.py
  services/
    container.py
    document_service.py
    embedding_service.py
    exam_service.py
    rag_service.py
    vector_store_service.py
  utils/
    file_utils.py
    text_utils.py
data/
  processed/
  uploads/
  vector_store/
frontend/
  index.html
  assets/
    css/styles.css
    js/app.js
    fonts/
      README.txt
run.py
requirements.txt
```

## Run Locally

1. Create a virtual environment and install dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Start the application.

```bash
python run.py
```

3. Open the application in your browser.

```text
http://127.0.0.1:5000
```

## API Endpoints

- `GET /api/health`: service health and embedding model information.
- `GET /api/stats`: indexed file and chunk statistics.
- `POST /api/upload`: upload and index documents.
- `POST /api/ask`: retrieve context and answer a question.
- `POST /api/generate-exam`: generate exam-style questions from indexed content.

## Font Setup

The frontend is configured to load `Poppins` bold from a local file using `@font-face`.

Place the font at:

```text
frontend/assets/fonts/Poppins-Bold.ttf
```

No external font CDN is required.

## Operational Notes

- The first embedding request may be slower because the model is loaded lazily.
- Indexed vectors are persisted under `data/vector_store/`.
- Uploaded files are stored under `data/uploads/`.
