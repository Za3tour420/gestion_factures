const chatArea = document.getElementById("chatArea");


function scrollToBottom() {
  chatArea.scrollTop = chatArea.scrollHeight;
}

const fileInput = document.getElementById("pdf");
const previewContainer = document.getElementById("previewContainer"); // For image preview
previewContainer.innerHTML = "";

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

document.getElementById("chatForm").addEventListener("submit", async function(event) {
  event.preventDefault();

  const form = new FormData();
  const query = document.getElementById("query").value;
  form.append("query", query);

  if (fileInput.files.length > 0) {
      form.append("pdf", fileInput.files[0]);
  }
  
  // Clear inputs
  document.getElementById("query").value = "";
  document.getElementById("pdf").value = "";
  previewContainer.innerHTML = "";
  
  // Append user input
  const div = document.createElement("div");
  div.className = `user`;
  div.innerHTML = `<strong>User:</strong><div>${marked.parse(query)}</div>`;
  chatArea.appendChild(div);
  
  // Loading spinner while generating
  const loadingDiv = document.createElement("div");
  loadingDiv.className = "message assistant";
  loadingDiv.id = "loading";
  loadingDiv.innerHTML = 
    `<strong>Assistant:</strong>
    <div class="loading-spinner"></div>`;
    
  chatArea.appendChild(loadingDiv);
  scrollToBottom();

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
      chatArea.lastElementChild?.scrollIntoView({ behavior: 'smooth' });
  });

  
  scrollToBottom();
});
