let isProcessing = false;

// Initialize the vector background
window.addEventListener("DOMContentLoaded", () => {
  const vectorBg = document.getElementById("vector-bg");

  for (let i = 0; i < 15; i++) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("width", "300");
    svg.setAttribute("height", "300");
    svg.classList.add("vector-element");

    // Random position
    svg.style.left = `${Math.random() * 100}%`;
    svg.style.top = `${Math.random() * 100}%`;

    // Create circle or path
    if (Math.random() > 0.5) {
      const circle = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "circle",
      );
      circle.setAttribute("cx", "150");
      circle.setAttribute("cy", "150");
      circle.setAttribute("r", `${50 + Math.random() * 100}`);
      svg.appendChild(circle);
    } else {
      const path = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "path",
      );
      path.setAttribute(
        "d",
        `M150,50 Q${50 + Math.random() * 200},${50 + Math.random() * 200} 150,250`,
      );
      svg.appendChild(path);
    }

    vectorBg.appendChild(svg);
  }
});

// Initialize Marked.js for markdown rendering
marked.setOptions({
  highlight: function (code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value;
    }
    return hljs.highlightAuto(code).value;
  },
  breaks: true,
  gfm: true,
});

// Handle image preview
function previewImage(event) {
  const preview = document.getElementById("imagePreview");
  const file = event.target.files[0];

  if (file) {
    const reader = new FileReader();
    reader.onload = function (e) {
      preview.innerHTML = `
                <div class="preview-wrapper">
                    <img src="${e.target.result}" class="preview-image">
                    <button type="button" class="remove-image" onclick="removeImage()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
    };
    reader.readAsDataURL(file);
  } else {
    preview.innerHTML = "";
  }
}

// Remove selected image
function removeImage() {
  document.getElementById("imageInput").value = "";
  document.getElementById("imagePreview").innerHTML = "";
}

// Handle Enter key press
function handleKeyPress(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

// Sanitize HTML to prevent XSS
function sanitizeHTML(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Add a timestamp to messages
function getTimestamp() {
  const now = new Date();
  return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// Send message to server
async function sendMessage() {
  if (isProcessing) return;

  const imageInput = document.getElementById("imageInput");
  const messageInput = document.getElementById("messageInput");
  const chatContainer = document.getElementById("chatContainer");
  const loading = document.getElementById("loading");
  const preview = document.getElementById("imagePreview");

  const message = messageInput.value.trim();
  if (!message) {
    messageInput.classList.add("error");
    setTimeout(() => messageInput.classList.remove("error"), 800);
    return;
  }

  isProcessing = true;
  loading.style.display = "flex";

  const formData = new FormData();
  formData.append("message", message);

  let imageIncluded = false;

  if (imageInput.files[0]) {
    formData.append("image", imageInput.files[0]);
    imageIncluded = true;
  }

  // Create user message element
  const userMessageElement = document.createElement("div");
  userMessageElement.className = "message-wrapper user-message-wrapper";
  userMessageElement.innerHTML = `
        <div class="message user-message">
            <strong>You <span class="message-time">${getTimestamp()}</span></strong>
            <p>${sanitizeHTML(message)}</p>
            ${imageIncluded ? '<img src="' + URL.createObjectURL(imageInput.files[0]) + '" class="preview-image">' : ""}
        </div>
    `;

  chatContainer.appendChild(userMessageElement);
  chatContainer.scrollTop = chatContainer.scrollHeight;

  try {
    const response = await fetch("/chat", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    // Create bot message element with avatar
    const botMessageElement = document.createElement("div");
    botMessageElement.className = "message-wrapper bot-message-wrapper";
    botMessageElement.innerHTML = `
            <div class="bot-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message bot-message">
                <strong>AI Assistant <span class="message-time">${getTimestamp()}</span></strong>
                <div class="markdown-content">${marked.parse(data.response)}</div>
            </div>
        `;

    chatContainer.appendChild(botMessageElement);

    // Apply syntax highlighting to code blocks
    document.querySelectorAll("pre code").forEach((block) => {
      hljs.highlightBlock(block);
    });

    // Add animation to the bot message
    gsap.from(botMessageElement, {
      y: 20,
      opacity: 0,
      duration: 0.4,
      ease: "power2.out",
    });
  } catch (error) {
    // Create error message
    const errorElement = document.createElement("div");
    errorElement.className = "message-wrapper bot-message-wrapper";
    errorElement.innerHTML = `
            <div class="bot-avatar">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="message bot-message error-message">
                <strong>Error <span class="message-time">${getTimestamp()}</span></strong>
                <p>${sanitizeHTML(error.message || "Something went wrong. Please try again.")}</p>
            </div>
        `;
    chatContainer.appendChild(errorElement);
  } finally {
    messageInput.value = "";
    imageInput.value = "";
    preview.innerHTML = "";
    loading.style.display = "none";
    isProcessing = false;
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }
}

// Add copy functionality to code blocks
function setupCodeBlocks() {
  document.querySelectorAll(".markdown-content pre").forEach((block) => {
    // Only add button if it doesn't already have one
    if (!block.querySelector(".copy-code-button")) {
      const copyButton = document.createElement("button");
      copyButton.className = "copy-code-button";
      copyButton.innerHTML = '<i class="fas fa-copy"></i>';
      copyButton.title = "Copy code";
      copyButton.addEventListener("click", () => {
        const code = block.querySelector("code").innerText;
        navigator.clipboard.writeText(code).then(() => {
          copyButton.innerHTML = '<i class="fas fa-check"></i>';
          setTimeout(() => {
            copyButton.innerHTML = '<i class="fas fa-copy"></i>';
          }, 2000);
        });
      });
      block.appendChild(copyButton);
    }
  });

  // Make links open in new tab
  document.querySelectorAll(".markdown-content a").forEach((link) => {
    if (!link.hasAttribute("target")) {
      link.setAttribute("target", "_blank");
      link.setAttribute("rel", "noopener noreferrer");
    }
  });
}

// Call setupCodeBlocks after bot message is added
document.addEventListener("DOMContentLoaded", () => {
  // Check for existing code blocks on page load
  setupCodeBlocks();

  // Create an observer to watch for changes in the chat container
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.addedNodes.length) {
        setupCodeBlocks();
      }
    });
  });

  const chatContainer = document.getElementById("chatContainer");
  observer.observe(chatContainer, { childList: true, subtree: true });
});
