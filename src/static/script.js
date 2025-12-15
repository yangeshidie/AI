let conversationHistory = [];
let currentConfig = { apiUrl: "", apiKey: "", model: "" };
let currentSessionFile = "";

document.addEventListener('DOMContentLoaded', () => {
    init();
    marked.setOptions({
        highlight: function(code, lang) {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        },
        langPrefix: 'hljs language-'
    });
});

async function init() {
    try {
        const res = await fetch('/api/config');
        const config = await res.json();
        document.getElementById('apiUrl').value = config.api_url;
        document.getElementById('apiKey').value = config.api_key;

        const select = document.getElementById('modelSelect');
        select.innerHTML = `<option value="${config.model}">${config.model} (默认)</option>`;

        updateConfigFromUI();
        loadHistoryList();
        startNewChat();
    } catch (e) { console.error(e); }
}

async function uploadToRag() {
    const fileInput = document.getElementById('ragInput');
    const file = fileInput.files[0];
    const btn = document.querySelector('#panel-knowledge .action-btn');
    const statusDiv = document.getElementById('ragStatus');

    if (!file) { alert("请先选择一个文件！"); return; }

    const originalBtnText = btn.innerText;
    btn.innerText = "⏳ 正在索引...";
    btn.disabled = true;

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch('/api/rag/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (res.ok) {
            statusDiv.innerHTML = `
                <p style="color: #4caf50;">✅ 上传成功！</p>
                <p>文件: <strong>${data.filename}</strong></p>
                <p>索引片段: <strong>${data.chunks_added}</strong></p>
            `;
            fileInput.value = '';
        } else { throw new Error(data.detail); }
    } catch (e) {
        statusDiv.innerHTML = `<p style="color: #ff5555;">❌ 错误: ${e.message}</p>`;
    } finally {
        btn.innerText = originalBtnText;
        btn.disabled = false;
    }
}

async function sendMessage() {
    updateConfigFromUI();
    const input = document.getElementById('userInput');
    const msg = input.value.trim();
    if (!msg) return;

    appendMessage('user', msg);
    input.value = '';
    conversationHistory.push({role: 'user', content: msg});

    // 这里不再提示 Searching，因为是后台静默完成的
    const loadingDiv = appendMessage('assistant', 'Thinking...', true);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                api_url: currentConfig.apiUrl,
                api_key: currentConfig.apiKey,
                model: currentConfig.model,
                messages: conversationHistory,
                session_file: currentSessionFile
            })
        });

        const data = await response.json();
        loadingDiv.remove();

        if (data.content) {
            appendMessage('assistant', data.content);
            conversationHistory.push(data);
            loadHistoryList();
        } else {
            appendMessage('system', 'API Error: 无内容返回');
        }
    } catch (e) {
        loadingDiv.innerText = "Error: " + e;
    }
}

function startNewChat() {
    const now = new Date();
    const timestamp = now.toISOString().replace(/[-:T.]/g, '').slice(0, 14);
    currentSessionFile = `data_${timestamp}.json`;
    conversationHistory = [{role: "system", content: "你是一个乐于助人的AI助手。"}];
    document.getElementById('chatBox').innerHTML = '';
    appendMessage('system', '新会话已开始');
    document.getElementById('chatTitle').innerText = currentSessionFile;
}

function clearChat() {
    if (!confirm("确定清空？")) return;
    conversationHistory = [{role: "system", content: "你是一个乐于助人的AI助手。"}];
    document.getElementById('chatBox').innerHTML = '<div class="message system">记忆已重置</div>';
}

function appendMessage(role, text, raw = false) {
    const chatBox = document.getElementById('chatBox');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    if (role === 'system' || raw) {
        div.innerText = text;
    } else {
        div.innerHTML = marked.parse(text);
        div.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div;
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const openBtn = document.getElementById('sidebarOpenBtn');
    if (sidebar.classList.contains('collapsed')) {
        sidebar.classList.remove('collapsed');
        openBtn.style.display = 'none';
    } else {
        sidebar.classList.add('collapsed');
        openBtn.style.display = 'block';
    }
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    document.querySelectorAll('.panel').forEach(panel => panel.classList.remove('active'));
    document.getElementById(`panel-${tabName}`).classList.add('active');
}

function updateConfigFromUI() {
    currentConfig.apiUrl = document.getElementById('apiUrl').value;
    currentConfig.apiKey = document.getElementById('apiKey').value;
    currentConfig.model = document.getElementById('modelSelect').value;
}

async function loadHistoryList() {
    const container = document.getElementById('history-list');
    try {
        const res = await fetch('/api/history/list');
        const data = await res.json();
        container.innerHTML = '';
        for (const [date, files] of Object.entries(data)) {
            const dateHeader = document.createElement('div');
            dateHeader.className = 'history-date';
            dateHeader.innerText = `📅 ${date}`;
            container.appendChild(dateHeader);
            files.forEach(file => {
                const item = document.createElement('div');
                item.className = 'history-item';
                item.innerHTML = `<span>💬</span> ${file.replace('.json', '')}`;
                item.onclick = () => loadSession(date + '/' + file);
                container.appendChild(item);
            });
        }
    } catch (e) { console.error(e); }
}

async function loadSession(filepath) {
    try {
        const res = await fetch('/api/history/load', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ filepath: filepath })
        });
        const historyData = await res.json();
        conversationHistory = historyData;
        currentSessionFile = filepath.split('/').pop();
        document.getElementById('chatBox').innerHTML = '';
        conversationHistory.forEach(msg => appendMessage(msg.role, msg.content));
        document.getElementById('chatTitle').innerText = currentSessionFile;
    } catch (e) { alert("加载失败: " + e); }
}

async function handleImportHistory(input) {
    const file = input.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    try {
        const res = await fetch('/api/history/upload', {method: 'POST', body: formData});
        const data = await res.json();
        conversationHistory = data;
        currentSessionFile = file.name;
        document.getElementById('chatBox').innerHTML = '';
        conversationHistory.forEach(msg => appendMessage(msg.role, msg.content));
        document.getElementById('chatTitle').innerText = "已导入: " + file.name;
        input.value = '';
    } catch (e) { alert("导入失败: " + e); }
}

async function fetchModels() {
    updateConfigFromUI();
    const select = document.getElementById('modelSelect');
    select.innerHTML = '<option>加载中...</option>';
    try {
        const res = await fetch('/api/models', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ api_url: currentConfig.apiUrl, api_key: currentConfig.apiKey })
        });
        const data = await res.json();
        if (data.models) {
            select.innerHTML = '';
            data.models.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m; opt.innerText = m;
                select.appendChild(opt);
            });
        }
    } catch (e) { alert("获取失败"); }
}

document.getElementById('userInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter' && e.ctrlKey) { sendMessage(); }
});