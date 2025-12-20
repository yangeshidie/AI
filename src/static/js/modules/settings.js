// static/js/modules/settings.js
import { state, setConfig } from '../state.js';
import { closeModal } from '../utils.js';

export async function loadConfigs() {
    try {
        const res = await fetch('/api/settings/configs');
        const data = await res.json();
        const select = document.getElementById('configSelect');

        // 保存当前选中的值
        const currentVal = select.value;

        select.innerHTML = '<option value="">-- Select Config --</option>';
        data.configs.forEach(name => {
            const opt = document.createElement('option');
            opt.value = name;
            opt.innerText = name;
            select.appendChild(opt);
        });

        // 尝试恢复选中状态
        if (currentVal && data.configs.includes(currentVal)) {
            select.value = currentVal;
        }
    } catch (e) {
        console.error("Failed to load configs", e);
    }
}

export async function applyConfig(name) {
    if (!name) return;
    try {
        const res = await fetch(`/api/settings/config/${name}`);
        if (!res.ok) throw new Error("Config not found");

        const data = await res.json();
        document.getElementById('apiUrl').value = data.base_url;
        document.getElementById('apiKey').value = data.api_key;

        // 更新全局状态
        setConfig({
            apiUrl: data.base_url,
            apiKey: data.api_key,
            model: document.getElementById('modelSelect').value
        });

        // 刷新模型列表
        if (window.fetchModels) {
            window.fetchModels();
        }

        alert(`已应用配置: ${name}`);
    } catch (e) {
        alert("应用配置失败: " + e.message);
    }
}


import { openModal, closeModal as closeUtilsModal } from '../utils.js';


export function showAddConfigModal() {

    const modal = document.getElementById('addConfigModal');
    if (modal) modal.classList.add('show');
}

export function closeAddConfigModal() {
    const modal = document.getElementById('addConfigModal');
    if (modal) modal.classList.remove('show');
    document.getElementById('newConfigName').value = '';
    document.getElementById('newConfigUrl').value = '';
    document.getElementById('newConfigKey').value = '';
}

export async function saveNewConfig() {
    const name = document.getElementById('newConfigName').value.trim();
    const url = document.getElementById('newConfigUrl').value.trim();
    const key = document.getElementById('newConfigKey').value.trim();

    if (!name || !url) {
        alert("名称和 API URL 必填");
        return;
    }

    try {
        const res = await fetch('/api/settings/configs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                base_url: url,
                api_key: key
            })
        });

        const data = await res.json();
        if (res.ok) {
            alert("配置保存成功");
            closeAddConfigModal();
            loadConfigs(); // 刷新列表
        } else {
            alert("保存失败: " + data.detail);
        }
    } catch (e) {
        alert("保存错误: " + e.message);
    }
}
