const chatHistory = $("#chat-history");
const uploadStatus = $("#upload-status");
const loadingIndicator = $("#loading-indicator");

function escapeHtml(text) {
  return $("<div>").text(text ?? "").html();
}

function renderMessage(role, content, sources = []) {
  const sourceMarkup = sources.length
    ? `<div class="sources mt-2">${sources
        .map(
          (source) => `
            <div class="source-chip">
              <strong>${escapeHtml(source.filename)}</strong>
              <span>chunk ${source.chunk_id}</span>
              <span>score ${escapeHtml(String(source.score))}</span>
            </div>
          `
        )
        .join("")}</div>`
    : "";

  chatHistory.append(`
    <article class="message ${role}">
      <div class="message-label">${role === "user" ? "You" : "Assistant"}</div>
      <div class="message-body">${escapeHtml(content).replace(/\n/g, "<br>")}</div>
      ${sourceMarkup}
    </article>
  `);
  chatHistory.scrollTop(chatHistory[0].scrollHeight);
}

function setStatus(message, isError = false) {
  uploadStatus
    .toggleClass("error", isError)
    .html(escapeHtml(message));
}

function loadHistory() {
  $.get("/api/history")
    .done((response) => {
      chatHistory.empty();
      if (!response.history.length) {
        chatHistory.append(`
          <div class="empty-state">
            Upload a document to start asking grounded questions.
          </div>
        `);
        return;
      }

      response.history.forEach((entry) => {
        renderMessage("user", entry.question);
        renderMessage("assistant", entry.answer, entry.sources || []);
      });
    })
    .fail(() => {
      chatHistory.html(`
        <div class="empty-state">
          Unable to load chat history right now.
        </div>
      `);
    });
}

$("#upload-form").on("submit", function (event) {
  event.preventDefault();
  const fileInput = $("#document-input")[0];
  if (!fileInput.files.length) {
    setStatus("Choose a PDF or TXT file first.", true);
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  setStatus("Uploading and indexing document...");

  $.ajax({
    url: "/api/upload",
    method: "POST",
    data: formData,
    processData: false,
    contentType: false,
  })
    .done((response) => {
      setStatus(
        `${response.filename} indexed successfully with ${response.chunks_indexed} chunks.`
      );
      fileInput.value = "";
    })
    .fail((xhr) => {
      setStatus(xhr.responseJSON?.detail || "Upload failed.", true);
    });
});

$("#query-form").on("submit", function (event) {
  event.preventDefault();
  const question = $("#question-input").val().trim();
  if (!question) {
    return;
  }

  $(".empty-state").remove();
  renderMessage("user", question);
  $("#question-input").val("");
  loadingIndicator.removeClass("d-none");

  $.ajax({
    url: "/api/query",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({ question }),
  })
    .done((response) => {
      renderMessage("assistant", response.answer, response.sources || []);
    })
    .fail((xhr) => {
      renderMessage(
        "assistant",
        xhr.responseJSON?.detail || "Something went wrong while answering."
      );
    })
    .always(() => {
      loadingIndicator.addClass("d-none");
    });
});

$("#clear-history").on("click", function () {
  $.post("/api/history/clear")
    .done(() => {
      loadHistory();
    })
    .fail(() => {
      setStatus("Unable to clear history right now.", true);
    });
});

$(document).ready(loadHistory);
