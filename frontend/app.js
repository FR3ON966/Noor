/**
 * UST Smart Chatbot — Frontend Application
 * Manages chat interactions, UI state, and API communication.
 */

// ──────── State ────────
const state = {
    conversationId: null,
    isLoading: false,
    theme: localStorage.getItem('ust-theme') || 'dark',
    messageCount: 0,
};

// ──────── DOM Elements ────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const messagesContainer = $('#messagesContainer');
const welcomeScreen = $('#welcomeScreen');
const messageInput = $('#messageInput');
const sendBtn = $('#sendBtn');
const newChatBtn = $('#newChatBtn');
const newChatBtnMobile = $('#newChatBtnMobile');
const themeToggle = $('#themeToggle');
const sidebar = $('#sidebar');
const menuBtn = $('#menuBtn');
const sidebarOverlay = $('#sidebarOverlay');
const closeSidebarBtn = $('#closeSidebarBtn');

// ──────── API ────────
const API_BASE = window.location.origin;

async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    };

    try {
        const response = await fetch(url, config);
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        return await response.json();
    } catch (err) {
        console.error(`API Error [${endpoint}]:`, err);
        throw err;
    }
}

// ──────── Chat Logic ────────
async function sendMessage(text) {
    if (!text.trim() || state.isLoading) return;

    state.isLoading = true;
    hideWelcomeScreen();
    updateSendButton();

    // Add user message to UI
    appendMessage('user', text);

    // Clear input
    messageInput.value = '';
    autoResizeTextarea();

    // Show typing indicator
    const typingEl = showTypingIndicator();

    try {
        // Use streaming endpoint
        const response = await fetch(`${API_BASE}/api/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                conversation_id: state.conversationId,
                language: 'auto',
            }),
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        // Remove typing indicator & create empty bot bubble
        typingEl.remove();
        const { bubble, row, timeEl } = createStreamBubble();

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        let meta = {};
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                try {
                    const event = JSON.parse(line.slice(6));

                    if (event.type === 'metadata') {
                        state.conversationId = event.conversation_id;
                        meta = event;
                    } else if (event.type === 'chunk') {
                        fullText += event.content;
                        // Store raw text for copying later
                        bubble.dataset.rawText = fullText;
                        
                        // Update bubble content in real-time
                        const contentEl = bubble.querySelector('.stream-content');
                        contentEl.innerHTML = formatContent(fullText);
                        scrollToBottom();
                    } else if (event.type === 'done') {
                        // Add metadata to bubble
                        addMetaToBubble(bubble, timeEl, meta, event);
                    }
                } catch (e) { /* skip invalid JSON */ }
            }
        }

    } catch (err) {
        typingEl.remove();

        // Fallback: try non-streaming
        try {
            const data = await apiCall('/api/chat/', {
                method: 'POST',
                body: JSON.stringify({
                    message: text,
                    conversation_id: state.conversationId,
                    language: 'auto',
                }),
            });
            state.conversationId = data.conversation_id;
            appendMessage('bot', data.answer, {
                messageId: data.message_id,
                sources: data.sources,
                confidence: data.confidence_score,
                responseTime: data.response_time_ms,
            });
        } catch (fallbackErr) {
            const errorMsg = 'لا يمكن الاتصال بالخادم. تأكد من تشغيل Backend.';
            appendMessage('bot', errorMsg, { isError: true });
        }
    } finally {
        state.isLoading = false;
        updateSendButton();
    }
}

function createStreamBubble() {
    state.messageCount++;

    const row = document.createElement('div');
    row.className = 'message-row bot';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '✨';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    const contentEl = document.createElement('div');
    contentEl.className = 'stream-content';
    bubble.appendChild(contentEl);

    const timeEl = document.createElement('div');
    timeEl.className = 'message-time';
    const now = new Date();
    timeEl.textContent = now.toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' });
    bubble.appendChild(timeEl);

    row.appendChild(avatar);
    row.appendChild(bubble);
    messagesContainer.appendChild(row);
    scrollToBottom();

    return { bubble, row, timeEl };
}

function addMetaToBubble(bubble, timeEl, meta, doneEvent) {
    // Confidence badge
    if (meta.confidence_score !== undefined) {
        const badge = document.createElement('span');
        badge.className = `confidence-badge ${getConfidenceClass(meta.confidence_score)}`;
        badge.textContent = `${Math.round(meta.confidence_score * 100)}% ثقة`;
        timeEl.appendChild(badge);
    }

    // Response time
    if (doneEvent.response_time_ms) {
        const timeSpan = document.createElement('span');
        timeSpan.style.fontSize = '0.68rem';
        timeSpan.textContent = `⚡ ${doneEvent.response_time_ms}ms`;
        timeEl.appendChild(timeSpan);
    }

    // Sources
    // if (meta.sources && meta.sources.length > 0) {
    //     const sourcesEl = createSourcesElement(meta.sources);
    //     bubble.appendChild(sourcesEl);
    // }

    // Feedback and copy buttons
    const actionsContainer = document.createElement('div');
    actionsContainer.className = 'message-actions';

    // Copy button
    const copyBtn = document.createElement('button');
    copyBtn.className = 'action-btn';
    copyBtn.innerHTML = `<svg viewBox="0 0 24 24"><path d="M16 1H4C2.9 1 2 1.9 2 3v14h2V3h12V1zm3 4H8C6.9 5 6 5.9 6 7v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg> نسخ`;
    
    // We get the raw text content by waiting a tiny bit or from a stored attribute.
    // For streaming, we can store fullText in the bubble element itself.
    copyBtn.onclick = () => copyToClipboard(bubble.dataset.rawText || bubble.innerText, copyBtn);
    actionsContainer.appendChild(copyBtn);

    if (doneEvent.message_id) {
        const feedbackEl = createFeedbackElement(doneEvent.message_id);
        actionsContainer.appendChild(feedbackEl);
    }

    bubble.appendChild(actionsContainer);

    scrollToBottom();
}

function startNewChat() {
    state.conversationId = null;
    state.messageCount = 0;

    // Clear messages
    const messages = messagesContainer.querySelectorAll('.message-row, .typing-row');
    messages.forEach(el => el.remove());

    // Show welcome screen
    showWelcomeScreen();

    // Close mobile sidebar
    closeSidebar();

    messageInput.focus();
}

// ──────── UI Rendering ────────
function appendMessage(role, content, meta = {}) {
    state.messageCount++;

    const row = document.createElement('div');
    row.className = `message-row ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : '✨';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    // Format content (basic markdown-like)
    const formattedContent = formatContent(content);
    bubble.innerHTML = formattedContent;

    // Add timestamp
    const timeEl = document.createElement('div');
    timeEl.className = 'message-time';
    const now = new Date();
    timeEl.textContent = now.toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' });

    // Add confidence badge for bot messages
    if (role === 'bot' && meta.confidence !== undefined && !meta.isError) {
        const badge = document.createElement('span');
        badge.className = `confidence-badge ${getConfidenceClass(meta.confidence)}`;
        badge.textContent = `${Math.round(meta.confidence * 100)}% ثقة`;
        timeEl.appendChild(badge);
    }

    // Add response time
    if (meta.responseTime) {
        const timeSpan = document.createElement('span');
        timeSpan.style.fontSize = '0.68rem';
        timeSpan.textContent = `⚡ ${meta.responseTime}ms`;
        timeEl.appendChild(timeSpan);
    }

    bubble.appendChild(timeEl);

    // Add sources
    if (meta.sources && meta.sources.length > 0) {
        const sourcesEl = createSourcesElement(meta.sources);
        bubble.appendChild(sourcesEl);
    }

    // Add feedback buttons and copy button for bot messages
    if (role === 'bot' && !meta.isError) {
        const actionsContainer = document.createElement('div');
        actionsContainer.className = 'message-actions';

        // Copy button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'action-btn';
        copyBtn.innerHTML = `<svg viewBox="0 0 24 24"><path d="M16 1H4C2.9 1 2 1.9 2 3v14h2V3h12V1zm3 4H8C6.9 5 6 5.9 6 7v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg> نسخ`;
        copyBtn.onclick = () => copyToClipboard(content, copyBtn);
        actionsContainer.appendChild(copyBtn);

        // Feedback buttons
        if (meta.messageId) {
            const feedbackEl = createFeedbackElement(meta.messageId);
            // Append the actual feedback buttons, not the container itself to avoid nesting issues if we change structure
            Array.from(feedbackEl.children).forEach(child => actionsContainer.appendChild(child));
        }

        bubble.appendChild(actionsContainer);
    }

    row.appendChild(avatar);
    row.appendChild(bubble);
    messagesContainer.appendChild(row);

    // Scroll to bottom
    scrollToBottom();
}

function formatContent(text) {
    if (!text) return '';

    // Escape HTML first to prevent XSS and broken tags
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Bold: **text**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic: *text*
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Protect Markdown links [text](url) - support http, https, mailto, tel
    const tempLinks = [];
    html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+|mailto:[^\)]+|tel:[^\)]+)\)/g, (match, text, url) => {
        let className = 'chat-link';
        if (url.startsWith('mailto:')) className += ' email-link';
        if (url.startsWith('tel:')) className += ' phone-link';
        
        tempLinks.push(`<a href="${url}" target="_blank" rel="noopener" class="${className}">${text}</a>`);
        return `__LINK_${tempLinks.length - 1}__`;
    });

    // Emails (e.g. info@ust.edu.sd) - only if not already processed
    html = html.replace(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)/g, (match, email) => {
        if (match.includes('__LINK_')) return match;
        tempLinks.push(`<a href="mailto:${email}" class="chat-link email-link">${email}</a>`);
        return `__LINK_${tempLinks.length - 1}__`;
    });

    // Plain URLs - only if not already processed
    html = html.replace(/(https?:\/\/[^\s<]+)/g, (match, url) => {
        if (match.includes('__LINK_')) return match;
        tempLinks.push(`<a href="${url}" target="_blank" rel="noopener" class="chat-link">${url}</a>`);
        return `__LINK_${tempLinks.length - 1}__`;
    });

    // Phone numbers (+249123456789 or 0123456789 or 201206450068) - only if not already processed
    html = html.replace(/(?<!\d|\+)(\+?\d{9,14})(?!\d)/g, (match, phone) => {
        if (match.includes('__LINK_')) return match;
        tempLinks.push(`<a href="tel:${phone}" class="chat-link phone-link" dir="ltr">${phone}</a>`);
        return `__LINK_${tempLinks.length - 1}__`;
    });

    // Restore all links from placeholders
    html = html.replace(/__LINK_(\d+)__/g, (match, index) => tempLinks[parseInt(index, 10)]);

    // Numbered lists
    html = html.replace(/^(\d+)\.\s+(.+)$/gm, '<div class="list-item"><span class="list-number">$1.</span> $2</div>');
    
    // Bullet lists
    html = html.replace(/^[\-\*]\s+(.+)$/gm, '<div class="list-item"><span class="list-bullet">•</span> $1</div>');

    // Line breaks
    html = html.replace(/\n/g, '<br>');

    return html;
}

function copyToClipboard(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
        const originalHtml = btn.innerHTML;
        btn.innerHTML = `<svg viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg> تم النسخ`;
        btn.style.color = 'var(--success)';
        setTimeout(() => {
            btn.innerHTML = originalHtml;
            btn.style.color = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}

function createSourcesElement(sources) {
    const container = document.createElement('div');
    container.className = 'message-sources';

    const label = document.createElement('div');
    label.className = 'sources-label';
    label.innerHTML = '📚 المصادر | Sources';
    container.appendChild(label);

    sources.slice(0, 3).forEach((src, i) => {
        const item = document.createElement('div');
        item.className = 'source-item';
        item.textContent = `${i + 1}. ${src.source} (${Math.round(src.relevance_score * 100)}%)`;
        container.appendChild(item);
    });

    return container;
}

function createFeedbackElement(messageId) {
    const wrapper = document.createElement('div');
    wrapper.style.display = 'flex';
    wrapper.style.flexDirection = 'column';
    wrapper.style.gap = '8px';
    wrapper.style.alignItems = 'flex-start';
    wrapper.style.marginTop = '10px';
    wrapper.style.width = '100%';

    const container = document.createElement('div');
    container.className = 'message-feedback';

    const label = document.createElement('span');
    label.style.fontSize = '0.72rem';
    label.style.color = 'var(--text-tertiary)';
    label.textContent = 'هل أفادتك الإجابة؟';
    container.appendChild(label);

    const commentBox = document.createElement('div');
    commentBox.className = 'feedback-comment-box';
    commentBox.style.display = 'none';
    commentBox.style.flexDirection = 'column';
    commentBox.style.gap = '10px';
    commentBox.style.width = '100%';
    commentBox.style.maxWidth = '350px';
    commentBox.style.background = 'rgba(0,0,0,0.2)';
    commentBox.style.padding = '12px';
    commentBox.style.borderRadius = '12px';
    commentBox.style.border = '1px solid var(--border-color)';
    commentBox.innerHTML = `
        <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 2px;">نأسف لذلك، كيف يمكننا تحسين الإجابة؟</div>
        <textarea placeholder="اكتب ملاحظاتك هنا... (اختياري)" style="width: 100%; min-height: 70px; padding: 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); background: var(--bg-panel); color: var(--text-primary); font-family: inherit; resize: none; font-size: 0.85rem; outline: none;"></textarea>
        <button style="align-self: flex-end; background: var(--primary-color); color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer; font-family: inherit; font-size: 0.8rem; font-weight: 600; transition: opacity 0.2s;">إرسال التقييم</button>
    `;

    const thumbsUp = document.createElement('button');
    thumbsUp.className = 'feedback-btn';
    thumbsUp.innerHTML = '👍';
    thumbsUp.title = 'مفيدة';
    thumbsUp.onclick = () => {
        submitFeedback(messageId, 5, null, thumbsUp, thumbsDown);
        wrapper.innerHTML = '<span style="color:var(--success); font-size:0.8rem; display:flex; align-items:center; gap:5px;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/></svg> شكراً على تقييمك الإيجابي!</span>';
    };
    container.appendChild(thumbsUp);

    const thumbsDown = document.createElement('button');
    thumbsDown.className = 'feedback-btn';
    thumbsDown.innerHTML = '👎';
    thumbsDown.title = 'غير مفيدة';
    thumbsDown.onclick = () => {
        container.style.display = 'none'; // Hide buttons completely
        commentBox.style.display = 'flex'; // Show comment box
    };
    container.appendChild(thumbsDown);

    const submitBtn = commentBox.querySelector('button');
    const textarea = commentBox.querySelector('textarea');
    submitBtn.onclick = () => {
        const comment = textarea.value.trim();
        submitFeedback(messageId, 1, comment, thumbsDown, thumbsUp);
        wrapper.innerHTML = '<span style="color:var(--success); font-size:0.8rem; display:flex; align-items:center; gap:5px;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/></svg> تم إرسال ملاحظاتك، شكراً لك!</span>';
    };

    wrapper.appendChild(container);
    wrapper.appendChild(commentBox);

    return wrapper;
}

async function submitFeedback(messageId, rating, comment, activeBtn, otherBtn) {
    try {
        await apiCall('/api/chat/feedback', {
            method: 'POST',
            body: JSON.stringify({ message_id: messageId, rating, comment }),
        });
        activeBtn.classList.add('active');
        otherBtn.classList.remove('active');
        activeBtn.disabled = true;
        otherBtn.disabled = true;
    } catch (err) {
        console.error('Feedback error:', err);
    }
}

function showTypingIndicator() {
    const row = document.createElement('div');
    row.className = 'message-row bot typing-row';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '✨';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    const typing = document.createElement('div');
    typing.className = 'typing-indicator';
    typing.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
    bubble.appendChild(typing);

    row.appendChild(avatar);
    row.appendChild(bubble);
    messagesContainer.appendChild(row);

    scrollToBottom();
    return row;
}

function getConfidenceClass(score) {
    if (score >= 0.7) return 'confidence-high';
    if (score >= 0.4) return 'confidence-medium';
    return 'confidence-low';
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    });
}

function hideWelcomeScreen() {
    if (welcomeScreen) {
        welcomeScreen.style.display = 'none';
    }
}

function showWelcomeScreen() {
    if (welcomeScreen) {
        welcomeScreen.style.display = 'flex';
    }
}

// ──────── Input Handling ────────
function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
}

function updateSendButton() {
    const hasText = messageInput.value.trim().length > 0;
    sendBtn.disabled = !hasText || state.isLoading;
}

// ──────── Theme ────────
function setTheme(theme) {
    state.theme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('ust-theme', theme);
}

function toggleTheme() {
    const newTheme = state.theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

// ──────── Sidebar (Mobile) ────────
function openSidebar() {
    sidebar.classList.add('open');
    sidebarOverlay.classList.add('active');
}

function closeSidebar() {
    sidebar.classList.remove('open');
    sidebarOverlay.classList.remove('active');
}

// ──────── Background Particles ────────
function createParticles() {
    const container = document.getElementById('bgParticles');
    if (!container) return;

    const colors = ['#3b82f6', '#a855f7', '#60a5fa', '#c084fc'];

    for (let i = 0; i < 12; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        const size = Math.random() * 150 + 50;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;
        particle.style.background = colors[Math.floor(Math.random() * colors.length)];
        particle.style.animationDuration = `${Math.random() * 15 + 15}s`;
        particle.style.animationDelay = `${Math.random() * 5}s`;
        container.appendChild(particle);
    }
}

// ──────── Event Listeners ────────
function initEventListeners() {
    // Send message
    sendBtn.addEventListener('click', () => sendMessage(messageInput.value));

    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(messageInput.value);
        }
    });

    messageInput.addEventListener('input', () => {
        autoResizeTextarea();
        updateSendButton();
    });

    // New chat
    newChatBtn.addEventListener('click', startNewChat);
    newChatBtnMobile.addEventListener('click', startNewChat);

    // Theme toggle
    themeToggle.addEventListener('click', toggleTheme);

    // Mobile sidebar
    menuBtn.addEventListener('click', openSidebar);
    sidebarOverlay.addEventListener('click', closeSidebar);
    if (closeSidebarBtn) {
        closeSidebarBtn.addEventListener('click', closeSidebar);
    }

    // Suggestion chips
    $$('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const question = chip.getAttribute('data-question');
            if (question) {
                messageInput.value = question;
                sendMessage(question);
            }
        });
    });
}

// ──────── Initialize ────────
function init() {
    setTheme(state.theme);
    createParticles();
    initEventListeners();
    updateSendButton();

    // Restore conversation from localStorage
    const savedConvId = localStorage.getItem('ust-conversation-id');
    if (savedConvId) {
        state.conversationId = savedConvId;
    }

    // Focus input
    messageInput.focus();

    console.log('🎓 UST Smart Chatbot initialized');
    console.log('📡 API Base:', API_BASE);
}

// Start app
document.addEventListener('DOMContentLoaded', init);
