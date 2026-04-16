from backend.rag.chunking import chunk_document
from backend.rag.metadata import ParsedBlock, ParsedDocument, ParsedPage


def test_structure_aware_chunking_preserves_section_and_pages() -> None:
    document = ParsedDocument(
        document_id="doc_001",
        filename="lecture.pdf",
        stored_filename="stored_lecture.pdf",
        source_type="pdf",
        pages=[
            ParsedPage(
                page_number=7,
                text="Transformer Architecture",
                blocks=[
                    ParsedBlock(text="Transformer Architecture", block_type="heading", page_number=7),
                    ParsedBlock(
                        text="Self-attention allows each token to attend to the rest of the sequence and capture long-range dependencies.",
                        block_type="paragraph",
                        page_number=7,
                    ),
                    ParsedBlock(
                        text="Multi-head attention learns several relationships in parallel by projecting tokens into multiple subspaces.",
                        block_type="paragraph",
                        page_number=8,
                    ),
                ],
            )
        ],
    )

    chunks = chunk_document(document)

    assert chunks
    assert chunks[0].section_title == "Transformer Architecture"
    assert chunks[0].page_start == 7
    assert chunks[0].page_end == 8
    assert "Self-attention" in chunks[0].chunk_text
