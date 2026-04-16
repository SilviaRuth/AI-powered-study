const studyApp = (window.studyApp = window.studyApp || {});

$("#upload-form").on("submit", function (event) {
  event.preventDefault();
  const fileInput = $("#document-input")[0];
  if (!fileInput.files.length) {
    studyApp.setStatus("Choose a PDF or TXT file first.", true);
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  studyApp.setStatus("Uploading and indexing document...");

  $.ajax({
    url: "/api/upload",
    method: "POST",
    data: formData,
    processData: false,
    contentType: false,
  })
    .done((response) => {
      studyApp.setStatus(
        `${response.filename} indexed successfully with ${response.chunks_indexed} chunks.`
      );
      fileInput.value = "";
      if (typeof studyApp.loadDocuments === "function") {
        studyApp.loadDocuments();
      }
    })
    .fail((xhr) => {
      studyApp.setStatus(xhr.responseJSON?.detail || "Upload failed.", true);
    });
});
