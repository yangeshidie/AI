import { state, setConfig, setSessionFile, clearHistory, setCurrentKB, pushToHistory, setDrawingWorkspaceEnabled, addDrawingWorkspaceImage, removeDrawingWorkspaceImage, clearDrawingWorkspaceImages } from '../state.js';
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

export function toggleStream() {
    state.streamEnabled = !state.streamEnabled;
    const btn = document.getElementById('streamToggleBtn');
    const icon = document.getElementById('streamIcon');
    const text = document.getElementById('streamText');
    
    if (state.streamEnabled) {
        btn.style.background = '#22c55e';
        btn.style.color = 'white';
        icon.innerText = 'check_circle';
        text.innerText = '开启';
    } else {
        btn.style.background = '';
        btn.style.color = '';
        icon.innerText = 'block';
        text.innerText = '关闭';
    }
}

export function toggleDrawingWorkspace() {
    state.drawingWorkspaceEnabled = !state.drawingWorkspaceEnabled;
    const btn = document.getElementById('drawingWorkspaceToggleBtn');
    const icon = document.getElementById('drawingWorkspaceIcon');
    const text = document.getElementById('drawingWorkspaceText');
    
    if (state.drawingWorkspaceEnabled) {
        btn.style.background = '#667eea';
        btn.style.color = 'white';
        icon.innerText = 'check_circle';
        text.innerText = '开启';
        setDrawingWorkspaceEnabled(true);
        document.getElementById('drawingWorkspacePanel').style.display = 'block';
        appendMessage('system', '绘图工作区已启用 - 对话将不保存历史记录');
    } else {
        btn.style.background = '';
        btn.style.color = '';
        icon.innerText = 'block';
        text.innerText = '关闭';
        setDrawingWorkspaceEnabled(false);
        document.getElementById('drawingWorkspacePanel').style.display = 'none';
        appendMessage('system', '绘图工作区已关闭');
    }
}

export function startNewChat(resetUI = true) {
    const now = new Date();
    const dateStr = now.toISOString().split('T')[0];
    setSessionFile(`${dateStr}/chat_${now.getTime()}.json`);
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

    if (!msgText && currentAttachments.length === 0 && state.drawingWorkspaceImages.length === 0) return;

    let messageContent;

    if (currentAttachments.length > 0 || state.drawingWorkspaceImages.length > 0) {
        messageContent = [];
        if (msgText) {
            messageContent.push({ type: "text", text: msgText });
        } else if (currentAttachments.length > 0 || state.drawingWorkspaceImages.length > 0) {
            messageContent.push({ type: "text", text: "Sent attachments." });
        }

        state.drawingWorkspaceImages.forEach(img => {
            messageContent.push({
                type: "image_url",
                image_url: { url: img.base64 }
            });
        });

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

    let uiContent = msgText;
    if (currentAttachments.length > 0 || state.drawingWorkspaceImages.length > 0) {
        const workspaceImages = state.drawingWorkspaceImages.map(a => `<br><img src="${a.base64}" style="max-width: 200px; border-radius: 8px; margin-top: 5px;">`).join('');
        const images = currentAttachments.filter(a => a.type === 'image').map(a => `<br><img src="${a.base64}" style="max-width: 200px; border-radius: 8px; margin-top: 5px;">`).join('');
        const others = currentAttachments.filter(a => a.type !== 'image').map(a => `<br>[${a.type}: ${a.name}]`).join('');
        uiContent = (uiContent || '') + workspaceImages + images + others;
    }

    input.value = '';
    clearMediaSelection();

    const userMsg = { role: 'user', content: messageContent };
    
    if (state.drawingWorkspaceEnabled) {
        pushToHistory(userMsg);
        appendMessage('user', uiContent, false, userMsg.id);
    } else {
        pushToHistory(userMsg);
        appendMessage('user', uiContent, false, userMsg.id);

        if (!state.currentSessionFile) {
            const now = new Date();
            const dateStr = now.toISOString().split('T')[0];
            setSessionFile(`${dateStr}/chat_${now.getTime()}.json`);
        }
    }

    const payload = {
        api_url: state.config.apiUrl,
        api_key: state.config.apiKey,
        model: state.config.model,
        messages: state.drawingWorkspaceEnabled ? [userMsg] : state.conversationHistory,
        session_file: state.drawingWorkspaceEnabled ? null : state.currentSessionFile,
        kb_id: state.currentKB ? state.currentKB.id : null,
        stream: state.streamEnabled,
        drawing_workspace_mode: state.drawingWorkspaceEnabled
    };

    if (state.streamEnabled) {
        await sendStreamMessage(payload);
    } else {
        await sendNonStreamMessage(payload);
    }
}

async function sendStreamMessage(payload) {
    const loadingDiv = appendMessage('assistant', 'Thinking...', true);
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content markdown-body';
    loadingDiv.appendChild(contentDiv);
    
    let fullContent = '';

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json();
            const errorMsg = errorData.detail || errorData.error || `HTTP ${response.status}: ${response.statusText}`;
            loadingDiv.remove();
            appendMessage('system', `Error: ${errorMsg}`);
            console.error('API Error:', errorData);
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.slice(6);
                    try {
                        const data = JSON.parse(dataStr);
                        
                        if (data.error) {
                            loadingDiv.remove();
                            appendMessage('system', `Error: ${data.error}`);
                            console.error('Stream Error:', data.error);
                            return;
                        }

                        if (data.content) {
                            fullContent += data.content;
                            contentDiv.innerHTML = marked.parse(fullContent);
                            
                            contentDiv.querySelectorAll('pre code').forEach((block) => {
                                hljs.highlightElement(block);
                            });
                        }

                        if (data.done) {
                            loadingDiv.remove();
                            const assistantMsg = { role: 'assistant', content: data.content };
                            if (data.id) {
                                assistantMsg.id = data.id;
                            }
                            const finalContentDiv = appendMessage('assistant', data.content, false, data.id);
                            addDetachButton(finalContentDiv.parentElement, data.content);
                            
                            if (state.drawingWorkspaceEnabled) {
                                addGeneratedImagesToWorkspace(data.content);
                            }
                            
                            pushToHistory(assistantMsg);
                            loadHistoryList();
                        }
                    } catch (e) {
                        console.error('Parse SSE data failed:', e, dataStr);
                    }
                }
            }
        }
    } catch (e) {
        if (loadingDiv) loadingDiv.innerText = "Error: " + e.message;
        console.error('Stream request failed:', e);
    }
}

async function sendNonStreamMessage(payload) {
    const loadingDiv = appendMessage('assistant', 'Thinking...', true);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        loadingDiv.remove();

        if (!response.ok) {
            const errorMsg = data.detail || data.error || `HTTP ${response.status}: ${response.statusText}`;
            appendMessage('system', `Error: ${errorMsg}`);
            console.error('API Error:', data);
            return;
        }

        if (data.content) {
            const contentDiv = appendMessage('assistant', data.content, false, data.id);
            addDetachButton(contentDiv.parentElement, data.content);
            
            if (state.drawingWorkspaceEnabled) {
                addGeneratedImagesToWorkspace(data.content);
            }
            
            pushToHistory(data);
            loadHistoryList();
        } else {
            appendMessage('system', 'Error: 无内容返回');
            console.error('Invalid response:', data);
        }
    } catch (e) {
        if (loadingDiv) loadingDiv.innerText = "Error: " + e.message;
        console.error('Request failed:', e);
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

export function handleDrawingWorkspaceUpload(input) {
    const files = input.files;
    if (!files.length) return;

    const file = files[0];
    const reader = new FileReader();

    reader.onload = function(e) {
        const base64 = e.target.result;
        try {
            addDrawingWorkspaceImage({ name: file.name, base64: base64 });
            updateDrawingWorkspaceUI();
            appendMessage('system', `图片 "${file.name}" 已添加到绘图工作区`);
        } catch (error) {
            appendMessage('system', error.message);
        }
    };

    reader.readAsDataURL(file);
    input.value = '';
}

export function removeDrawingWorkspaceImageByIndex(index) {
    removeDrawingWorkspaceImage(index);
    updateDrawingWorkspaceUI();
}

export function clearDrawingWorkspace() {
    if (confirm('确定要清空绘图工作区吗？')) {
        clearDrawingWorkspaceImages();
        updateDrawingWorkspaceUI();
        appendMessage('system', '绘图工作区已清空');
    }
}

function updateDrawingWorkspaceUI() {
    const grid = document.getElementById('drawingWorkspaceGrid');
    const count = document.getElementById('drawingWorkspaceCount');
    
    count.innerText = `${state.drawingWorkspaceImages.length}/20`;
    
    grid.innerHTML = state.drawingWorkspaceImages.map((img, index) => `
        <div class="drawing-workspace-item" onclick="window.viewDrawingWorkspaceImage(${index})">
            <img src="${img.base64}" alt="${img.name}" style="width: 100%; height: 100%; object-fit: cover;">
            <button class="drawing-workspace-delete" onclick="event.stopPropagation(); window.removeDrawingWorkspaceImageByIndex(${index})">
                <span class="material-symbols-outlined" style="font-size: 16px;">close</span>
            </button>
        </div>
    `).join('');
}

export function viewDrawingWorkspaceImage(index) {
    const img = state.drawingWorkspaceImages[index];
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); display: flex; justify-content: center; align-items: center; z-index: 9999;';
    modal.innerHTML = `
        <img src="${img.base64}" style="max-width: 90%; max-height: 90%; border-radius: 8px;">
        <button onclick="this.parentElement.remove()" style="position: absolute; top: 20px; right: 20px; background: white; border: none; border-radius: 50%; width: 40px; height: 40px; font-size: 24px; cursor: pointer;">×</button>
    `;
    document.body.appendChild(modal);
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
}

async function addGeneratedImagesToWorkspace(content) {
    const imagePattern = /!\[.*?\]\((\/static\/generated_images\/[^)]+)\)/g;
    const matches = content.matchAll(imagePattern);
    
    for (const match of matches) {
        const imageUrl = match[1];
        try {
            const response = await fetch(imageUrl);
            if (!response.ok) continue;
            
            const blob = await response.blob();
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const base64 = e.target.result;
                const filename = imageUrl.split('/').pop();
                try {
                    addDrawingWorkspaceImage({ name: filename, base64: base64 });
                    updateDrawingWorkspaceUI();
                } catch (error) {
                    console.error('添加生成图片到工作区失败:', error);
                }
            };
            
            reader.readAsDataURL(blob);
        } catch (error) {
            console.error('获取生成图片失败:', error);
        }
    }
}