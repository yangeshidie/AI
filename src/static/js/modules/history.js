import { appendMessage } from '../utils.js';
import { state, setSessionFile, clearHistory, pushToHistory, setCurrentKB } from '../state.js';
import { startNewChat } from './chat.js';

export function toggleHistory() {
    document.getElementById('historyDrawer').classList.toggle('open');
    loadHistoryList();
}

export async function loadHistoryList() {
    const container = document.getElementById('historyListContent');
    try {
        const res = await fetch('/api/history/list');
        const data = await res.json();
        container.innerHTML = '';
        for (const [date, files] of Object.entries(data)) {
            const dateHeader = document.createElement('div');
            dateHeader.className = 'history-date-header';
            dateHeader.innerText = date;
            container.appendChild(dateHeader);

            files.forEach(file => {
                const fullPath = `${date}/${file}`;
                const displayName = file.replace('.json', '');

                const item = document.createElement('div');
                item.className = 'history-item-row';
                item.innerHTML = `
                    <div class="h-name" onclick="window.loadSession('${fullPath}')">
                        <span class="material-symbols-outlined">chat_bubble_outline</span>
                        <span>${displayName}</span>
                    </div>
                    <div class="h-actions">
                        <button onclick="window.renameHistory('${fullPath}', '${displayName}')"><span class="material-symbols-outlined">edit</span></button>
                        <button onclick="window.deleteHistory('${fullPath}')" style="color:#ef4444;"><span class="material-symbols-outlined">delete</span></button>
                    </div>
                `;
                container.appendChild(item);
            });
        }
    } catch (e) { console.error(e); }
}

export async function loadSession(filepath) {
    try {
        const res = await fetch('/api/history/load', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filepath: filepath })
        });
        const historyData = await res.json();

        // 恢复状态
        clearHistory();
        historyData.messages.forEach(msg => pushToHistory(msg));
        setSessionFile(filepath);

        // UI 恢复
        document.getElementById('chatBox').innerHTML = '';
        state.conversationHistory.forEach(msg => appendMessage(msg.role, msg.content, false, msg.id));

        // 恢复智能体状态
        if (historyData.kb_id) {
            const kbInfo = await getKBInfo(historyData.kb_id);
            if (kbInfo) {
                setCurrentKB(kbInfo);
                document.getElementById('chat-title').innerText = kbInfo.name;
                document.getElementById('chat-subtitle').innerText = "📚 知识库模式已激活";
                document.getElementById('chat-mode-icon').innerText = "smart_toy";
                document.getElementById('chat-mode-icon').style.color = "var(--accent)";
            } else {
                setCurrentKB(null);
                document.getElementById('chat-title').innerText = "History Session";
                document.getElementById('chat-subtitle').innerText = filepath;
                document.getElementById('chat-mode-icon').innerText = "chat_bubble";
                document.getElementById('chat-mode-icon').style.color = "var(--text-sub)";
            }
        } else {
            setCurrentKB(null);
            document.getElementById('chat-title').innerText = "History Session";
            document.getElementById('chat-subtitle').innerText = filepath;
            document.getElementById('chat-mode-icon').innerText = "chat_bubble";
            document.getElementById('chat-mode-icon').style.color = "var(--text-sub)";
        }

        document.getElementById('historyDrawer').classList.remove('open');

    } catch (e) { alert("加载失败: " + e); }
}

async function getKBInfo(kbId) {
    try {
        const res = await fetch('/api/kb/list');
        const data = await res.json();
        return data.kbs.find(kb => kb.id === kbId);
    } catch (e) {
        console.error('获取知识库信息失败:', e);
        return null;
    }
}

export async function renameHistory(fullPath, oldName) {
    const newName = prompt("重命名会话:", oldName);
    if (!newName || newName === oldName) return;
    try {
        await fetch('/api/history/rename', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: fullPath, new_name: newName })
        });
        loadHistoryList();
    } catch (e) { alert("失败: " + e); }
}

export async function deleteHistory(fullPath) {
    if (!confirm("确定删除此会话记录？")) return;
    try {
        await fetch('/api/history/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: fullPath })
        });
        loadHistoryList();
        if (state.currentSessionFile && state.currentSessionFile.includes(fullPath.split('/')[1])) {
            startNewChat();
        }
    } catch (e) { alert("失败: " + e); }
}