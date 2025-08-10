// Elements
const chatArea = document.getElementById("chatArea");
const submitBtn = document.getElementById("submitBtn");
const query = document.getElementById("query");
const fileInput = document.getElementById("pdf");
const clearFilesBtn = document.getElementById("clearFilesBtn");
const previewContainer = document.getElementById("previewContainer");

let messageCount = 0;

previewContainer.innerHTML = "";
window.addEventListener("DOMContentLoaded", updateButtonState);

/********* Functions *********/
function setQuery(text) {
    query.value = text;
    query.focus();
    updateButtonState();
    hideEmptyState();
}

function hideEmptyState() {
    const emptyState = chatArea.querySelector('.empty-state');
    if (emptyState) {
        emptyState.style.display = 'none';
    }
}

function scrollToBottom() {
    chatArea.scrollTo({
        top: chatArea.scrollHeight,
        behavior: "smooth"
    });
}

function updateButtonState() {
    const hasText = query.value.trim().length > 0;
    const hasFiles = fileInput.files.length > 0;
    submitBtn.disabled = !(hasText || hasFiles);
}

function showTypingIndicator() {
    const typingDiv = document.createElement("div");
    typingDiv.className = "typing-indicator";
    typingDiv.id = "typing-indicator";
    typingDiv.innerHTML = `
        <div class="message-header">Assistant</div>
        <div class="typing-dots">
            <div></div>
            <div></div>
            <div></div>
        </div>
    `;
    chatArea.appendChild(typingDiv);
    scrollToBottom();
}

function removeTypingIndicator() {
    const typing = document.getElementById("typing-indicator");
    if (typing) typing.remove();
}

/********* Event Listeners *********/

// Button state updates
query.addEventListener("input", updateButtonState);
fileInput.addEventListener("change", updateButtonState);

// Auto-resize textarea
query.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

// Clear file button event listener
clearFilesBtn.addEventListener("click", () => {
    fileInput.value = "";
    previewContainer.innerHTML = "";
    updateButtonState();
});

// Image preview
fileInput.addEventListener("change", () => {
    previewContainer.innerHTML = "";
    Array.from(fileInput.files).forEach(file => {
        if (file.type.startsWith("image/")) {
            const reader = new FileReader();
            reader.onload = e => {
                const img = document.createElement("img");
                img.src = e.target.result;
                img.title = file.name;
                previewContainer.appendChild(img);
            };
            reader.readAsDataURL(file);
        }
    });
});

// Submit form
document.getElementById("chatForm").addEventListener("submit", async function(event) {
    event.preventDefault();
    hideEmptyState();
    
    const form = new FormData();
    form.append("query", query.value);
    
    if (fileInput.files.length > 0) {
        form.append("pdf", fileInput.files[0]);
    }
    
    // Add user message
    messageCount++;
    const userDiv = document.createElement("div");
    userDiv.className = "message user";
    
    let imageHtml = "";
    Array.from(fileInput.files).forEach(file => {
        if (file.type.startsWith("image/")) {
            const reader = new FileReader();
            reader.onload = e => {
                const img = document.createElement("img");
                img.src = e.target.result;
                userDiv.appendChild(img);
            };
            reader.readAsDataURL(file);
        }
    });
    
    userDiv.innerHTML = `
        <div class="message-header">Vous</div>
        <div class="content">${marked.parse(query.value) || '<em>Document téléchargé</em>'}</div>
    `;
    
    if (imageHtml) {
        userDiv.innerHTML += imageHtml;
    }
    
    chatArea.appendChild(userDiv);
    
    // Clear inputs
    fileInput.value = "";
    query.value = "";
    query.style.height = 'auto';
    previewContainer.innerHTML = "";
    updateButtonState();
    scrollToBottom();
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Fetch response
        const response = await fetch("/chat", {
            method: "POST",
            body: form,
        });
        
        removeTypingIndicator();
        
        if (!response.ok) {
            throw new Error("Erreur serveur");
        }
        
        const data = await response.json();
        const newMessages = data.history.slice(-1);
        
        newMessages.forEach(msg => {
            const div = document.createElement("div");
            div.className = `message ${msg.role}`;
            div.innerHTML = `
                <div class="message-header">${msg.role === 'assistant' ? 'Assistant' : 'Vous'}</div>
                <div class="content">${marked.parse(msg.content)}</div>
            `;
            chatArea.appendChild(div);
        });
        
        scrollToBottom();
        
    } catch (error) {
        removeTypingIndicator();
        const errorDiv = document.createElement("div");
        errorDiv.className = "message assistant";
        errorDiv.innerHTML = `
            <div class="message-header">Assistant</div>
            <div class="content">❌ Une erreur est survenue. Veuillez réessayer.</div>
        `;
        chatArea.appendChild(errorDiv);
        scrollToBottom();
    }
});

// Enter key to submit (Ctrl+Enter for new line)
query.addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !event.shiftKey && !event.ctrlKey) {
        event.preventDefault();
        if (!submitBtn.disabled) {
            document.getElementById("chatForm").dispatchEvent(new Event('submit'));
        }
    }
});
