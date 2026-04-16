from backend.rag.metadata import RetrievedChunk
from backend.rag.retrieval.dedupe import dedupe_candidates
from backend.rag.retrieval.hybrid_retriever import HybridRetriever


class _FakeRetriever:
    def __init__(self, items):
        self.items = items

    def search(self, query: str, top_k: int):
        return self.items[:top_k]


def _chunk(document_id: str, chunk_id: int, text: str, origin: str, score: float) -> RetrievedChunk:
    payload = dict(
        document_id=document_id,
        filename="lecture.txt",
        stored_filename="stored.txt",
        chunk_id=chunk_id,
        page_start=None,
        page_end=None,
        section_title="Overview",
        chunk_text=text,
        token_count=len(text.split()),
        source_type="txt",
        tags=[],
        retrieval_score=score,
        rerank_score=None,
        dense_score=score if origin == "dense" else None,
        sparse_score=score if origin == "sparse" else None,
        match_origin=[origin],
    )
    return RetrievedChunk(**payload)


def test_hybrid_retriever_fuses_dense_and_sparse_matches() -> None:
    dense = _FakeRetriever(
        [
            _chunk("doc_1", 0, "self attention overview", "dense", 0.9),
            _chunk("doc_2", 0, "rnn overview", "dense", 0.8),
        ]
    )
    sparse = _FakeRetriever(
        [
            _chunk("doc_1", 0, "self attention overview", "sparse", 5.0),
            _chunk("doc_3", 0, "study skills overview", "sparse", 4.0),
        ]
    )

    results = HybridRetriever(dense, sparse).search("self attention")

    assert results[0].document_id == "doc_1"
    assert set(results[0].match_origin) == {"dense", "sparse"}


def test_dedupe_candidates_removes_exact_duplicates() -> None:
    first = _chunk("doc_1", 0, "same evidence chunk", "dense", 0.9)
    second = _chunk("doc_1", 1, "same evidence chunk", "sparse", 0.8)

    deduped = dedupe_candidates([first, second])

    assert len(deduped) == 1
