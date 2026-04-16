# AI-powered-study

AI-powered-study is a lightweight local-first RAG study assistant built with FastAPI, OpenAI, FAISS, a local BM25 index, and a small jQuery frontend.

## Overview

The upgraded app preserves the original flow:

1. Upload PDF or TXT files
2. Parse and index content
3. Ask grounded questions
4. Get answers with evidence-linked citations
5. Keep chat history

It now adds modular backend layers, page-aware parsing, metadata-rich chunking, hybrid retrieval, optional reranking, document management, and a local evaluation workflow.

## Architecture

```text
frontend/
  index.html
  chat-app.js
  upload.js
  docs.js
  styles.css
  rag-upgrade.css

backend/
  app.py
  routes/
  services/
  core/
  models/
  rag/
    parser.py
    chunking.py
    ingest.py
    query_rewrite.py
    retrieval/
    generation/
    storage/
  evaluation/
  tests/

data/
  uploads/
  processed/
  history.json
  eval/

vector_store/
  dense/
  sparse/
```

See [architecture](docs/architecture.md), [RAG design](docs/rag_design.md), [benchmark notes](docs/benchmark.md), and [roadmap](docs/roadmap.md).

## Feature List

- Upload and index PDF and TXT documents
- Page-aware PDF parsing and structure-aware chunking
- Rich chunk metadata with document id, chunk id, pages, section title, and token count
- Dense retrieval with OpenAI embeddings and FAISS
- Sparse retrieval with a local BM25 index
- Hybrid retrieval with reciprocal rank fusion
- Deduplication before generation
- Optional query rewriting and optional reranking
- Evidence-linked answers with structured source cards
- Document registry, list, delete, and rebuild endpoints
- Chat history persisted to JSON
- Local evaluation script and starter benchmark dataset

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

3. Configure environment variables.

```powershell
Copy-Item .env.example .env
$env:OPENAI_API_KEY="your_openai_api_key_here"
```

Important variables:

- `OPENAI_CHAT_MODEL`
- `OPENAI_EMBEDDING_MODEL`
- `RAG_CHUNK_SIZE_WORDS`
- `RAG_CHUNK_OVERLAP_WORDS`
- `RAG_TOP_K`
- `RAG_HYBRID_DENSE_WEIGHT`
- `RAG_HYBRID_SPARSE_WEIGHT`
- `RAG_RERANK_ENABLED`
- `RAG_QUERY_REWRITE_ENABLED`
- `LOG_LEVEL`

4. Start the app.

```powershell
uvicorn backend.app:app --reload
```

5. Open `http://127.0.0.1:8000`.

## API Endpoints

Existing endpoints:

- `POST /api/upload`
- `POST /api/query`
- `GET /api/history`
- `POST /api/history/clear`

New endpoints:

- `GET /api/documents`
- `DELETE /api/documents/{document_id}`
- `POST /api/documents/rebuild`
- `POST /api/eval/run`

## Retrieval Pipeline

1. Parse uploaded files into page-aware blocks.
2. Build structure-aware chunks with metadata.
3. Index chunks into FAISS and BM25.
4. Optionally rewrite conversational queries.
5. Retrieve dense and sparse candidates.
6. Fuse rankings, dedupe, and optionally rerank.
7. Compress evidence spans.
8. Generate a grounded answer with citation ids.
9. Return the final answer plus structured evidence cards.

## Evaluation

Starter benchmark examples live in `data/eval/golden_set.json`.

Run evaluation:

```powershell
python scripts/run_eval.py
```

The JSON report is written to `data/eval/last_run.json`.

## Local Commands

Run the app:

```powershell
uvicorn backend.app:app --reload
```

Rebuild indexes:

```powershell
python scripts/rebuild_index.py
```

Seed demo benchmark notes:

```powershell
python scripts/seed_demo_data.py
```

Run tests:

```powershell
pytest backend/tests
```

## Design Tradeoffs

- The stack stays direct and readable instead of adding a larger framework.
- Storage remains local JSON plus local vector and sparse indexes.
- Reranking and rewriting are optional so the base workflow stays inexpensive.
- The answer generator fails safe to `I don't know` when evidence or citations are insufficient.

## Screenshots

- UI screenshot placeholder
- Evidence card screenshot placeholder
- Documents panel screenshot placeholder

## Migration Notes

- Dense index files now live in `vector_store/dense/` and sparse artifacts live in `vector_store/sparse/`.
- Existing legacy FAISS files at the old root vector store path may need a rebuild if they do not have matching processed chunk artifacts.
- If older local index files behave unexpectedly, delete the local store contents and run `python scripts/rebuild_index.py` after reprocessing documents.
