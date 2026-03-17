# AI-powered-study

AI Knowledge Assistant built with FastAPI, OpenAI, FAISS, Bootstrap, and jQuery.

## Features

- Upload PDF and TXT documents
- Chunk and embed documents with OpenAI embeddings
- Store vectors locally in FAISS
- Ask grounded questions against uploaded content
- Return "I don't know" when the answer is not in retrieved context
- Keep chat history between requests
- Simple responsive chat-style frontend

## Project Structure

```text
backend/
  app.py
  routes.py
  rag/
    chunking.py
    embeddings.py
    pipeline.py
    retriever.py
frontend/
  index.html
  chat.js
  styles.css
data/
  uploads/
vector_store/
requirements.txt
```

## Setup

1. Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Set environment variables.

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
$env:OPENAI_CHAT_MODEL="gpt-4.1-mini"
$env:OPENAI_EMBEDDING_MODEL="text-embedding-3-small"
```

4. Start the app.

```powershell
uvicorn backend.app:app --reload
```

5. Open http://127.0.0.1:8000

## API Endpoints

- `POST /api/upload` uploads and indexes a PDF or TXT file
- `POST /api/query` answers a question using retrieved chunks
- `GET /api/history` returns chat history
- `POST /api/history/clear` clears stored chat history

## Notes

- Uploaded files are saved in `data/uploads/`
- FAISS index data is saved in `vector_store/`
- Chat history is saved in `data/history.json`
- If no relevant context is available, the assistant is instructed to answer with `I don't know`

## Demo Flow

1. Upload a PDF or TXT document.
2. Wait for indexing to finish.
3. Ask a question about the uploaded material.
4. Review the answer and retrieved chunk references in the UI.
