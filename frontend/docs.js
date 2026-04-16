const studyDocs = (window.studyApp = window.studyApp || {});
const documentsList = $("#documents-list");

function renderDocuments(documents) {
  if (!documents.length) {
    documentsList.html(`
      <div class="empty-state small">
        No indexed documents yet.
      </div>
    `);
    return;
  }

  documentsList.html(
    documents
      .map(
        (doc) => `
          <article class="document-card">
            <div class="document-card-head">
              <div>
                <div class="document-title">${studyDocs.escapeHtml(doc.original_filename)}</div>
                <div class="document-meta">
                  <span>${studyDocs.escapeHtml(doc.source_type.toUpperCase())}</span>
                  <span>${studyDocs.escapeHtml(String(doc.chunk_count))} chunks</span>
                </div>
              </div>
              <button class="btn btn-sm btn-outline-light delete-document" data-document-id="${studyDocs.escapeHtml(
                doc.document_id
              )}">
                Delete
              </button>
            </div>
          </article>
        `
      )
      .join("")
  );
}

studyDocs.loadDocuments = function loadDocuments() {
  $.get("/api/documents")
    .done((response) => {
      renderDocuments(response.documents || []);
    })
    .fail(() => {
      documentsList.html(`
        <div class="empty-state small">
          Unable to load indexed documents.
        </div>
      `);
    });
};

$(document).on("click", ".delete-document", function () {
  const documentId = $(this).data("document-id");
  $.ajax({
    url: `/api/documents/${documentId}`,
    method: "DELETE",
  })
    .done(() => {
      studyDocs.loadDocuments();
      studyDocs.setStatus("Document deleted.");
    })
    .fail((xhr) => {
      studyDocs.setStatus(
        xhr.responseJSON?.detail || "Unable to delete document right now.",
        true
      );
    });
});

$("#rebuild-indexes").on("click", function () {
  studyDocs.setStatus("Rebuilding indexes...");
  $.post("/api/documents/rebuild")
    .done((response) => {
      studyDocs.setStatus(
        `Rebuilt indexes for ${response.indexed_documents} processed documents.`
      );
      studyDocs.loadDocuments();
    })
    .fail((xhr) => {
      studyDocs.setStatus(
        xhr.responseJSON?.detail || "Unable to rebuild indexes right now.",
        true
      );
    });
});

$(document).ready(studyDocs.loadDocuments);
