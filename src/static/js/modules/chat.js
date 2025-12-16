import { state, setSessionFile, setCurrentKB, clearHistory, pushToHistory, setConfig } from '../state.js';
import { appendMessage } from '../utils.js';
import { loadHistoryList } from './history.js'; // 循环依赖注意：这里只用于发送后刷新列表
//import { sendMessage, startNewChat, fetchModels, saveConfig, loadConfig, updateConfigFromUI } from './chat.js';
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

export async function sendMessage() {
    updateConfigFromUI();
    const input = document.getElementById('userInput');
    const msg = input.value.trim();
    if (!msg) return;

    appendMessage('user', msg);
    input.value = '';
    pushToHistory({role: 'user', content: msg});

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
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        loadingDiv.remove();

        if (data.content) {
            appendMessage('assistant', data.content);
            pushToHistory(data);
            // 刷新历史列表
            loadHistoryList();
        } else {
            appendMessage('system', 'Error: 无内容返回');
        }
    } catch (e) {
        loadingDiv.innerText = "Error: " + e;
    }
}

export async function fetchModels() {
    updateConfigFromUI();
    const select = document.getElementById('modelSelect');
    select.innerHTML = '<option>Loading...</option>';
    try {
        const res = await fetch('/api/models', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
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
    } catch(e) { console.error("Load Models Failed", e); }
}


export function initChatListeners() {
    const input = document.getElementById('userInput');
    if (input) {
        // 先移除旧的监听器，防止重复绑定 (虽然 DOMContentLoaded 只跑一次，但好习惯)
        const newClone = input.cloneNode(true);
        input.parentNode.replaceChild(newClone, input);

        newClone.addEventListener('keydown', function (e) {
            // 检查 Ctrl 或 Command (Mac) + Enter
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault(); // 阻止默认换行
                console.log("Ctrl+Enter detected"); // 调试用
                sendMessage();
            }
        });

        // 顺便重新绑定一下 ID，防止引用丢失
        // 注意：因为克隆了节点，需要更新外部对 userInput 的引用，
        // 但由于我们在 sendMessage 里是现取 document.getElementById('userInput')，所以没影响。
    }
}
// 暴露给设置保存按钮
export function saveConfig() {
    updateConfigFromUI();
    alert("配置已更新 (仅本次会话有效)");
}