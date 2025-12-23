import { state, setConfig, setSessionFile, clearHistory, setCurrentKB, pushToHistory } from '../state.js';
import { appendMessage } from '../utils.js';
import { loadHistoryList } from './history.js';

export let currentAttachments = [];

export function updateConfigFromUI() {
    const newConfig = {
        apiUrl: document.getElementById('apiUrl').value,
        apiKey: document.getElementById('apiKey').value,
        model: document.getElementById('modelSelect').value
    };
    setConfig(newConfig);
}

export function startNewChat(resetUI = true) {
    const now = new Date();
    setSessionFile(`chat_${now.getTime()}.json`);
    clearHistory();
    document.getElementById('chatBox').innerHTML = '';

    if (resetUI) {
        setCurrentKB(null);
        document.getElementById('chat-title').innerText = "General Chat";
        document.getElementById('chat-subtitle').innerText = "无知识库挂载";
        document.getElementById('chat-mode-icon').innerText = "chat_bubble";
        document.getElementById('chat-mode-icon').style.color = "var(--text-sub)";
        appendMessage('system', '新对话已开始 (普通模式)');
    }
}

export async function sendMessage() {
    updateConfigFromUI();
    const input = document.getElementById('userInput');
    const msgText = input.value.trim();

    if (!msgText && currentAttachments.length === 0) return;

    // 构建消息内容
    let messageContent;

    if (currentAttachments.length > 0) {
        messageContent = [];
        if (msgText) {
            messageContent.push({ type: "text", text: msgText });
        } else if (currentAttachments.length > 0 && !msgText) {
            messageContent.push({ type: "text", text: "Sent attachments." });
        }

        currentAttachments.forEach(att => {
            if (att.type === 'image') {
                messageContent.push({
                    type: "image_url",
                    image_url: { url: att.base64 }
                });
            } else {
                messageContent.push({
                    type: "text",
                    text: `[Attached ${att.type}: ${att.name}]`
                });
            }
        });
    } else {
        messageContent = msgText;
    }

    // UI Display logic
    let uiContent = msgText;
    if (currentAttachments.length > 0) {
        const images = currentAttachments.filter(a => a.type === 'image').map(a => `<br><img src="${a.base64}" style="max-width: 200px; border-radius: 8px; margin-top: 5px;">`).join('');
        const others = currentAttachments.filter(a => a.type !== 'image').map(a => `<br>[${a.type}: ${a.name}]`).join('');
        uiContent = (uiContent || '') + images + others;
    }

    appendMessage('user', uiContent);

    input.value = '';
    clearMediaSelection();

    pushToHistory({ role: 'user', content: messageContent });

    const loadingDiv = appendMessage('assistant', 'Thinking...', true);

    try {
        const payload = {
            api_url: state.config.apiUrl,
            api_key: state.config.apiKey,
            model: state.config.model,
            messages: state.conversationHistory,
            session_file: state.currentSessionFile,
            kb_id: state.currentKB ? state.currentKB.id : null
        };

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        loadingDiv.remove();

        if (data.content) {
            const contentDiv = appendMessage('assistant', data.content);
            addDetachButton(contentDiv.parentElement, data.content);
            pushToHistory(data);
            loadHistoryList();
        } else {
            appendMessage('system', 'Error: 无内容返回');
        }
    } catch (e) {
        if (loadingDiv) loadingDiv.innerText = "Error: " + e;
    }
}

function addDetachButton(messageWrapper, content) {
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'bubble-actions';

    const detachBtn = document.createElement('button');
    detachBtn.className = 'bubble-btn';
    detachBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px">open_in_new</span> Detach';
    detachBtn.onclick = () => detachBubble(content);

    actionsDiv.appendChild(detachBtn);
    messageWrapper.appendChild(actionsDiv);
}

// === 悬浮气泡逻辑 ===
function detachBubble(contentHtml) {
    const container = document.getElementById('floating-container');
    const bubbleId = 'bubble-' + Date.now();

    const bubble = document.createElement('div');
    bubble.className = 'floating-bubble';
    bubble.id = bubbleId;
    bubble.style.left = '100px';
    bubble.style.top = '100px';

    bubble.innerHTML = `
    <div class="floating-header" id="${bubbleId}-header">
        <span class="floating-title">Floating Response</span>
        <button class="floating-close" onclick="document.getElementById('${bubbleId}').remove()">×</button>
    </div>
    <div class="floating-content markdown-body">
        ${marked.parse(contentHtml)}
    </div>
`;

    container.appendChild(bubble);

    bubble.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });

    if (typeof renderMathInElement === 'function') {
        renderMathInElement(bubble.querySelector('.floating-content'), {
            delimiters: [
                { left: '$$', right: '$$', display: true },
                { left: '$', right: '$', display: false },
                { left: '\\[', right: '\\]', display: true },
                { left: '\\(', right: '\\)', display: false }
            ],
            throwOnError: false
        });
    }

    makeDraggable(bubble, document.getElementById(`${bubbleId}-header`));
}

function makeDraggable(element, handle) {
    let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    handle.onmousedown = dragMouseDown;

    function dragMouseDown(e) {
        e = e || window.event;
        e.preventDefault();
        pos3 = e.clientX;
        pos4 = e.clientY;
        document.onmouseup = closeDragElement;
        document.onmousemove = elementDrag;
    }

    function elementDrag(e) {
        e = e || window.event;
        e.preventDefault();
        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;
        element.style.top = (element.offsetTop - pos2) + "px";
        element.style.left = (element.offsetLeft - pos1) + "px";
    }

    function closeDragElement() {
        document.onmouseup = null;
        document.onmousemove = null;
    }
}

export async function fetchModels() {
    updateConfigFromUI();
    const select = document.getElementById('modelSelect');
    select.innerHTML = '<option>Loading...</option>';
    try {
        const res = await fetch('/api/models', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                base_url: state.config.apiUrl,
                api_url: state.config.apiUrl,
                api_key: state.config.apiKey
            })
        });
        const data = await res.json();
        select.innerHTML = '';
        data.models.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m; opt.innerText = m;
            select.appendChild(opt);
        });
        document.getElementById('current-model-display').innerText = "Model: " + select.value;
        select.addEventListener('change', function () {
            document.getElementById('current-model-display').innerText = "Model: " + this.value;
        });
    } catch (e) { console.error("Load Models Failed", e); }
}

export function initChatListeners() {
    const input = document.getElementById('userInput');
    if (input) {
        const newClone = input.cloneNode(true);
        input.parentNode.replaceChild(newClone, input);

        newClone.addEventListener('keydown', function (e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                console.log("Ctrl+Enter detected");
                sendMessage();
            }
        });
    }
}

export function saveConfig() {
    updateConfigFromUI();
    alert("配置已更新 (仅本次会话有效)");
}

export function loadConfig() {
    updateConfigFromUI();
}

export function handleFileSelect(input, type) {
    const files = input.files;
    if (!files.length) return;

    const file = files[0];
    const reader = new FileReader();

    reader.onload = function (e) {
        const base64 = e.target.result;
        currentAttachments.push({
            type: type,
            name: file.name,
            base64: base64
        });
        updateMediaPreview();
    };

    reader.readAsDataURL(file);
    input.value = ''; // Reset input
}

export function clearMediaSelection() {
    currentAttachments = [];
    updateMediaPreview();
}

function updateMediaPreview() {
    const previewArea = document.getElementById('mediaPreviewArea');
    const contentDiv = document.getElementById('mediaPreviewContent');

    if (currentAttachments.length === 0) {
        previewArea.style.display = 'none';
        contentDiv.innerHTML = '';
        return;
    }

    previewArea.style.display = 'block';
    contentDiv.innerHTML = currentAttachments.map(att => {
        if (att.type === 'image') {
            return `<img src="${att.base64}" style="height: 60px; border-radius: 4px; margin-right: 5px;">`;
        } else {
            return `<span style="display:inline-block; padding: 5px 10px; background: #333; border-radius: 4px; margin-right: 5px; font-size: 12px;">[${att.type}] ${att.name}</span>`;
        }
    }).join('');
}