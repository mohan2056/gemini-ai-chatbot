
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const chatMessages = document.getElementById("chatMessages");
const sendBtn = document.getElementById("sendBtn");
const clearBtn = document.getElementById("clearBtn");
const statusElement = document.getElementById("status");

// Stores messages for conversation context.
// Each item has a role and content.
let history = [];
let isLoading = false;

// Display one message in the chat window.
function addMessage(text, sender) {
    const wrapper = document.createElement("div");
    wrapper.className = `message ${sender}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = sender === "bot" ? "✦" : "U";

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    // textContent prevents AI-generated text
    // from being interpreted as HTML.
    bubble.textContent = text;

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);
    chatMessages.appendChild(wrapper);

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Send a question to FastAPI.
async function sendMessage(question) {
    if (isLoading) return;

    isLoading = true;
    sendBtn.disabled = true;
    clearBtn.disabled = true;
    messageInput.disabled = true;

    addMessage(question, "user");
    statusElement.textContent = "Gemini is thinking...";

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: question,
                history: history
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                typeof data.detail === "string"
                    ? data.detail
                    : "Request failed."
            );
        }

        addMessage(data.reply, "bot");

        // Store successful exchanges only.
        history.push({
            role: "user",
            content: question
        });

        history.push({
            role: "model",
            content: data.reply
        });

        // Keep the last six exchanges.
        history = history.slice(-12);

        statusElement.textContent = "";

    } catch (error) {
        addMessage(
            "Unable to get a response. " + error.message,
            "bot"
        );

        statusElement.textContent =
            "Please check the connection and try again.";

    } finally {
        isLoading = false;
        sendBtn.disabled = false;
        clearBtn.disabled = false;
        messageInput.disabled = false;
        messageInput.focus();
    }
}

// Handle form submission.
chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const question = messageInput.value.trim();

    if (!question || isLoading) return;

    messageInput.value = "";

    await sendMessage(question);
});

// Enter submits; Shift+Enter creates a new line.
messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();

        if (!isLoading) {
            chatForm.requestSubmit();
        }
    }
});

// Clear conversation and restore greeting.
clearBtn.addEventListener("click", () => {
    if (isLoading) return;

    history = [];
    chatMessages.innerHTML = "";
    statusElement.textContent = "";

    addMessage(
        "Hello! I'm your AI Tutor. " +
        "Ask me any programming question.",
        "bot"
    );

    messageInput.focus();
});

