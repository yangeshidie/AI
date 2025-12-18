// static/js/modules/prompts.js
/**
 * Prompt Storage Module
 */

/**
 * Load all prompts from the server.
 * @returns {Promise<Array>}
 */
export async function loadPrompts() {
    try {
        const response = await fetch('/api/prompts');
        return await response.json();
    } catch (error) {
        console.error('Failed to load prompts:', error);
        return [];
    }
}

/**
 * Save a new prompt.
 * @param {string} name - Prompt name.
 * @param {string} content - Prompt content.
 * @returns {Promise<Object|null>}
 */
export async function savePrompt(name, content) {
    try {
        const response = await fetch('/api/prompts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, content })
        });
        return await response.json();
    } catch (error) {
        console.error('Failed to save prompt:', error);
        return null;
    }
}

/**
 * Delete a prompt by ID.
 * @param {string} promptId - The ID of the prompt to delete.
 * @returns {Promise<boolean>}
 */
export async function deletePrompt(promptId) {
    try {
        const response = await fetch(`/api/prompts/${promptId}`, {
            method: 'DELETE'
        });
        return response.ok;
    } catch (error) {
        console.error('Failed to delete prompt:', error);
        return false;
    }
}

/**
 * Render prompts list into a container.
 * @param {string} containerId - The ID of the container element.
 */
export async function renderPromptsList(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const prompts = await loadPrompts();
    
    if (prompts.length === 0) {
        container.innerHTML = '<p style="color:#666; text-align:center;">暂无保存的提示词</p>';
        return;
    }

    container.innerHTML = prompts.map(prompt => `
        <div class="prompt-item" data-id="${prompt.id}">
            <div class="prompt-info" onclick="usePrompt('${prompt.id}')">
                <span class="prompt-name">${prompt.name}</span>
            </div>
            <div class="prompt-actions">
                <button class="icon-action-btn" onclick="usePrompt('${prompt.id}')" title="使用">
                    <span class="material-symbols-outlined">play_arrow</span>
                </button>
                <button class="icon-action-btn delete" onclick="deletePromptItem('${prompt.id}')" title="删除">
                    <span class="material-symbols-outlined">delete</span>
                </button>
            </div>
        </div>
    `).join('');
}

/**
 * Use a prompt by inserting its content into the input.
 * @param {string} promptId - The ID of the prompt.
 */
export async function usePrompt(promptId) {
    const prompts = await loadPrompts();
    const prompt = prompts.find(p => p.id === promptId);
    if (prompt) {
        const input = document.getElementById('userInput');
        if (input) {
            input.value = prompt.content;
            input.focus();
        }
        closePromptsModal();
    }
}

/**
 * Delete a prompt item and refresh the list.
 * @param {string} promptId - The ID of the prompt.
 */
export async function deletePromptItem(promptId) {
    const success = await deletePrompt(promptId);
    if (success) {
        renderPromptsList('promptsListContent');
    }
}

/**
 * Show prompts modal.
 */
export function showPromptsModal() {
    const modal = document.getElementById('promptsModal');
    if (modal) {
        modal.classList.add('show');
        renderPromptsList('promptsListContent');
    }
}

/**
 * Close prompts modal.
 */
export function closePromptsModal() {
    const modal = document.getElementById('promptsModal');
    if (modal) {
        modal.classList.remove('show');
    }
}

/**
 * Save current input as a new prompt.
 */
export async function saveCurrentPrompt() {
    const input = document.getElementById('userInput');
    const content = input ? input.value.trim() : '';
    
    if (!content) {
        alert('请先输入提示词内容');
        return;
    }
    
    const name = window.prompt('请输入提示词名称:');
    if (!name || !name.trim()) {
        return;
    }
    
    const result = await savePrompt(name.trim(), content);
    if (result) {
        alert('提示词已保存');
        renderPromptsList('promptsListContent');
    } else {
        alert('保存失败');
    }
}
