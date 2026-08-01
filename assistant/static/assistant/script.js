/* Coach Spark - script.js */
document.addEventListener("DOMContentLoaded", () => {

  const employeeCard   = document.getElementById("employee-card");
  const employeeSelect = document.getElementById("employee-select");
  const startBtn       = document.getElementById("start-btn");
  const endBtn         = document.getElementById("end-btn");

  const chatSection    = document.getElementById("chat-section");
  const chatEmployee    = document.getElementById("chat-employee-name");
  const chatBox         = document.getElementById("chat-box");
  const chatForm        = document.getElementById("chat-form");
  const messageInput     = document.getElementById("message-input");
  const sendBtn          = document.getElementById("send-btn");

  let employeeId = "";

  const escapeHtml = (value) =>
    String(value).replace(/[&<>"]/g, (char) => (
      { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[char]
    ));

  const SECTION_EMOJI = {
    Safety: "🦺",
    Maintenance: "🛠️",
    Quality: "🔍",
    Warehouse: "📦",
    Learning: "📘",
    Leadership: "🌟",
    General: "📄",
  };

  const scrollToBottom = () => {
    // Run after paint so newly-added content (including chips that
    // animate in) is measured correctly before we scroll to it.
    requestAnimationFrame(() => {
      chatBox.scrollTop = chatBox.scrollHeight;
    });
  };

  function appendMessage(kind, label, text) {
    const bubble = document.createElement("div");
    bubble.className = `message ${kind}`;
    bubble.innerHTML = `
      <span class="message-label">${escapeHtml(label)}</span>
      <p>${escapeHtml(text)}</p>
    `;
    chatBox.appendChild(bubble);
    scrollToBottom();
    return bubble;
  }

  function appendMetaBlock(bubble, section, sources, recommendations) {
    let html = "";

    if (section) {
      const emoji = SECTION_EMOJI[section] || "📄";
      html += `
        <div class="meta-block">
          <div class="meta-title">🗂️ Section</div>
          <span class="chip section">${emoji} ${escapeHtml(section)}</span>
        </div>`;
    }

    if (sources && sources.length) {
      html += `
        <div class="meta-block">
          <div class="meta-title">📚 Sources</div>
          ${sources.map((s) => `<span class="chip source">📘 ${escapeHtml(s)}</span>`).join("")}
        </div>`;
    }

    if (recommendations && recommendations.length) {
      html += `
        <div class="meta-block">
          <div class="meta-title">🚀 Recommended Next Training</div>
          ${recommendations.map((r) => `<span class="chip reco">🎯 ${escapeHtml(r)}</span>`).join("")}
        </div>`;
    }

    if (html) {
      bubble.insertAdjacentHTML("beforeend", html);
      scrollToBottom();
    }
  }

  function setBusy(isBusy) {
    sendBtn.disabled = isBusy;
    messageInput.disabled = isBusy;

    let loadingBubble = document.getElementById("loading-bubble");

    if (isBusy) {
      if (loadingBubble) return;
      loadingBubble = document.createElement("div");
      loadingBubble.id = "loading-bubble";
      loadingBubble.className = "message bot loading";
      loadingBubble.innerHTML = `
        <span class="message-label">Coach Spark</span>
        <p>🔎 Searching training manuals <span class="typing-dots"><span>.</span><span>.</span><span>.</span></span></p>
      `;
      chatBox.appendChild(loadingBubble);
    } else if (loadingBubble) {
      loadingBubble.remove();
      messageInput.focus();
    }

    scrollToBottom();
  }

  function startSession() {
    employeeId = employeeSelect.value;
    if (!employeeId) {
      alert("Please select an employee.");
      return;
    }

    const employeeLabel = employeeSelect.options[employeeSelect.selectedIndex].text;
    chatEmployee.textContent = employeeLabel;

    employeeCard.classList.add("hidden");
    chatSection.classList.remove("hidden");
    messageInput.focus();
  }

  function endSession() {
    employeeId = "";
    chatBox.innerHTML = `
      <div class="message bot">
        <span class="message-label">Coach Spark</span>
        <p>Hello! Ask me about safety, PPE, maintenance, machine operation, quality, or training. I'll answer using our manuals only.</p>
      </div>
    `;
    chatSection.classList.add("hidden");
    employeeCard.classList.remove("hidden");
  }

  async function sendMessage(event) {
    event.preventDefault();

    const question = messageInput.value.trim();
    if (!question) return;

    appendMessage("user", "You", question);
    messageInput.value = "";
    setBusy(true);

    try {
      const response = await fetch("/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ employee_id: employeeId, message: question }),
      });

      const data = await response.json();
      setBusy(false);

      if (!response.ok || data.error) {
        appendMessage("bot", "Coach Spark", data.error || "Request failed. Please try again.");
        return;
      }

      const bubble = appendMessage("bot", "Coach Spark", data.response || "No response received.");
      appendMetaBlock(bubble, data.section, data.sources, data.recommendations);
      scrollToBottom();

    } catch (error) {
      console.error(error);
      setBusy(false);
      appendMessage("bot", "Coach Spark", "Unable to connect to the server. Please try again.");
    }
  }

  startBtn?.addEventListener("click", startSession);
  endBtn?.addEventListener("click", endSession);
  chatForm?.addEventListener("submit", sendMessage);
});