import { state, setFileToDelete } from '../state.js';
import { openModal, closeModal } from '../utils.js';
import { loadKBList } from './kb.js';

export async function loadRootFiles() {
    const tbody = document.getElementById('file-list-body');
    if(!tbody) return;
    tbody.innerHTML = '<tr><td colspan="4">加载中...</td></tr>';
    try {
        const res = await fetch('/api/files/list');
        const data = await res.json();
        tbody.innerHTML = '';
        if (data.files.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#666;">暂无文件</td></tr>';
            return;
        }
            data.files.forEach(f => {
            tbody.innerHTML += `
                <tr>
                    <td style="display:flex; align-items:center; gap:8px;">
                        <span class="material-symbols-outlined">description</span> 
                        <span class="fname">${f.name}</span>
                    </td>
                    <!-- 新增分组列交互 -->
                    <td>
                        <span class="group-badge" onclick="window.changeGroup('${f.name}', '${f.group}')">
                            ${f.group} <span class="material-symbols-outlined" style="font-size:12px">edit</span>
                        </span>
                    </td>
                    <td>${f.size}</td>
                    <td>${f.date}</td>
                    <td style="text-align:right;">
                        <!-- 按钮保持不变 -->
                        <button class="icon-action-btn" onclick="window.renameFile('${f.name}')" title="重命名">
                            <span class="material-symbols-outlined" style="font-size:18px">edit</span>
                        </button>
                        <button class="icon-action-btn delete" onclick="window.tryDeleteFile('${f.name}')" title="删除">
                            <span class="material-symbols-outlined" style="font-size:18px">delete</span>
                        </button>
                    </td>
                </tr>
            `;
        });
    } catch (e) { console.error(e); }
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
    } catch(e) { alert("设置失败"); }
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
    } catch(e) { alert("重命名失败: " + e.message); }
}

export async function tryDeleteFile(filename) {
    setFileToDelete(filename);
    try {
        const res = await fetch('/api/files/delete', {
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
    } catch(e) { alert("请求失败: " + e); }
}

export async function confirmDeleteFile() {
    if (!state.fileToDelete) return;
    try {
        const res = await fetch('/api/files/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ filename: state.fileToDelete, confirm_delete: true })
        });
        if(res.ok) {
            closeDeleteModal();
            loadRootFiles();
            // 刷新 KB 列表以防显示过期数据
            loadKBList();
        } else {
            alert("删除失败");
        }
    } catch(e) { console.error(e); }
}

export function closeDeleteModal() {
    closeModal('deleteConfirmModal');
    setFileToDelete(null);
}