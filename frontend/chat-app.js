const studyApp = (window.studyApp = window.studyApp || {});
const chatHistory = $("#chat-history");
const uploadStatus = $("#upload-status");
const loadingIndicator = $("#loading-indicator");

studyApp.escapeHtml = function escapeHtml(text) {
  return $("<div>").text(text ?? "").html();
};

function renderSources(sources = []) {
  if (!sources.length) {
    return "";
  }

  return `<div class="sources mt-3">${sources
    .map(
      (source) => `
        <article class="source-card">
          <div class="source-card-head">
            <strong>${studyApp.escapeHtml(source.citation_label || source.filename)}</strong>
            <span>${studyApp.escapeHtml(
              source.page_label || `chunk ${source.chunk_id}`
            )}</span>
          </div>
          <div class="source-card-meta">
            <span>${studyApp.escapeHtml(source.section_title || "General")}</span>
            <span>score ${studyApp.escapeHtml(String(source.rerank_score ?? source.retrieval_score ?? ""))}</span>
            <span>${studyApp.escapeHtml((source.match_origin || []).join(" + "))}</span>
          </div>
          <div class="source-card-body">${studyApp.escapeHtml(source.excerpt || "").replace(/\n/g, "<br>")}</div>
        </article>
      `
    )
    .join("")}</div>`;
}

studyApp.renderMessage = function renderMessage(role, content, sources = []) {
  chatHistory.append(`
    <article class="message ${role}">
      <div class="message-label">${role === "user" ? "You" : "Assistant"}</div>
      <div class="message-body">${studyApp.escapeHtml(content).replace(/\n/g, "<br>")}</div>
      ${renderSources(sources)}
    </article>
  `);
  chatHistory.scrollTop(chatHistory[0].scrollHeight);
};

studyApp.setStatus = function setStatus(message, isError = false) {
  uploadStatus
    .toggleClass("error", isError)
    .html(studyApp.escapeHtml(message));
};

studyApp.loadHistory = function loadHistory() {
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
        studyApp.renderMessage("user", entry.question);
        studyApp.renderMessage("assistant", entry.answer, entry.sources || []);
      });
    })
    .fail(() => {
      chatHistory.html(`
        <div class="empty-state">
          Unable to load chat history right now.
        </div>
      `);
    });
};

$("#query-form").on("submit", function (event) {
  event.preventDefault();
  const question = $("#question-input").val().trim();
  if (!question) {
    return;
  }

  $(".empty-state").remove();
  studyApp.renderMessage("user", question);
  $("#question-input").val("");
  loadingIndicator.removeClass("d-none");

  $.ajax({
    url: "/api/query",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({ question }),
  })
    .done((response) => {
      studyApp.renderMessage("assistant", response.answer, response.sources || []);
    })
    .fail((xhr) => {
      studyApp.renderMessage(
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
      studyApp.loadHistory();
    })
    .fail(() => {
      studyApp.setStatus("Unable to clear history right now.", true);
    });
});

$(document).ready(studyApp.loadHistory);
