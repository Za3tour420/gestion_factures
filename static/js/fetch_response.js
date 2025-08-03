// Elements
const chatArea = document.getElementById("chatArea");
const submitBtn = document.getElementById("submitBtn");
const query = document.getElementById("query");
const fileInput = document.getElementById("pdf");
const previewContainer = document.getElementById("previewContainer"); // For image preview
previewContainer.innerHTML = "";
window.addEventListener("DOMContentLoaded", updateButtonState); // Button disabled by default

/********* Functions *********/
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

query.addEventListener("input", updateButtonState);
fileInput.addEventListener("change", updateButtonState);

// Image preview (near input)
fileInput.addEventListener("change", () => {
  previewContainer.innerHTML = ""; // Clear old previews
  Array.from(fileInput.files).forEach(file => {
    if (file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = e => {
        const img = document.createElement("img");
        img.src = e.target.result;
        previewContainer.appendChild(img);
      };
      reader.readAsDataURL(file);
    }
  });
});

// Submit form
document.getElementById("chatForm").addEventListener("submit", async function(event) {
  event.preventDefault();

  // Get query value
  const form = new FormData();
  form.append("query", query.value);

  // See if any files were uploaded
  if (fileInput.files.length > 0) {
      form.append("pdf", fileInput.files[0]);
  }
  
  // Append user input (and image if uploaded) to chat area
  const userDiv = document.createElement("div");
  userDiv.className = `user`;
  
  Array.from(fileInput.files).forEach(file =>{
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

  const textDiv = document.createElement("div");
  textDiv.innerHTML = `<strong>User:</strong><div>${marked.parse(query.value)}</div>`;
  userDiv.appendChild(textDiv);
  chatArea.appendChild(userDiv);
  
  // Clear inputs
  fileInput.value = "";
  query.value = "";
  previewContainer.innerHTML = "";
  updateButtonState();
  scrollToBottom();
  
  // Loading spinner while generating
  const loadingDiv = document.createElement("div");
  loadingDiv.className = "message assistant";
  loadingDiv.id = "loading";
  loadingDiv.innerHTML = 
    `<strong>Assistant:</strong>
    <div class="loading-spinner"></div>`;
    
  chatArea.appendChild(loadingDiv);
  
  
  // Fetch response
  const response = await fetch("/chat", {
      method: "POST",
      body: form,
  });

  if (!response.ok) {
      alert("Erreur côté serveur.");
      return;
  }

  const data = await response.json();
  const newMessages = data.history.slice(-1) // Last message (AIMessage)
  document.getElementById("loading").remove(); // Remove spinner

  newMessages.forEach(msg => {
      const div = document.createElement("div");
      div.className = `message ${msg.role}`;
      div.innerHTML = `<strong>${msg.role.charAt(0).toUpperCase() + msg.role.slice(1)}:</strong><div>${marked.parse(msg.content)}</div>`;
      chatArea.appendChild(div);
  });
  scrollToBottom();
});
