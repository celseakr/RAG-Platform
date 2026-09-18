// ============================
// GET HTML ELEMENTS
// ============================

const tabs = document.querySelectorAll(".tab");

const panels = document.querySelectorAll(".panel");

const fileInput = document.getElementById("file-input");

const fileInfo = document.getElementById("file-info");

const fileName = document.getElementById("file-name");

const fileSize = document.getElementById("file-size");

const documentName = document.getElementById("document-name");

const questionForm = document.getElementById("question-form");

const questionInput = document.getElementById("question-input");

const messages = document.getElementById("messages");

const thinking = document.getElementById("thinking");

// ============================
// TAB FUNCTIONALITY
// ============================

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    // Remove active class
    // from all tabs

    tabs.forEach((tab) => {
      tab.classList.remove("active");
    });

    // Remove active class
    // from all panels

    panels.forEach((panel) => {
      panel.classList.remove("active");
    });

    // Add active class
    // to clicked tab

    tab.classList.add("active");

    // Get the tab name

    const tabName = tab.dataset.tab;

    // Show the correct panel

    document.getElementById(`${tabName}-panel`).classList.add("active");
  });
});

// ============================
// FILE UPLOAD
// ============================
fileInput.addEventListener("change", async (event) => {
  const file = event.target.files[0];

  if (!file) {
    return;
  }

  // Show file information
  fileName.textContent = file.name;

  const size = (file.size / 1024 / 1024).toFixed(2);
  fileSize.textContent = `${size} MB`;

  fileInfo.classList.add("show");

  // Update chat document name
  documentName.textContent = file.name;

  // Send PDF to FastAPI
  const formData = new FormData(); //Think of FormData as a package/envelope that JavaScript can use to send an actual file.
  formData.append("file", file);

  // Switch to chat immediately
  document.querySelector('[data-tab="chat"]').click();

  try {
    const response = await fetch("http://127.0.0.1:8000/upload", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    console.log(data);
  } catch (error) {
    console.error("Upload error:", error);
  }
});

// ============================
// QUESTION FORM
// ============================

questionForm.addEventListener("submit", async (event) => {
  // Stop page refresh
  event.preventDefault();

  const question = questionInput.value.trim();

  // Don't do anything if input is empty
  if (!question) {
    return;
  }

  // Create user's message
  const userMessage = document.createElement("div");
  userMessage.classList.add("message");

  userMessage.innerHTML = `
        <div class="message-icon">
            C
        </div>
        <div>
            <small>YOU</small>
            <p>${question}</p>
        </div>
    `;

  // Add user's message to chat
  messages.appendChild(userMessage);

  // Clear input
  questionInput.value = "";

  // Show thinking indicator
  thinking.style.display = "flex";

  try {
    // Send question to FastAPI
    const response = await fetch("http://127.0.0.1:8000/ask", {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        question: question,
        file: fileInput.files[0].name,
      }),
    });

    // Convert response from JSON
    const data = await response.json();

    // Create AI message
    const aiMessage = document.createElement("div");
    aiMessage.classList.add("message");

    aiMessage.innerHTML = `
            <div class="message-icon">
                ✦
            </div>
            <div>
                <small>DOCQUERY</small>
                <p>${data.answer}</p>
            </div>
        `;

    // Add AI response to chat
    messages.appendChild(aiMessage);
  } catch (error) {
    console.error("Error:", error);

    const aiMessage = document.createElement("div");
    aiMessage.classList.add("message");

    aiMessage.innerHTML = `
            <div class="message-icon">
                ✦
            </div>
            <div>
                <small>DOCQUERY</small>
                <p>
                    Sorry, I couldn't connect to the RAG server.
                </p>
            </div>
        `;

    messages.appendChild(aiMessage);
  } finally {
    // Hide thinking indicator
    thinking.style.display = "none";
  }
});
