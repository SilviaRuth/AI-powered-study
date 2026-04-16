# Architecture

```text
frontend
  index.html
  chat-app.js
  upload.js
  docs.js

FastAPI app
  backend/app.py
  backend/routes/*
  backend/services/*

RAG core
  parser -> chunking -> metadata-rich chunks
  dense retriever (FAISS + OpenAI embeddings)
  sparse retriever (local BM25)
  hybrid fusion -> dedupe -> optional rerank
  context compression -> answer generation -> citations

Local persistence
  data/uploads/
  data/processed/
  data/history.json
  vector_store/dense/
  vector_store/sparse/
```

The design stays local-first and keeps the original product flow intact while separating routing, services, retrieval, storage, and evaluation concerns.
