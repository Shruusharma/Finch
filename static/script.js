/* ============================================================
   FINCH AI — script.js
   Handles: navbar scroll, scroll reveal, chat API, insights
   ============================================================ */

// ─────────────────────────────────────────────────────────────
// CONFIGURATION
// Change this to your deployed Railway URL when running locally.
// When served from FastAPI on Railway, "/" auto-resolves.
// ─────────────────────────────────────────────────────────────
const API_BASE = "";  // Empty string = same origin (correct for Railway deployment)
//
// If you are opening index.html directly from your file system
// (not through FastAPI), change the line above to:
// const API_BASE = "https://finch-production-95c79.up.railway.app";


// ─────────────────────────────────────────────────────────────
// NAVBAR — adds `.scrolled` class after 40px scroll
// ─────────────────────────────────────────────────────────────
const navbar = document.getElementById("navbar");

window.addEventListener("scroll", () => {
  if (window.scrollY > 40) {
    navbar.classList.add("scrolled");
  } else {
    navbar.classList.remove("scrolled");
  }
}, { passive: true });


// ─────────────────────────────────────────────────────────────
// SCROLL REVEAL — animates elements as they enter viewport
// Uses IntersectionObserver (no scroll event listener needed)
// ─────────────────────────────────────────────────────────────
const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const delay = el.dataset.delay ? parseInt(el.dataset.delay) : 0;
        setTimeout(() => {
          el.classList.add("visible");
        }, delay);
        revealObserver.unobserve(el); // Only animate once
      }
    });
  },
  { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
);

// Observe all feature cards and section headers
document.querySelectorAll(".feature-card, [data-reveal]").forEach((el) => {
  revealObserver.observe(el);
});


// ─────────────────────────────────────────────────────────────
// CHAT — core functionality
// ─────────────────────────────────────────────────────────────
const chatMessages   = document.getElementById("chatMessages");
const chatInput      = document.getElementById("chatInput");
const sendBtn        = document.getElementById("sendBtn");
const typingIndicator = document.getElementById("typingIndicator");
const chatError      = document.getElementById("chatError");
const chatErrorText  = document.getElementById("chatErrorText");
const dismissError   = document.getElementById("dismissError");

// Track if a request is in flight so we don't double-send
let isLoading = false;

/**
 * Appends a message bubble to the chat window.
 * @param {string} role - "user" or "assistant"
 * @param {string} text - The message content
 */
function appendMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = role === "user" ? "U" : "F";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";

  // Split on double newlines to render paragraphs properly
  const paragraphs = text.trim().split(/\n\n+/);
  paragraphs.forEach((para) => {
    if (para.trim()) {
      const p = document.createElement("p");
      // Handle single newlines within a paragraph as <br>
      p.innerHTML = para.trim().replace(/\n/g, "<br>");
      bubble.appendChild(p);
    }
  });

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  chatMessages.appendChild(wrapper);

  // Auto-scroll to bottom
  scrollToBottom();
}

/**
 * Smoothly scrolls the chat messages container to the bottom.
 */
function scrollToBottom() {
  chatMessages.scrollTo({
    top: chatMessages.scrollHeight,
    behavior: "smooth",
  });
}

/**
 * Shows or hides the typing indicator.
 */
function setTyping(visible) {
  typingIndicator.style.display = visible ? "block" : "none";
  if (visible) {
    scrollToBottom();
  }
}

/**
 * Shows an error message in the chat error bar.
 */
function showError(message) {
  chatErrorText.textContent = message;
  chatError.style.display = "flex";
}

/**
 * Hides the error bar.
 */
function hideError() {
  chatError.style.display = "none";
}

dismissError.addEventListener("click", hideError);

/**
 * Disables or enables the send button and input.
 */
function setInputDisabled(disabled) {
  sendBtn.disabled = disabled;
  chatInput.disabled = disabled;
}

/**
 * Main function: sends the user message to the backend and
 * displays the response.
 *
 * API contract:
 *   POST /api/v1/chat
 *   Body: { "message": "..." }
 *   Response: { "response": "..." }
 */
async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text || isLoading) return;

  isLoading = true;
  hideError();
  setInputDisabled(true);

  // Show the user's message immediately
  appendMessage("user", text);

  // Clear the input and reset its height
  chatInput.value = "";
  chatInput.style.height = "auto";

  // Show the animated typing dots
  setTyping(true);

  try {
    const response = await fetch(`${API_BASE}/api/v1/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message: text }),
    });

    // Parse the JSON regardless of status code so we can show
    // the backend's error message if it provides one
    const data = await response.json();

    if (!response.ok) {
      // Backend returned a structured error
      const detail = data.detail || data.error || `Server error ${response.status}`;
      throw new Error(detail);
    }

    // Success — display the assistant's response
    setTyping(false);

    const aiText = data.response || "I didn't receive a response. Please try again.";
    appendMessage("assistant", aiText);

  } catch (err) {
    setTyping(false);

    // Differentiate network errors from API errors
    if (err instanceof TypeError && err.message.includes("fetch")) {
      showError("Could not reach the Finch backend. Check your connection or the API_BASE setting in script.js.");
    } else {
      showError(`Error: ${err.message}`);
    }
  } finally {
    isLoading = false;
    setInputDisabled(false);
    chatInput.focus();
  }
}


// ─────────────────────────────────────────────────────────────
// CHAT INPUT — send on Enter (Shift+Enter = newline)
// ─────────────────────────────────────────────────────────────
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendBtn.addEventListener("click", sendMessage);

// Auto-grow textarea height as user types
chatInput.addEventListener("input", () => {
  chatInput.style.height = "auto";
  chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + "px";
});


// ─────────────────────────────────────────────────────────────
// PROMPT CHIPS — clicking a chip fills and sends the input
// ─────────────────────────────────────────────────────────────
document.querySelectorAll(".prompt-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const prompt = chip.dataset.prompt;
    chatInput.value = prompt;
    chatInput.style.height = "auto";
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + "px";

    // Scroll to chat section if not visible, then send
    document.getElementById("chat").scrollIntoView({ behavior: "smooth", block: "start" });

    // Small delay to let scroll settle before sending
    setTimeout(() => {
      sendMessage();
    }, 400);
  });
});


// ─────────────────────────────────────────────────────────────
// WEEKLY INSIGHT — loads from GET /api/v1/insights/latest
// ─────────────────────────────────────────────────────────────
const loadInsightBtn = document.getElementById("loadInsight");
const insightBody    = document.getElementById("insightBody");

loadInsightBtn.addEventListener("click", async () => {
  loadInsightBtn.textContent = "Loading…";
  loadInsightBtn.disabled = true;

  try {
    const response = await fetch(`${API_BASE}/api/v1/insights/latest`);

    if (response.status === 404) {
      insightBody.innerHTML = `<p style="color: var(--text-dim); font-size: 12px;">No insight generated yet. Finch runs every Monday at 9 AM UTC.</p>`;
      return;
    }

    if (!response.ok) {
      throw new Error(`Server error ${response.status}`);
    }

    const data = await response.json();

    // The insight endpoint returns the insight text in `data.insight`
    // or wrapped in whatever structure your insight_store uses.
    // Adjust the field name below if your backend returns a different key.
    const insightText = data.insight || data.content || data.report || JSON.stringify(data, null, 2);

    // Truncate for the sidebar panel — user can scroll the chat for full version
    const truncated = insightText.length > 300
      ? insightText.slice(0, 300) + "…"
      : insightText;

    insightBody.innerHTML = `
      <p style="font-size: 12px; line-height: 1.6; color: var(--text-muted);">${truncated}</p>
      <button class="btn btn-ghost btn-sm" id="viewFullInsight" style="margin-top: 10px;">
        View full insight in chat →
      </button>
    `;

    // Clicking "view full" sends it as a chat message
    document.getElementById("viewFullInsight").addEventListener("click", () => {
      chatInput.value = "Show me the latest weekly investment insight";
      sendMessage();
      document.getElementById("chat").scrollIntoView({ behavior: "smooth" });
    });

  } catch (err) {
    insightBody.innerHTML = `<p style="color: #fca5a5; font-size: 12px;">Could not load insight: ${err.message}</p>`;
  }
});


// ─────────────────────────────────────────────────────────────
// MOBILE NAV — hamburger toggle
// ─────────────────────────────────────────────────────────────
const hamburger = document.getElementById("hamburger");

hamburger.addEventListener("click", () => {
  // Simple approach: toggle a mobile menu overlay
  // For this implementation we scroll to the chat section directly
  document.getElementById("chat").scrollIntoView({ behavior: "smooth" });
});


// ─────────────────────────────────────────────────────────────
// SMOOTH SCROLL — internal anchor links
// ─────────────────────────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", (e) => {
    const target = document.querySelector(anchor.getAttribute("href"));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
});
