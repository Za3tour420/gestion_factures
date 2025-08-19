// Updated fetch_response.js with batch processing support

// Elements
const chatArea = document.getElementById("chatArea");
const submitBtn = document.getElementById("submitBtn");
const query = document.getElementById("query");
const fileInput = document.getElementById("fileUpload");
const clearFilesBtn = document.getElementById("clearFilesBtn");
const previewContainer = document.getElementById("previewContainer");

let isSubmitting = false;

// Configuration constants
const MAX_FILES = 5;
const MAX_IMAGES = 3;
const MAX_FILE_SIZE_MB = 10; // Per file
const MAX_TOTAL_SIZE_MB = 50;

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

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function isImageFile(filename) {
    const imageExtensions = ['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp'];
    const extension = filename.split('.').pop().toLowerCase();
    return imageExtensions.includes(extension);
}

function validateFiles(files) {
    const errors = [];
    let totalSize = 0;
    let imageCount = 0;

    if (files.length > MAX_FILES) {
        errors.push(`Trop de fichiers sélectionnés. Maximum: ${MAX_FILES}`);
        return { valid: false, errors };
    }

    for (let file of files) {
        // Check individual file size
        if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
            errors.push(`${file.name} est trop volumineux (max: ${MAX_FILE_SIZE_MB}MB)`);
        }

        // Count images
        if (isImageFile(file.name)) {
            imageCount++;
        }

        totalSize += file.size;
    }

    // Check image count
    if (imageCount > MAX_IMAGES) {
        errors.push(`Trop d'images sélectionnées. Maximum: ${MAX_IMAGES}`);
    }

    // Check total size
    if (totalSize > MAX_TOTAL_SIZE_MB * 1024 * 1024) {
        errors.push(`Taille totale trop importante (max: ${MAX_TOTAL_SIZE_MB}MB)`);
    }

    return { valid: errors.length === 0, errors, totalSize, imageCount };
}

function updateButtonState() {
    const hasText = query.value.trim().length > 0;
    const hasFiles = fileInput.files.length > 0;
    submitBtn.disabled = !(hasText || hasFiles) || isSubmitting;
    
    // Update submit button text based on file count
    if (hasFiles) {
        const fileCount = fileInput.files.length;
        submitBtn.textContent = `🚀 Analyser ${fileCount} fichier${fileCount > 1 ? 's' : ''}`;
    } else {
        submitBtn.textContent = '🚀 Analyser';
    }
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

function showError(message) {
    const errorDiv = document.createElement("div");
    errorDiv.className = "error-message";
    errorDiv.style.cssText = `
        background: #fee;
        border: 1px solid #fcc;
        color: #c33;
        padding: 10px;
        margin: 10px 0;
        border-radius: 5px;
        font-size: 14px;
    `;
    errorDiv.textContent = message;
    
    // Insert before the chat input
    const chatInput = document.querySelector('.chat-input');
    chatInput.parentNode.insertBefore(errorDiv, chatInput);
    
    // Remove after 5 seconds
    setTimeout(() => errorDiv.remove(), 5000);
}

function updatePreviewContainer() {
    previewContainer.innerHTML = "";
    const files = Array.from(fileInput.files);
    
    if (files.length === 0) return;

    // Validate files
    const validation = validateFiles(files);
    
    if (!validation.valid) {
        validation.errors.forEach(error => showError(error));
        fileInput.value = ""; // Clear invalid selection
        updateButtonState();
        return;
    }

    // Create preview container header
    const headerDiv = document.createElement("div");
    headerDiv.className = "preview-header";
    headerDiv.innerHTML = `
        <span>📎 ${files.length} fichier${files.length > 1 ? 's' : ''} sélectionné${files.length > 1 ? 's' : ''}</span>
        <span class="total-size">(${formatFileSize(validation.totalSize)})</span>
    `;
    previewContainer.appendChild(headerDiv);

    // Create previews for each file
    files.forEach((file, index) => {
        const fileDiv = document.createElement("div");
        fileDiv.className = "file-preview-item";
        fileDiv.style.cssText = `
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin: 5px 0;
            background: #f9f9f9;
        `;

        if (isImageFile(file.name)) {
            // Image preview
            const reader = new FileReader();
            reader.onload = e => {
                const img = document.createElement("img");
                img.src = e.target.result;
                img.style.cssText = "width: 40px; height: 40px; object-fit: cover; border-radius: 3px;";
                fileDiv.appendChild(img);
                
                const infoDiv = document.createElement("div");
                infoDiv.innerHTML = `
                    <div style="font-weight: bold; font-size: 12px;">${file.name}</div>
                    <div style="font-size: 11px; color: #666;">${formatFileSize(file.size)}</div>
                `;
                fileDiv.appendChild(infoDiv);
            };
            reader.readAsDataURL(file);
        } else {
            // Document preview
            const icon = document.createElement("div");
            icon.textContent = "📄";
            icon.style.cssText = "font-size: 24px; width: 40px; text-align: center;";
            fileDiv.appendChild(icon);
            
            const infoDiv = document.createElement("div");
            infoDiv.innerHTML = `
                <div style="font-weight: bold; font-size: 12px;">${file.name}</div>
                <div style="font-size: 11px; color: #666;">${formatFileSize(file.size)}</div>
            `;
            fileDiv.appendChild(infoDiv);
        }

        previewContainer.appendChild(fileDiv);
    });
}

/********* Event Listeners *********/

// Button state updates
query.addEventListener("input", updateButtonState);
fileInput.addEventListener("change", () => {
    updateButtonState();
    updatePreviewContainer();
});

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

// Submit form
document.getElementById("chatForm").addEventListener("submit", async function(event) {
    event.preventDefault();
    
    if (isSubmitting) return;
    
    const files = Array.from(fileInput.files);
    const userQuery = query.value.trim();
    
    // Final validation before submission
    if (files.length > 0) {
        const validation = validateFiles(files);
        if (!validation.valid) {
            validation.errors.forEach(error => showError(error));
            return;
        }
    }
    
    if (!userQuery && files.length === 0) {
        showError("Veuillez saisir une question ou sélectionner des fichiers.");
        return;
    }
    
    isSubmitting = true;
    hideEmptyState();
    
    const form = new FormData();
    form.append("query", userQuery);
    
    // Append all files
    files.forEach(file => {
        form.append("fileUpload", file);
    });
    
    // Create user message with file information
    const userDiv = document.createElement("div");
    userDiv.className = "message user";
    
    let contentHtml = `<div class="message-header">Vous</div>`;
    contentHtml += `<div class="content">${marked.parse(userQuery) || '<em>Fichiers téléchargés</em>'}</div>`;
    
    // Add file summary
    if (files.length > 0) {
        contentHtml += `<div class="file-summary" style="margin-top: 8px; font-size: 12px; color: #666;">`;
        contentHtml += `📎 ${files.length} fichier${files.length > 1 ? 's' : ''}: `;
        contentHtml += files.map(f => f.name).join(', ');
        contentHtml += `</div>`;
    }
    
    userDiv.innerHTML = contentHtml;
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
            const errorData = await response.json();
            throw new Error(errorData.error || "Erreur serveur");
        }
        
        const data = await response.json();
        
        // Get the last message from the server response
        const lastMessage = data.history[data.history.length - 1];
        
        // Add assistant response
        if (lastMessage && lastMessage.role === 'assistant') {
            const div = document.createElement("div");
            div.className = "message assistant";
            div.innerHTML = `
                <div class="message-header">Assistant</div>
                <div class="content">${marked.parse(lastMessage.content)}</div>
            `;
            chatArea.appendChild(div);
        }
        
        scrollToBottom();
        
    } catch (error) {
        removeTypingIndicator();
        showError(error.message);
        
        const errorDiv = document.createElement("div");
        errorDiv.className = "message assistant";
        errorDiv.innerHTML = `
            <div class="message-header">Assistant</div>
            <div class="content">❌ ${error.message}</div>
        `;
        chatArea.appendChild(errorDiv);
        scrollToBottom();
    } finally {
        isSubmitting = false;
        updateButtonState();
    }
});

// Enter key to submit (Shift+Enter for new line)
query.addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !event.shiftKey && !event.ctrlKey) {
        event.preventDefault();
        if (!submitBtn.disabled && !isSubmitting) {
            document.getElementById("chatForm").requestSubmit();
        }
    }
});
