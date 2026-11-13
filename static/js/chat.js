const chatContainer = document.getElementById('chatContainer');
const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

function scrollToBottom() {
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function appendUserMessage(text) {
  const row = document.createElement('div');
  row.className = 'message-row user';
  row.innerHTML = `
    <div class="message-bubble">${escapeHtml(text)}</div>
    <div class="avatar user-avatar">You</div>
  `;
  chatContainer.appendChild(row);
  scrollToBottom();
}

function showTypingIndicator() {
  const row = document.createElement('div');
  row.className = 'message-row bot';
  row.id = 'typingIndicator';
  row.innerHTML = `
    <div class="avatar bot-avatar">AI</div>
    <div class="typing-bubble">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>
  `;
  chatContainer.appendChild(row);
  scrollToBottom();
}

function hideTypingIndicator() {
  const indicator = document.getElementById('typingIndicator');
  if (indicator) {
    indicator.remove();
  }
}

function appendBotMessage(reply, category) {
  const row = document.createElement('div');
  row.className = 'message-row bot';
  
  const categoryBadge = category ? `<br><span class="category-tag">${escapeHtml(category)}</span>` : '';
  
  row.innerHTML = `
    <div class="avatar bot-avatar">AI</div>
    <div class="message-bubble">
      ${escapeHtml(reply).replace(/\n/g, '<br>')}
      ${categoryBadge}
    </div>
  `;
  chatContainer.appendChild(row);
  scrollToBottom();
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.innerText = text;
  return div.innerHTML;
}

async function sendMessage(text) {
  const cleanText = text.trim();
  if (!cleanText) return;

  // Render user question
  appendUserMessage(cleanText);
  userInput.value = '';
  userInput.disabled = true;
  sendBtn.disabled = true;

  // Show typing indicator
  showTypingIndicator();

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message: cleanText })
    });

    const data = await response.json();
    hideTypingIndicator();

    if (response.ok) {
      appendBotMessage(data.reply, data.category);
    } else {
      appendBotMessage(data.reply || "An error occurred. Please try again.", "Error");
    }
  } catch (error) {
    hideTypingIndicator();
    appendBotMessage("Connection issue. Please check your network and try again.", "Error");
  } finally {
    userInput.disabled = false;
    sendBtn.disabled = false;
    userInput.focus();
    scrollToBottom();
  }
}

function handleChatSubmit(event) {
  event.preventDefault();
  const text = userInput.value;
  sendMessage(text);
}

function sendChipMessage(text) {
  sendMessage(text);
}

// Initial focus
window.addEventListener('DOMContentLoaded', () => {
  if (userInput) userInput.focus();
});
