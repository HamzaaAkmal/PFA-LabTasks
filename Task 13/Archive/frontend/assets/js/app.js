const els = {
  uploadForm: document.getElementById("uploadForm"),
  uploadStatus: document.getElementById("uploadStatus"),
  askForm: document.getElementById("askForm"),
  answerBox: document.getElementById("answerBox"),
  contexts: document.getElementById("contexts"),
  examForm: document.getElementById("examForm"),
  examOutput: document.getElementById("examOutput"),
  stats: document.getElementById("stats"),
  healthBadge: document.getElementById("healthBadge"),
  contextCardTemplate: document.getElementById("contextCardTemplate"),
};

function setStatus(node, text, ok = true) {
  node.textContent = text;
  node.classList.remove("ok", "err");
  node.classList.add(ok ? "ok" : "err");
}

function renderStats(stats) {
  const entries = Object.entries(stats || {});
  if (!entries.length) {
    els.stats.innerHTML = "<p>No index stats available yet.</p>";
    return;
  }

  els.stats.innerHTML = entries
    .map(([key, value]) => {
      const val = Array.isArray(value) ? value.join(", ") || "none" : String(value);
      return `
        <div class="stat-item">
          <div class="stat-key">${key}</div>
          <div class="stat-value">${val}</div>
        </div>
      `;
    })
    .join("");
}

async function checkHealth() {
  if (!els.healthBadge) {
    return;
  }

  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    els.healthBadge.textContent = `Local engine ready: ${data.local_models.embedding}`;
    els.healthBadge.classList.add("ok");
  } catch (err) {
    els.healthBadge.textContent = "Local engine check failed. Start Flask backend.";
    els.healthBadge.classList.add("err");
  }
}

async function loadStats() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();
    renderStats(data);
  } catch (err) {
    els.stats.innerHTML = "<p>Unable to load stats.</p>";
  }
}

els.uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const fileInput = document.getElementById("files");
  const files = fileInput.files;

  if (!files.length) {
    setStatus(els.uploadStatus, "Select at least one file.", false);
    return;
  }

  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }

  setStatus(els.uploadStatus, "Indexing documents...", true);

  try {
    const res = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Upload failed.");
    }

    setStatus(
      els.uploadStatus,
      `Indexed ${data.uploaded.length} file(s), ${data.chunks_added} chunks added.`,
      true
    );
    renderStats(data.stats);
    fileInput.value = "";
  } catch (err) {
    setStatus(els.uploadStatus, err.message, false);
  }
});

els.askForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = document.getElementById("question").value.trim();
  const topK = Number(document.getElementById("topK").value) || 5;

  if (!question) {
    els.answerBox.innerHTML = '<p class="answer-err">Question is required.</p>';
    return;
  }

  els.answerBox.innerHTML = '<p>Retrieving answer...</p>';
  els.contexts.innerHTML = "";

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, top_k: topK }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || "Unable to fetch answer.");
    }

    els.answerBox.innerHTML = `<p class="answer-ok">${data.answer}</p>`;

    if (!data.contexts || !data.contexts.length) {
      els.contexts.innerHTML = "<p>No retrieved contexts.</p>";
      return;
    }

    const cards = data.contexts.map((ctx) => {
      const fragment = els.contextCardTemplate.content.cloneNode(true);
      fragment.querySelector(".context-meta").textContent = `${ctx.file_name} | score: ${ctx.score}`;
      fragment.querySelector(".context-text").textContent = ctx.text;
      return fragment;
    });

    cards.forEach((card) => els.contexts.appendChild(card));
  } catch (err) {
    els.answerBox.innerHTML = `<p class="answer-err">${err.message}</p>`;
  }
});

els.examForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const topic = document.getElementById("topic").value.trim();
  const numQuestions = Number(document.getElementById("numQuestions").value) || 6;

  els.examOutput.innerHTML = "<p>Generating exam set...</p>";

  try {
    const res = await fetch("/api/generate-exam", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, num_questions: numQuestions }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || "Exam generation failed.");
    }

    if (!data.questions.length) {
      els.examOutput.innerHTML = "<p>No questions could be generated.</p>";
      return;
    }

    els.examOutput.innerHTML = data.questions
      .map((item, idx) => {
        const optionsHtml = item.options
          ? `<ul class="exam-options">${item.options.map((opt) => `<li>${opt}</li>`).join("")}</ul>`
          : "";

        const answerHint = item.correct_answer
          ? `Correct answer: ${item.correct_answer}. ${item.answer_guide || ""}`
          : item.answer_guide || "";

        return `
          <article class="exam-card">
            <div class="exam-meta">Q${idx + 1} | ${item.type}</div>
            <p class="exam-q">${item.question}</p>
            ${optionsHtml}
            <div class="exam-guide">${answerHint}</div>
          </article>
        `;
      })
      .join("");
  } catch (err) {
    els.examOutput.innerHTML = `<p class="answer-err">${err.message}</p>`;
  }
});

checkHealth();
loadStats();
