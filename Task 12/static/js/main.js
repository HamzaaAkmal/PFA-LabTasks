const chat = document.getElementById("chat");
const qInput = document.getElementById("q");
const sendBtn = document.getElementById("send");
const matchesBox = document.getElementById("matches");

function addMsg(text, who) {
  const d = document.createElement("div");
  d.className = `msg ${who}`;
  d.textContent = text;
  chat.appendChild(d);
  chat.scrollTop = chat.scrollHeight;
}

function showMatches(matches) {
  if (!matches || matches.length === 0) {
    matchesBox.textContent = "No similar matches found.";
    return;
  }

  const lines = matches.map((m, i) => {
    const score = (m.score * 100).toFixed(2);
    return `${i + 1}. ${m.question} (score: ${score}%)`;
  });

  matchesBox.textContent = "Top similar matches:\n" + lines.join("\n");
}

async function askBot() {
  const q = qInput.value.trim();
  if (!q) return;

  addMsg(q, "user");
  qInput.value = "";

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q }),
    });

    const data = await res.json();
    addMsg(data.reply || "No answer", "bot");
    showMatches(data.matches || []);
  } catch (e) {
    addMsg("Server issue, please try again.", "bot");
  }
}

sendBtn.addEventListener("click", askBot);
qInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    askBot();
  }
});
