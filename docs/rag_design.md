# RAG Design

1. Documents are uploaded into `data/uploads/`.
2. The parser extracts page-aware PDF text or TXT blocks.
3. Structure-aware chunking creates metadata-rich chunks with page, section, and token counts.
4. Chunks are embedded into FAISS and also stored in a local BM25 index.
5. Queries optionally get rewritten when they look conversational.
6. Hybrid retrieval fuses dense and sparse rankings with reciprocal rank fusion.
7. A dedupe pass removes redundant chunks.
8. Optional reranking can reorder the final evidence set.
9. Context compression keeps only the most question-relevant spans.
10. The answer generator responds only from evidence and returns citation ids.
11. Citation building turns those ids into readable labels and structured source cards.
