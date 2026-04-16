from backend.rag.generation.citation_builder import CitationBuilder
from backend.rag.metadata import RetrievedChunk


def _candidate() -> RetrievedChunk:
    return RetrievedChunk(
        document_id="doc_001",
        filename="lecture3.pdf",
        stored_filename="stored_lecture3.pdf",
        chunk_id=17,
        page_start=7,
        page_end=7,
        section_title="Transformer Architecture",
        chunk_text="Self-attention allows tokens to attend to each other.",
        token_count=8,
        source_type="pdf",
        tags=[],
        retrieval_score=0.88,
        rerank_score=0.94,
        dense_score=0.88,
        sparse_score=4.0,
        match_origin=["dense", "sparse"],
    )


def test_citation_builder_formats_answer_and_sources() -> None:
    builder = CitationBuilder()
    candidates = builder.assign_labels([_candidate()])

    answer = builder.build_answer("Self-attention links tokens across a sequence.", ["S1"], candidates)
    sources = builder.build_sources(["S1"], candidates)

    assert "[lecture3.pdf p.7]" in answer
    assert sources[0]["page_label"] == "p.7"
    assert sources[0]["section_title"] == "Transformer Architecture"
