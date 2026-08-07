// /* Coach Spark - script.js */
// document.addEventListener("DOMContentLoaded", () => {

//   const employeeCard   = document.getElementById("employee-card");
//   const employeeSelect = document.getElementById("employee-select");
//   const startBtn       = document.getElementById("start-btn");
//   const endBtn         = document.getElementById("end-btn");

//   const chatSection    = document.getElementById("chat-section");
//   const chatEmployee    = document.getElementById("chat-employee-name");
//   const chatBox         = document.getElementById("chat-box");
//   const chatForm        = document.getElementById("chat-form");
//   const messageInput     = document.getElementById("message-input");
//   const sendBtn          = document.getElementById("send-btn");
//   const quizQuickBtn     = document.getElementById("quiz-quick-btn");

//   let employeeId = "";

//   const escapeHtml = (value) =>
//     String(value).replace(/[&<>"]/g, (char) => (
//       { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[char]
//     ));

//   const SECTION_EMOJI = {
//     Safety: "🦺",
//     "Machine Operation": "⚙️",
//     Maintenance: "🛠️",
//     Quality: "🔍",
//     Warehouse: "📦",
//     Learning: "📘",
//     Leadership: "🌟",
//     General: "📄",
//   };

//   const scrollToBottom = () => {
//     // Run after paint so newly-added content (including chips that
//     // animate in) is measured correctly before we scroll to it.
//     requestAnimationFrame(() => {
//       chatBox.scrollTop = chatBox.scrollHeight;
//     });
//   };

//   function appendMessage(kind, label, text) {
//     const bubble = document.createElement("div");
//     bubble.className = `message ${kind}`;
//     bubble.innerHTML = `
//       <span class="message-label">${escapeHtml(label)}</span>
//       <p>${escapeHtml(text)}</p>
//     `;
//     chatBox.appendChild(bubble);
//     scrollToBottom();
//     return bubble;
//   }

//   function appendMetaBlock(bubble, section, sources, recommendations) {
//     let html = "";

//     if (section) {
//       const emoji = SECTION_EMOJI[section] || "📄";
//       html += `
//         <div class="meta-block">
//           <div class="meta-title">🗂️ Section</div>
//           <span class="chip section">${emoji} ${escapeHtml(section)}</span>
//         </div>`;
//     }

//     if (sources && sources.length) {
//       html += `
//         <div class="meta-block">
//           <div class="meta-title">📚 Sources</div>
//           ${sources.map((s) => `<span class="chip source">📘 ${escapeHtml(s)}</span>`).join("")}
//         </div>`;
//     }

//     if (recommendations && recommendations.length) {
//       html += `
//         <div class="meta-block">
//           <div class="meta-title">🚀 Recommended Next Training</div>
//           ${recommendations.map((r) => `<span class="chip reco">🎯 ${escapeHtml(r)}</span>`).join("")}
//         </div>`;
//     }

//     if (html) {
//       bubble.insertAdjacentHTML("beforeend", html);
//       scrollToBottom();
//     }
//   }

//   function setBusy(isBusy) {
//     sendBtn.disabled = isBusy;
//     messageInput.disabled = isBusy;

//     let loadingBubble = document.getElementById("loading-bubble");

//     if (isBusy) {
//       if (loadingBubble) return;
//       loadingBubble = document.createElement("div");
//       loadingBubble.id = "loading-bubble";
//       loadingBubble.className = "message bot loading";
//       loadingBubble.innerHTML = `
//         <span class="message-label">Coach Spark</span>
//         <p>🔎 Searching training manuals <span class="typing-dots"><span>.</span><span>.</span><span>.</span></span></p>
//       `;
//       chatBox.appendChild(loadingBubble);
//     } else if (loadingBubble) {
//       loadingBubble.remove();
//       messageInput.focus();
//     }

//     scrollToBottom();
//   }

//   function startSession() {
//     employeeId = employeeSelect.value;
//     if (!employeeId) {
//       alert("Please select an employee.");
//       return;
//     }

//     const employeeLabel = employeeSelect.options[employeeSelect.selectedIndex].text;
//     chatEmployee.textContent = employeeLabel;

//     employeeCard.classList.add("hidden");
//     chatSection.classList.remove("hidden");
//     messageInput.focus();
//   }

//   function endSession() {
//     employeeId = "";
//     chatBox.innerHTML = `
//       <div class="message bot">
//         <span class="message-label">Coach Spark</span>
//         <p>Hello! Ask me about safety, PPE, maintenance, machine operation, quality, or training. I'll answer using our manuals only.</p>
//       </div>
//     `;
//     chatSection.classList.add("hidden");
//     employeeCard.classList.remove("hidden");
//   }

//   async function sendMessage(event) {
//     event.preventDefault();

//     const question = messageInput.value.trim();
//     if (!question) return;

//     appendMessage("user", "You", question);
//     messageInput.value = "";

//     if (/\bquiz\b/i.test(question)) {
//       await startQuiz(question);
//       messageInput.focus();
//       return;
//     }

//     setBusy(true);

//     try {
//       const response = await fetch("/chat/", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ employee_id: employeeId, message: question }),
//       });

//       const data = await response.json();
//       setBusy(false);

//       if (!response.ok || data.error) {
//         appendMessage("bot", "Coach Spark", data.error || "Request failed. Please try again.");
//         return;
//       }

//       const bubble = appendMessage("bot", "Coach Spark", data.response || "No response received.");
//       appendMetaBlock(bubble, data.section, data.sources, data.recommendations);
//       scrollToBottom();

//     } catch (error) {
//       console.error(error);
//       setBusy(false);
//       appendMessage("bot", "Coach Spark", "Unable to connect to the server. Please try again.");
//     }
//   }

//   // ==========================================
//   // Interactive Quiz
//   // ==========================================

//   async function startQuiz(topic) {
//     setBusy(true);

//     try {
//       const response = await fetch("/quiz/start/", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ topic }),
//       });

//       const data = await response.json();
//       setBusy(false);

//       if (!response.ok || data.error) {
//         appendMessage("bot", "Coach Spark", data.error || "Couldn't start the quiz. Please try again.");
//         return;
//       }

//       appendMessage(
//         "bot",
//         "Coach Spark",
//         `🎯 Let's test your knowledge on ${data.section}! ${data.total} questions — good luck.`
//       );
//       renderQuizQuestion(data.question);

//     } catch (error) {
//       console.error(error);
//       setBusy(false);
//       appendMessage("bot", "Coach Spark", "Unable to connect to the server. Please try again.");
//     }
//   }

//   function renderQuizQuestion(question) {
//     const card = document.createElement("div");
//     card.className = "message bot quiz-card";

//     const optionsHtml = Object.entries(question.options).map(([letter, text]) => `
//       <button class="quiz-option" data-letter="${letter}" type="button">
//         <span class="quiz-option-letter">${letter}</span>
//         <span class="quiz-option-text">${escapeHtml(text)}</span>
//       </button>
//     `).join("");

//     card.innerHTML = `
//       <span class="message-label">🎯 Question ${question.number} of ${question.total}</span>
//       <p class="quiz-question-text">${escapeHtml(question.question)}</p>
//       <div class="quiz-options">${optionsHtml}</div>
//     `;

//     chatBox.appendChild(card);
//     scrollToBottom();

//     const buttons = card.querySelectorAll(".quiz-option");
//     buttons.forEach((btn) => {
//       btn.addEventListener("click", () => submitQuizAnswer(btn.dataset.letter, card, buttons), { once: true });
//     });
//   }

//   async function submitQuizAnswer(selectedLetter, card, buttons) {
//     buttons.forEach((btn) => { btn.disabled = true; });
//     card.querySelector(`[data-letter="${selectedLetter}"]`)?.classList.add("selected");

//     try {
//       const response = await fetch("/quiz/answer/", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ selected: selectedLetter }),
//       });

//       const data = await response.json();

//       if (!response.ok || data.error) {
//         appendMessage("bot", "Coach Spark", data.error || "Something went wrong with the quiz.");
//         return;
//       }

//       buttons.forEach((btn) => {
//         if (btn.dataset.letter === data.correct_answer) {
//           btn.classList.add("correct");
//         } else if (btn.dataset.letter === selectedLetter && !data.correct) {
//           btn.classList.add("incorrect");
//         }
//       });

//       const feedback = document.createElement("div");
//       feedback.className = `quiz-feedback ${data.correct ? "correct" : "incorrect"}`;
//       feedback.innerHTML = `
//         <span class="quiz-feedback-label">${data.correct ? "✅ Correct!" : "❌ Not quite."}</span>
//         ${data.explanation ? `<p class="quiz-explanation">💡 ${escapeHtml(data.explanation)}</p>` : ""}
//         <span class="quiz-score">Score: ${data.score}/${data.total}</span>
//       `;
//       card.appendChild(feedback);
//       scrollToBottom();

//       if (data.finished) {
//         setTimeout(() => renderQuizSummary(data.score, data.total), 700);
//       } else {
//         setTimeout(() => renderQuizQuestion(data.next_question), 900);
//       }

//     } catch (error) {
//       console.error(error);
//       appendMessage("bot", "Coach Spark", "Unable to connect to the server. Please try again.");
//     }
//   }

//   function renderQuizSummary(score, total) {
//     const pct = score / total;
//     let emoji = "📖";
//     let note = "Keep practicing — review the manual and try again!";

//     if (pct === 1) {
//       emoji = "🏆";
//       note = "Perfect score! You know this material cold.";
//     } else if (pct >= 0.7) {
//       emoji = "🎉";
//       note = "Nice work — solid understanding!";
//     } else if (pct >= 0.4) {
//       emoji = "👍";
//       note = "Good effort — a bit more review will help.";
//     }

//     appendMessage("bot", "Coach Spark", `${emoji} Quiz complete! Final score: ${score}/${total}\n${note}`);
//   }

//   startBtn?.addEventListener("click", startSession);
//   endBtn?.addEventListener("click", endSession);
//   chatForm?.addEventListener("submit", sendMessage);
//   quizQuickBtn?.addEventListener("click", () => {
//     messageInput.value = "Quiz me on ";
//     messageInput.focus();
//   });
// });
























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
  const quizQuickBtn     = document.getElementById("quiz-quick-btn");
  const progressBtn      = document.getElementById("progress-btn");

  let employeeId = "";

  const escapeHtml = (value) =>
    String(value).replace(/[&<>"]/g, (char) => (
      { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[char]
    ));

  const SECTION_EMOJI = {
    Safety: "🦺",
    "Machine Operation": "⚙️",
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

    if (/\bquiz\b/i.test(question)) {
      await startQuiz(question);
      messageInput.focus();
      return;
    }

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

  // ==========================================
  // My Progress (persisted quiz history)
  // ==========================================

  async function loadProgress() {
    if (!employeeId) return;

    setBusy(true);

    try {
      const response = await fetch(`/quiz/history/?employee_id=${encodeURIComponent(employeeId)}`);
      const data = await response.json();
      setBusy(false);

      if (!response.ok || data.error) {
        appendMessage("bot", "Coach Spark", data.error || "Couldn't load your quiz history.");
        return;
      }

      if (!data.history || data.history.length === 0) {
        appendMessage(
          "bot", "Coach Spark",
          '📊 No quiz attempts yet. Try asking me to "quiz me on safety" to get started!'
        );
        return;
      }

      const lines = data.history.slice(0, 8).map((attempt) => {
        const emoji = SECTION_EMOJI[attempt.section] || "📄";
        const date = new Date(attempt.timestamp).toLocaleDateString();
        return `${emoji} ${attempt.section} — ${attempt.score}/${attempt.total}  (${date})`;
      });

      let text = `📊 Your Quiz History\n\n${lines.join("\n")}`;

      if (data.weak_sections && data.weak_sections.length) {
        text += `\n\n📌 Consider reviewing: ${data.weak_sections.join(", ")}`;
      }

      appendMessage("bot", "Coach Spark", text);

    } catch (error) {
      console.error(error);
      setBusy(false);
      appendMessage("bot", "Coach Spark", "Unable to connect to the server. Please try again.");
    }
  }

  // ==========================================
  // Interactive Quiz
  // ==========================================

  async function startQuiz(topic) {
    setBusy(true);

    try {
      const response = await fetch("/quiz/start/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, employee_id: employeeId }),
      });

      const data = await response.json();
      setBusy(false);

      if (!response.ok || data.error) {
        appendMessage("bot", "Coach Spark", data.error || "Couldn't start the quiz. Please try again.");
        return;
      }

      appendMessage(
        "bot",
        "Coach Spark",
        `🎯 Let's test your knowledge on ${data.section}! ${data.total} questions — good luck.`
      );
      renderQuizQuestion(data.question);

    } catch (error) {
      console.error(error);
      setBusy(false);
      appendMessage("bot", "Coach Spark", "Unable to connect to the server. Please try again.");
    }
  }

  function renderQuizQuestion(question) {
    const card = document.createElement("div");
    card.className = "message bot quiz-card";

    const optionsHtml = Object.entries(question.options).map(([letter, text]) => `
      <button class="quiz-option" data-letter="${letter}" type="button">
        <span class="quiz-option-letter">${letter}</span>
        <span class="quiz-option-text">${escapeHtml(text)}</span>
      </button>
    `).join("");

    card.innerHTML = `
      <span class="message-label">🎯 Question ${question.number} of ${question.total}</span>
      <p class="quiz-question-text">${escapeHtml(question.question)}</p>
      <div class="quiz-options">${optionsHtml}</div>
    `;

    chatBox.appendChild(card);
    scrollToBottom();

    const buttons = card.querySelectorAll(".quiz-option");
    buttons.forEach((btn) => {
      btn.addEventListener("click", () => submitQuizAnswer(btn.dataset.letter, card, buttons), { once: true });
    });
  }

  async function submitQuizAnswer(selectedLetter, card, buttons) {
    buttons.forEach((btn) => { btn.disabled = true; });
    card.querySelector(`[data-letter="${selectedLetter}"]`)?.classList.add("selected");

    try {
      const response = await fetch("/quiz/answer/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ selected: selectedLetter }),
      });

      const data = await response.json();

      if (!response.ok || data.error) {
        appendMessage("bot", "Coach Spark", data.error || "Something went wrong with the quiz.");
        return;
      }

      buttons.forEach((btn) => {
        if (btn.dataset.letter === data.correct_answer) {
          btn.classList.add("correct");
        } else if (btn.dataset.letter === selectedLetter && !data.correct) {
          btn.classList.add("incorrect");
        }
      });

      const feedback = document.createElement("div");
      feedback.className = `quiz-feedback ${data.correct ? "correct" : "incorrect"}`;
      feedback.innerHTML = `
        <span class="quiz-feedback-label">${data.correct ? "✅ Correct!" : "❌ Not quite."}</span>
        ${data.explanation ? `<p class="quiz-explanation">💡 ${escapeHtml(data.explanation)}</p>` : ""}
        <span class="quiz-score">Score: ${data.score}/${data.total}</span>
      `;
      card.appendChild(feedback);
      scrollToBottom();

      if (data.finished) {
        setTimeout(() => renderQuizSummary(data.score, data.total), 700);
      } else {
        setTimeout(() => renderQuizQuestion(data.next_question), 900);
      }

    } catch (error) {
      console.error(error);
      appendMessage("bot", "Coach Spark", "Unable to connect to the server. Please try again.");
    }
  }

  function renderQuizSummary(score, total) {
    const pct = score / total;
    let emoji = "📖";
    let note = "Keep practicing — review the manual and try again!";

    if (pct === 1) {
      emoji = "🏆";
      note = "Perfect score! You know this material cold.";
    } else if (pct >= 0.7) {
      emoji = "🎉";
      note = "Nice work — solid understanding!";
    } else if (pct >= 0.4) {
      emoji = "👍";
      note = "Good effort — a bit more review will help.";
    }

    appendMessage("bot", "Coach Spark", `${emoji} Quiz complete! Final score: ${score}/${total}\n${note}`);
  }

  startBtn?.addEventListener("click", startSession);
  endBtn?.addEventListener("click", endSession);
  chatForm?.addEventListener("submit", sendMessage);
  quizQuickBtn?.addEventListener("click", () => {
    messageInput.value = "Quiz me on ";
    messageInput.focus();
  });
  progressBtn?.addEventListener("click", loadProgress);
});