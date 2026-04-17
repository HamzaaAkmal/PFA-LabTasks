const chatBox = document.getElementById("chat-box");
const msgInput = document.getElementById("user-msg");
const sendBtn = document.getElementById("send-btn");

function addMsg(text, who) {
  const div = document.createElement("div");
  div.className = `msg ${who}`;
  div.textContent = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMsg() {
  const text = msgInput.value.trim();
  if (!text) return;

  addMsg(text, "user");
  msgInput.value = "";

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    const data = await res.json();
    addMsg(data.reply || "No reply", "bot");
  } catch (e) {
    addMsg("Server error, please try agian.", "bot");
  }
}

sendBtn.addEventListener("click", sendMsg);
msgInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    sendMsg();
  }
});
