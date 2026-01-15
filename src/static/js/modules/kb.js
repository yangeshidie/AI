import { setCurrentKB } from '../state.js';
import { switchView } from '../router.js';
import { startNewChat } from './chat.js';
import { appendMessage, openModal, closeModal } from '../utils.js';

export async function loadKBList() {
    const grid = document.getElementById('kb-grid');
    if (!grid) return;
    try {
        const res = await fetch('/api/kb/list');
        const data = await res.json();
        grid.innerHTML = '';
        data.kbs.forEach(kb => {
            const card = document.createElement('div');
            card.className = 'kb-card';
            card.innerHTML = `
                <button class="delete-btn" onclick="window.deleteKB('${kb.id}', event)">×</button>
                <button class="edit-btn" onclick="window.showEditKBModal('${kb.id}', event)">✎</button>
                <h4>${kb.name}</h4>
                <p>${kb.description || "暂无描述"}</p>
                <span class="tag">📚 ${kb.files.length} 个文件</span>
            `;
            card.onclick = (e) => {
                if(e.target.className === 'delete-btn' || e.target.className === 'edit-btn') return;
                openKBChat(kb);
            };
            grid.appendChild(card);
        });
    } catch (e) { console.error(e); }
}

export function openKBChat(kb) {
    setCurrentKB(kb);
    switchView('chat');
    document.getElementById('chat-title').innerText = kb.name;
    document.getElementById('chat-subtitle').innerText = "📚 知识库模式已激活";
    document.getElementById('chat-mode-icon').innerText = "smart_toy";
    document.getElementById('chat-mode-icon').style.color = "var(--accent)";

    startNewChat(false);
    appendMessage('system', `已切换到智能体：**${kb.name}**\n包含文件：${kb.files.join(', ')}`);
}

export function showCreateKBModal() {
    openModal('createKBModal');
    // 加载文件选择
    fetch('/api/files/list').then(r => r.json()).then(data => {
        const container = document.getElementById('kbFileSelector');
        container.innerHTML = '';
        data.files.forEach(f => {
            container.innerHTML += `
                <label class="file-option">
                    <input type="checkbox" value="${f.name}">
                    <span>${f.name}</span>
                </label>
            `;
        });
    });
}

export async function submitCreateKB() {
    const name = document.getElementById('kbName').value;
    const desc = document.getElementById('kbDesc').value;
    const checkboxes = document.querySelectorAll('#kbFileSelector input:checked');
    const files = Array.from(checkboxes).map(cb => cb.value);

    if (!name) {
        showToast('warning', '提示', '请输入名称');
        return;
    }

    await fetch('/api/kb/create', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name, description: desc, files})
    });

    closeModal('createKBModal');
    loadKBList();
}

export async function deleteKB(id, event) {
    event.stopPropagation();
    if (!confirm("确定删除此智能体吗？")) return;
    await fetch('/api/kb/delete', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({kb_id: id})
    });
    loadKBList();
}

export function showEditKBModal(id, event) {
    event.stopPropagation();
    const modal = document.getElementById('editKBModal');
    if (!modal) return;
    
    document.getElementById('editKbId').value = id;
    document.getElementById('editKbName').value = '';
    document.getElementById('editKbDesc').value = '';
    
    Promise.all([
        fetch('/api/kb/list').then(r => r.json()),
        fetch('/api/files/list').then(r => r.json())
    ]).then(([kbData, fileData]) => {
        const kb = kbData.kbs.find(k => k.id === id);
        if (kb) {
            document.getElementById('editKbName').value = kb.name;
            document.getElementById('editKbDesc').value = kb.description || '';
            
            const container = document.getElementById('editKbFileSelector');
            container.innerHTML = '';
            fileData.files.forEach(f => {
                const isChecked = kb.files.includes(f.name) ? 'checked' : '';
                container.innerHTML += `
                    <label class="file-option">
                        <input type="checkbox" value="${f.name}" ${isChecked}>
                        <span>${f.name}</span>
                    </label>
                `;
            });
        }
    });
    
    openModal('editKBModal');
}

export async function submitEditKB() {
    const id = document.getElementById('editKbId').value;
    const name = document.getElementById('editKbName').value;
    const desc = document.getElementById('editKbDesc').value;
    const checkboxes = document.querySelectorAll('#editKbFileSelector input:checked');
    const files = Array.from(checkboxes).map(cb => cb.value);

    if (!name) {
        showToast('warning', '提示', '请输入名称');
        return;
    }

    const res = await fetch('/api/kb/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({kb_id: id, name, description: desc, files})
    });

    const data = await res.json();
    if (data.status === 'error') {
        showToast('error', '错误', data.message);
        return;
    }

    closeModal('editKBModal');
    loadKBList();
}