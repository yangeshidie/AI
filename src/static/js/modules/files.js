import { state, setFileToDelete } from '../state.js';
import { openModal, closeModal } from '../utils.js';
import { loadKBList } from './kb.js';

export async function loadRootFiles() {
    const container = document.getElementById('file-library-container');
    if(!container) return;

    try {
        const res = await fetch('/api/files/list');
        const data = await res.json();

        if (data.files.length === 0) {
            container.innerHTML = '<div class="empty-state">暂无文件，请点击右上角上传</div>';
            return;
        }

        // 1. 数据分组
        const groups = {};
        data.files.forEach(f => {
            const gName = f.group || "未分组";
            if (!groups[gName]) groups[gName] = [];
            groups[gName].push(f);
        });

        // 2. 渲染 HTML
        container.innerHTML = '';

        // 遍历每个分组
        for (const [groupName, files] of Object.entries(groups)) {
            // 创建分组容器
            const groupDiv = document.createElement('div');
            groupDiv.className = 'file-group-container';

            // 分组标题
            groupDiv.innerHTML = `
                <div class="group-header">
                    <span class="material-symbols-outlined">folder</span>
                    <h4>${groupName}</h4>
                    <span class="count-badge">${files.length}</span>
                </div>
                <div class="file-grid">
                    <!-- 文件卡片将插在这里 -->
                </div>
            `;

            const grid = groupDiv.querySelector('.file-grid');

            // 渲染该组内的文件
            files.forEach(f => {
                const card = document.createElement('div');
                card.className = 'file-card';
                card.innerHTML = `
                    <div class="f-icon">
                        <span class="material-symbols-outlined">description</span>
                    </div>
                    <div class="f-info">
                        <div class="f-name" title="${f.name}">${f.name}</div>
                        <div class="f-meta">${f.size} • ${f.date}</div>
                    </div>
                    <div class="f-actions">
                        <button onclick="window.changeGroup('${f.name}', '${groupName}')" title="移动分组">
                            <span class="material-symbols-outlined">drive_file_move</span>
                        </button>
                        <button onclick="window.renameFile('${f.name}')" title="重命名">
                            <span class="material-symbols-outlined">edit</span>
                        </button>
                        <button class="danger" onclick="window.tryDeleteFile('${f.name}')" title="删除">
                            <span class="material-symbols-outlined">delete</span>
                        </button>
                    </div>
                `;
                grid.appendChild(card);
            });

            container.appendChild(groupDiv);
        }

    } catch (e) {
        console.error(e);
        container.innerHTML = `<div style="color:red">加载失败: ${e.message}</div>`;
    }
}

export async function changeGroup(filename, oldGroup) {
    const newGroup = prompt("请输入新的分组名称 (例如: 财务, 技术, 未分组):", oldGroup);
    if (!newGroup || newGroup === oldGroup) return;

    try {
        await fetch('/api/files/set_group', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ filename, group: newGroup })
        });
        loadRootFiles();
    } catch(e) { 
        showToast('error', '设置失败', e.message || '未知错误');
    }
}

export async function handleRootUpload(input) {
    const files = input.files;
    if (!files.length) return;
    for (let file of files) {
        const formData = new FormData();
        formData.append("file", file);
        try {
            await fetch('/api/files/upload', {method: 'POST', body: formData});
        } catch (e) { console.error("Upload failed", file.name); }
    }
    input.value = '';
    loadRootFiles();
}

export async function renameFile(oldName) {
    const newName = prompt("请输入新文件名 (带后缀):", oldName);
    if (!newName || newName === oldName) return;
    try {
        const res = await fetch('/api/files/rename', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ filename: oldName, new_name: newName })
        });
        const data = await res.json();
        if(!res.ok) throw new Error(data.detail);
        loadRootFiles();
    } catch(e) { 
        showToast('error', '重命名失败', e.message);
    }
}

export async function tryDeleteFile(filename) {
    setFileToDelete(filename);
    try {
        const res = await fetch('/api/files/delete/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ filename: filename, confirm_delete: false })
        });
        const data = await res.json();

        const warningText = document.getElementById('deleteWarningText');
        const affectedBox = document.getElementById('affectedAgentsList');
        const ul = document.getElementById('affectedListUl');

        warningText.innerText = `确定要永久删除文件 "${filename}" 吗？此操作不可恢复。`;

        if (data.status === 'warning') {
            affectedBox.style.display = 'block';
            ul.innerHTML = data.affected_kbs.map(kb => `<li>${kb}</li>`).join('');
        } else {
            affectedBox.style.display = 'none';
        }
        openModal('deleteConfirmModal');
    } catch(e) { 
        showToast('error', '请求失败', e.message || '未知错误');
    }
}

export async function confirmDeleteFile() {
    // 【修正】直接使用顶部导入的 state，不要在函数内 import
    if (!state.fileToDelete) return;

    const btn = document.getElementById('confirmDeleteBtn');
    const originalText = btn.innerText;
    btn.innerText = "删除中...";
    btn.disabled = true;

    try {
        const res = await fetch('/api/files/delete/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ filename: state.fileToDelete, confirm_delete: true })
        });

        if(res.ok) {
            // 成功
        } else {
            console.warn("后端可能正在重启，或者删除返回了错误");
        }
    } catch(e) {
        console.error("删除请求异常 (可能是后端重启导致):", e);
    } finally {
        // === 强制执行 UI 重置 ===
        closeDeleteModal();
        btn.innerText = originalText;
        btn.disabled = false;

        // 延时一点刷新，等后端重启完
        setTimeout(() => {
            loadRootFiles();
            // 如果 window.loadKBList 存在，同时刷新它
            if(window.loadKBList) window.loadKBList();
        }, 1000);
    }
}

export function closeDeleteModal() {
    // 【修正】直接使用顶部导入的 closeModal 和 setFileToDelete
    closeModal('deleteConfirmModal');
    setFileToDelete(null);
}

window.changeGroup = changeGroup;
window.renameFile = renameFile;
window.tryDeleteFile = tryDeleteFile;
window.handleRootUpload = handleRootUpload;