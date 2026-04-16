# AI-powered-study — RAG Upgrade Specification for Codex

## 1) Objective
Upgrade the current **AI-powered-study** repository from a baseline single-index([github.com](https://github.com/SilviaRuth/AI-powered-study))more robust, portfolio-grade AI study assistant with:
- modular backend structure
- richer document parsing and metadata
- hybrid retrieval (dense + sparse)
- reranking
- evidence-linked answers with citations
- document registry and management
- evaluation scripts and benchmark dataset
- improved README and developer experience

This work must preserve the current core product flow:
1. upload PDF/TXT
2. index content
3. ask grounded questions
4. return answer and supporting sources
5. keep chat history

Do **not** remove the existing functionality. Refactor and extend it safely.

---

## 2) Current repo assumptions
The current repo is a small FastAPI app with this approximate layout:

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
README.md
```

Current behavior to preserve:
- upload and index PDF/TXT files
- use OpenAI embeddings
- store vectors locally
- query against uploaded content
- answer with grounded context and fallback to “I don’t know” when unsupported
- persist chat history

---

## 3) Target architecture
Implement this target backend structure:

```text
backend/
  app.py
  routes/
    upload.py
    query.py
    history.py
    docs.py
    eval.py
  core/
    config.py
    logging.py
    exceptions.py
  models/
    schemas.py
  services/
    document_service.py
    query_service.py
    history_service.py
  rag/
    pipeline.py
    ingest.py
    parser.py
    chunking.py
    metadata.py
    query_rewrite.py
    retrieval/
      dense_retriever.py
      bm25_retriever.py
      hybrid_retriever.py
      reranker.py
      dedupe.py
    generation/
      prompt_builder.py
      answer_generator.py
      citation_builder.py
      context_compressor.py
    storage/
      faiss_store.py
      bm25_store.py
      doc_registry.py
  evaluation/
    dataset_loader.py
    retrieval_eval.py
    answer_eval.py
    benchmark_runner.py
  tests/
    test_chunking.py
    test_retrieval.py
    test_citations.py
    test_api.py

frontend/
  index.html
  chat.js
  upload.js
  docs.js
  styles.css

data/
  uploads/
  processed/
  history.json
  eval/
    golden_set.json

vector_store/
  dense/
  sparse/

scripts/
  rebuild_index.py
  run_eval.py
  seed_demo_data.py

docs/
  architecture.md
  rag_design.md
  benchmark.md
  roadmap.md

requirements.txt
.env.example
README.md
```

If some files are unnecessary for the current implementation, create only the ones required for the completed features. However, the public module boundaries should follow this design.

---

## 4) Non-functional requirements
- Keep the code Pythonic, readable, and typed where practical.
- Preserve existing API behavior unless there is a clear upgrade path.
- Avoid introducing breaking frontend changes unless the response format becomes strictly better and the frontend is updated in the same PR.
- Use environment variables for configurable behavior.
- Add concise docstrings where useful.
- Handle failures gracefully with actionable error messages.
- Keep local-first storage; do not introduce external databases unless optional.
- Do not add authentication in this iteration.
- Do not add features that require paid third-party services beyond the existing OpenAI dependency.

---

## 5) Feature implementation requirements

### Phase A — Refactor and stabilize
#### A1. Backend modularization
Refactor the current flat backend into modular route, service, and RAG layers.

Requirements:
- Split `routes.py` into route modules.
- Extract business logic from route handlers into service modules.
- Centralize configuration in `core/config.py`.
- Add shared schema definitions in `models/schemas.py`.
- Ensure `backend/app.py` remains the entry point.

Acceptance:
- Existing upload, query, history, and clear-history workflows still work.
- Imports are clean and circular dependencies are avoided.

#### A2. Config and environment
Add environment-driven config for:
- OpenAI chat model
- OpenAI embedding model
- chunk size / overlap
- top_k retrieval
- hybrid retrieval weights
- reranking on/off
- query rewriting on/off
- logging level

Add `.env.example` with safe placeholders.

---

### Phase B — Ingestion and metadata upgrade
#### B1. Page-aware parsing
Upgrade PDF ingestion so the parser extracts page-by-page content instead of flattening everything into one string.

Requirements:
- Keep page numbers.
- Preserve per-page text blocks.
- Maintain TXT file support.
- Store processed intermediate representation under `data/processed/` when useful.

#### B2. Structure-aware chunking
Replace the current simple word-window chunker with structure-aware chunking.

Rules:
- Prefer splitting by headings, paragraphs, or natural text blocks.
- Fall back to max-length chunking when blocks are too large.
- Preserve overlap only where helpful.
- Avoid tiny/noisy chunks.
- Return chunk text plus metadata.

#### B3. Rich metadata
Each chunk must carry metadata like:

```json
{
  "document_id": "doc_001",
  "filename": "lecture_3.pdf",
  "stored_filename": "uuid_lecture_3.pdf",
  "chunk_id": 17,
  "page_start": 7,
  "page_end": 8,
  "section_title": "Transformer Architecture",
  "chunk_text": "...",
  "token_count": 312,
  "source_type": "pdf",
  "tags": []
}
```

#### B4. Document registry
Implement a lightweight document registry using JSON or SQLite.

Each document entry should include:
- document_id
- original filename
- stored filename
- upload timestamp
- source type
- chunk count
- status
- optional tags

Also add helper methods to:
- list indexed documents
- fetch document metadata
- delete a document’s registry entry and related index data if supported

---

### Phase C — Retrieval upgrade
#### C1. Dense retriever
Preserve FAISS-based dense retrieval, but move it into a dedicated module with a clean interface.

#### C2. Sparse retriever
Add BM25 lexical retrieval over chunk text.

Requirements:
- persist sparse index artifacts locally
- support rebuilds
- expose a consistent retrieval interface

#### C3. Hybrid retrieval
Create a hybrid retriever that:
- calls both dense and sparse retrievers
- merges results using weighted reciprocal rank fusion or another defensible rank-fusion method
- returns provenance fields indicating whether a chunk matched dense, sparse, or both

Configurable settings:
- dense candidate count
- sparse candidate count
- final pre-rerank candidate count
- fusion weights

#### C4. Deduplication
Add a dedupe pass before generation.

Requirements:
- remove exact duplicates
- collapse highly overlapping adjacent chunks when appropriate
- preserve the strongest-scoring instance

---

### Phase D — Reranking
#### D1. Reranker module
Add an optional reranking layer.

Preferred behavior:
- retrieve top 12–20 candidates from hybrid retrieval
- rerank them to top 4–6 chunks for generation

Implementation order:
1. simple LLM-based relevance scoring is acceptable if cross-encoder setup is too heavy
2. design the module so a cross-encoder can be swapped in later

Requirements:
- store both retrieval score and rerank score
- fail open: if reranking errors, fall back to hybrid ranking
- controlled by env var

---

### Phase E — Query rewriting and conversational retrieval
#### E1. Query rewriting
Add a pre-retrieval query rewriting step.

Purpose:
- turn follow-up questions into standalone search-friendly queries
- use recent conversation context when needed

Requirements:
- keep original user query for generation and UI
- use rewritten query for retrieval
- log original and rewritten query internally
- if rewrite fails, use original query
- make optional via env var

#### E2. Query classification
Add a lightweight check for whether rewriting is needed.

Examples:
- "What about the next chapter?"
- "Explain that again"
- "How does this compare with RNN?"

---

### Phase F — Answer generation and citations
#### F1. Context compression
Before final generation, compress or filter retrieved evidence to reduce noise.

Requirements:
- preserve only answer-relevant spans
- avoid passing too many redundant chunks to the model

#### F2. Citation builder
Add evidence-linked answering.

Answer requirements:
- final answer should cite only chunks actually used in generation
- citation format should be compact and readable, e.g. `[lecture3.pdf p.7]`
- if page is unavailable, fall back to filename + chunk id

#### F3. Structured sources in API response
Return structured evidence cards, for example:

```json
{
  "answer": "... [lecture3.pdf p.7]",
  "sources": [
    {
      "document_id": "doc_001",
      "filename": "lecture3.pdf",
      "page_label": "p.7",
      "section_title": "Transformer Architecture",
      "excerpt": "Self-attention allows...",
      "retrieval_score": 0.88,
      "rerank_score": 0.94,
      "match_origin": ["dense", "sparse"]
    }
  ]
}
```

#### F4. Prompt updates
Prompts must instruct the model to:
- answer only from evidence
- say “I don’t know” when unsupported
- avoid inventing citations
- keep answers concise unless the user asks for detail

---

### Phase G — Document management and frontend improvements
#### G1. Document management endpoints
Add routes to:
- list indexed documents
- optionally delete a document
- optionally rebuild indexes

#### G2. Frontend upgrades
Update the frontend to support:
- rendering evidence cards under each answer
- showing page/section info
- optionally listing indexed documents
- preserving the current simple UX

Keep the frontend lightweight.

---

### Phase H — Evaluation framework
#### H1. Benchmark dataset
Create `data/eval/golden_set.json` with a starter set of benchmark examples.

Each item should support fields like:

```json
{
  "question": "What is self-attention used for?",
  "expected_answer": "...",
  "expected_documents": ["lecture3.pdf"],
  "expected_pages": [7]
}
```

Add a reasonable starter size.

#### H2. Retrieval evaluation
Implement metrics such as:
- hit@k
- recall@k
- MRR

#### H3. Answer evaluation
Implement lightweight answer quality checks such as:
- citation correctness
- unsupported answer rate
- correct `I don't know` rate

Heuristic evaluation is acceptable for this iteration.

#### H4. CLI runner
Add `scripts/run_eval.py` and evaluation modules so the benchmark can be run locally and results written to JSON.

---

### Phase I — README and developer experience
Rewrite README to include:
- project overview
- architecture diagram in markdown/text form
- feature list
- setup instructions
- API endpoints
- retrieval pipeline explanation
- evaluation section
- screenshots placeholders
- roadmap
- design tradeoffs

Also ensure:
- `requirements.txt` is updated
- `.env.example` exists
- docs files are created if referenced

---

## 6) API compatibility expectations
Preserve existing routes if possible:
- `POST /api/upload`
- `POST /api/query`
- `GET /api/history`
- `POST /api/history/clear`

Add new routes as needed, e.g.:
- `GET /api/documents`
- `DELETE /api/documents/{document_id}`
- `POST /api/eval/run`

Do not rename existing routes unless there is a compelling reason and all references are updated.

---

## 7) Coding standards
- Use type hints on public functions and major internal helpers.
- Keep function responsibilities narrow.
- Prefer composition over oversized utility files.
- Avoid magic constants; use config.
- Add tests for new logic.
- Keep comments concise and useful.

---

## 8) Implementation order
Codex should implement in this order:

1. Refactor backend structure without changing behavior
2. Add config module and `.env.example`
3. Upgrade parser and chunking
4. Add metadata and document registry
5. Add dense retriever abstraction
6. Add BM25 sparse retriever
7. Add hybrid retrieval
8. Add dedupe
9. Add reranker
10. Add query rewriting
11. Add context compression
12. Add citations and structured sources
13. Add document management routes
14. Add evaluation framework
15. Update frontend
16. Rewrite README and docs
17. Add/adjust tests

---

## 9) Acceptance criteria
The work is complete when all of the following are true:

### Functional
- Existing upload/query/history flows still work
- PDF/TXT documents can be ingested
- uploaded content is chunked with richer metadata
- hybrid retrieval works
- reranking can be toggled on/off
- answers include real citations to retrieved evidence
- document listing works
- evaluation script runs

### Engineering
- backend is modularized
- config is centralized
- code is typed where practical
- tests exist for chunking, retrieval, citations, and API basics
- README accurately reflects the implementation

### UX
- frontend still feels simple
- answer responses display evidence cards cleanly
- citations are understandable

---

## 10) Explicit constraints
- Do not rewrite the project into LangChain/LlamaIndex unless there is a strong reason. Prefer direct, readable implementation.
- Do not add a heavyweight database unless optional.
- Do not break the local development workflow.
- Do not remove the "I don't know" fallback behavior.
- Do not invent benchmark claims in the README; only document results that can actually be produced by the new evaluation pipeline.

---

## 11) Deliverables expected from Codex
At the end of implementation, provide:
1. updated project files
2. a concise summary of changes
3. a list of new environment variables
4. instructions to run locally
5. instructions to run evaluation
6. any migration notes for existing vector store/index files

---

## 12) Nice-to-have enhancements if time permits
Only after the main scope is complete:
- basic OCR fallback for scanned PDFs
- source tags / course tags
- streaming responses
- better frontend upload/document management UX
- benchmark report export in markdown

---

## 13) Final instruction to Codex
Implement the upgrade incrementally and safely. Optimize for maintainability, clarity, and measurable RAG quality improvement. Preserve the project’s lightweight feel while making it substantially stronger in retrieval quality, trustworthiness, and portfolio value.

