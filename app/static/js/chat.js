const CHAT_ENABLED = true;

function setChatStatus(message) {
  const status = document.getElementById('chatStatus');
  if (status) {
    status.textContent = message || '';
  }
}

function wirePromptButtons(selector) {
  document.querySelectorAll(selector).forEach((button) => {
    button.addEventListener('click', () => {
      const input = document.getElementById('messageInput');
      if (input) input.value = button.textContent.trim();
      input?.focus();
    });
  });
}

async function sendMessage() {
  const input = document.getElementById('messageInput');
  const message = (input?.value || '').trim();
  if (!message) return;

  if (!CHAT_ENABLED) {
    setChatStatus('Demo mode: connect the backend to make this composer live.');
    return;
  }

  const shell = document.querySelector('[data-chat-role]');
  const role = shell?.dataset.chatRole || 'user';
  const endpoint = role === 'admin' ? '/chat/admin' : '/chat/user';

  appendMessage('user', message);

  try {
    setChatStatus('Thinking...');
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || payload.response || 'Chat request failed.');
    }
    setChatStatus('');
    input.value = '';
    appendMessage('assistant', payload.response || 'No response');
  } catch (error) {
    setChatStatus('Error: ' + (error.message || 'Unable to reach the assistant.'));
  }
}

function getTimeString() {
  const now = new Date();
  let h = now.getHours(), m = now.getMinutes();
  const ampm = h >= 12 ? 'PM' : 'AM';
  h = h % 12 || 12;
  return `${h}:${m.toString().padStart(2, '0')} ${ampm}`;
}

function appendMessage(role, text) {
  const history = document.getElementById('chatHistory');
  if (!history) return;

  const msg = document.createElement('div');
  msg.className = `message ${role}-message chat-message ${role}`;

  // add avatar for assistant
  if (role === 'assistant') {
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '🛒';
    msg.appendChild(avatar);
  }

  const wrapper = document.createElement('div');
  wrapper.className = 'message-wrapper';

  const content = document.createElement('div');
  content.className = 'message-content chat-bubble';

  // parse bullet points from text
  const lines = text.split('\n').filter(l => l.trim());
  const bulletLines = lines.filter(l => /^[\-\•\*]\s/.test(l.trim()));
  
  if (bulletLines.length > 1) {
    const intro = lines.filter(l => !/^[\-\•\*]\s/.test(l.trim()));
    if (intro.length) {
      const p = document.createElement('p');
      p.textContent = intro.join(' ');
      content.appendChild(p);
    }
    const ul = document.createElement('ul');
    bulletLines.forEach(bl => {
      const li = document.createElement('li');
      li.textContent = bl.replace(/^[\-\•\*]\s*/, '');
      ul.appendChild(li);
    });
    content.appendChild(ul);
  } else {
    const p = document.createElement('p');
    p.textContent = text;
    content.appendChild(p);
  }

  wrapper.appendChild(content);

  // timestamp
  const ts = document.createElement('span');
  ts.className = 'message-time';
  ts.textContent = getTimeString() + (role === 'user' ? ' ✓' : '');
  wrapper.appendChild(ts);

  msg.appendChild(wrapper);
  history.appendChild(msg);
  history.scrollTop = history.scrollHeight;
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('sendBtn')?.addEventListener('click', () => sendMessage());
  document.getElementById('messageInput')?.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      sendMessage();
    }
  });

  wirePromptButtons('.chat-chip');
  wirePromptButtons('.admin-chip');

  if (document.getElementById('chatHistory')?.children.length === 0) {
    const shell = document.querySelector('[data-chat-role]');
    const role = shell?.dataset.chatRole || 'user';
    const welcomeMessages = {
      admin: 'Hello Admin! I\'m your Admin Assistant. Ask me about stock levels, trending products, sales forecasts, restocking recommendations, or business insights.',
      user: 'Hello! I can help with product recommendations, order status, shipping, returns, and warranty questions.',
    };
    appendMessage('assistant', welcomeMessages[role] || welcomeMessages.user);
  }

  document.getElementById('newChatBtn')?.addEventListener('click', () => {
    const input = document.getElementById('messageInput');
    if (input) input.value = '';
    setChatStatus('');
  });
});
