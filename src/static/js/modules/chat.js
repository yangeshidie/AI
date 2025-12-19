import { state, setSessionFile, setCurrentKB, clearHistory, pushToHistory, setConfig } from '../state.js';
import { appendMessage } from '../utils.js';
import { loadHistoryList } from './history.js';

let currentMedia = {
    type: null, // 'image', 'video', 'audio'
    base64: null,
    mimeType: null
};

export async function loadConfig() {
    try {
        const res = await fetch('/api/config');
        const config = await res.json();
        setConfig(config);
        document.getElementById('apiUrl').value = config.api_url;
        document.getElementById('apiKey').value = config.api_key;
        fetchModels();
    } catch (e) { console.error(e); }
}

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

// === 多模态文件处理逻辑 ===
window.handleFileSelect = function (input, type) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const reader = new FileReader();

        reader.onload = function (e) {
            currentMedia = {
                type: type,
                base64: e.target.result,
                mimeType: file.type
            };

            const previewContent = document.getElementById('mediaPreviewContent');
            previewContent.innerHTML = ''; // Clear previous

            if (type === 'image') {
                previewContent.innerHTML = `<img src="${currentMedia.base64}" style="max-height: 80px; border-radius: 8px; border: 1px solid #444;">`;
            } else if (type === 'video') {
                previewContent.innerHTML = `<video src="${currentMedia.base64}" controls style="max-height: 80px; border-radius: 8px; border: 1px solid #444;"></video>`;
            } else if (type === 'audio') {
                previewContent.innerHTML = `<audio src="${currentMedia.base64}" controls style="height: 40px;"></audio>`;
            }

            document.getElementById('mediaPreviewArea').style.display = 'block';
        };

        reader.readAsDataURL(file);
    }
};

window.clearMediaSelection = function () {
    currentMedia = { type: null, base64: null, mimeType: null };
    document.getElementById('imageInput').value = '';
    document.getElementById('videoInput').value = '';
    document.getElementById('audioInput').value = '';
    document.getElementById('mediaPreviewArea').style.display = 'none';
    document.getElementById('mediaPreviewContent').innerHTML = '';
};

// Backward compatibility for image only (if needed, but we replaced the call in HTML)
window.handleImageSelect = function (input) {
    window.handleFileSelect(input, 'image');
};
window.clearImageSelection = window.clearMediaSelection;

export async function sendMessage() {
    updateConfigFromUI();
    const input = document.getElementById('userInput');
    const msgText = input.value.trim();

    if (!msgText && !currentMedia.base64) return;

    // 构建消息内容 (统一用于 UI 显示和后端发送)
    let messageContent;
    if (currentMedia.base64) {
        messageContent = [
            { type: "text", text: msgText },
            {
                type: "image_url",
                image_url: {
                    url: currentMedia.base64
                }
            }
        ];
    } else {
        messageContent = msgText;
    }

    // 直接传递结构化内容给 UI
    appendMessage('user', messageContent);

    input.value = '';
    window.clearMediaSelection();

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
        loadingDiv.innerText = "Error: " + e;
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
            body: JSON.stringify({ api_url: state.config.apiUrl, api_key: state.config.apiKey })
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