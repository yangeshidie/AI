// static/js/utils.js
import { state } from './state.js';

// 初始化 Markdown
export function initMarkdown() {
    marked.setOptions({
        highlight: function (code, lang) {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        }
    });
}

// 消息上屏逻辑
export function appendMessage(role, text, raw = false, msgId = null) {
    const chatBox = document.getElementById('chatBox');

    const wrapper = document.createElement('div');
    wrapper.className = `message ${role}`;
    wrapper.dataset.messageId = msgId || Date.now() + Math.random().toString(36).substr(2, 9);
    wrapper.dataset.messageRole = role;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'msg-content';

    // 消息主体容器
    const bodyDiv = document.createElement('div');
    bodyDiv.className = 'msg-body';

    // Helper function to render text
    const renderText = (content) => {
        const div = document.createElement('div');
        div.className = 'message-content markdown-body';
        div.innerHTML = marked.parse(content || ''); // Handle null/undefined
        div.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
        return div;
    };

    // Helper function to render media
    const renderMedia = (url) => {
        if (!url) return document.createElement('div');

        if (url.startsWith('data:video') || url.match(/\.(mp4|webm)$/i)) {
            const vid = document.createElement('video');
            vid.src = url;
            vid.controls = true;
            vid.className = 'msg-image';
            return vid;
        } else if (url.startsWith('data:audio') || url.match(/\.(mp3|wav)$/i)) {
            const aud = document.createElement('audio');
            aud.src = url;
            aud.controls = true;
            return aud;
        } else {
            const img = document.createElement('img');
            img.src = url;
            img.className = 'msg-image';
            return img;
        }
    };

    if (role === 'system') {
        bodyDiv.innerText = text;
    } else if (Array.isArray(text)) {
        // Handle Multimodal Content (Array)
        text.forEach(item => {
            if (item.type === 'text') {
                bodyDiv.appendChild(renderText(item.text));
            } else if (item.type === 'image_url') {
                const url = item.image_url.url;
                bodyDiv.appendChild(renderMedia(url));
            }
        });
    } else {
        // Handle Simple String
        if (raw) {
            bodyDiv.innerText = text;
        } else {
            bodyDiv.appendChild(renderText(text));
        }
    }

    // Render LaTeX formulas with KaTeX
    if (typeof renderMathInElement === 'function' && role !== 'system') {
        renderMathInElement(bodyDiv, {
            delimiters: [
                { left: '$$', right: '$$', display: true },
                { left: '$', right: '$', display: false },
                { left: '\\[', right: '\\]', display: true },
                { left: '\\(', right: '\\)', display: false }
            ],
            throwOnError: false
        });
    }

    contentDiv.appendChild(bodyDiv);

    // 复制工具栏 (仅对非系统消息显示)
    if (role !== 'system') {
        const copyToolbar = document.createElement('div');
        copyToolbar.className = 'copy-toolbar';

        // Copy Text Button
        const copyTextBtn = document.createElement('button');
        copyTextBtn.className = 'copy-btn';
        copyTextBtn.innerText = 'Copy Text';
        copyTextBtn.onclick = () => {
            navigator.clipboard.writeText(bodyDiv.innerText).then(() => {
                const original = copyTextBtn.innerText;
                copyTextBtn.innerText = 'Copied!';
                setTimeout(() => copyTextBtn.innerText = original, 2000);
            });
        };

        // Copy MD Button
        const copyMdBtn = document.createElement('button');
        copyMdBtn.className = 'copy-btn';
        copyMdBtn.innerText = 'Copy MD';
        copyMdBtn.onclick = () => {
            let mdText = "";
            if (Array.isArray(text)) {
                mdText = text.filter(t => t.type === 'text').map(t => t.text).join('\n');
            } else {
                mdText = text;
            }
            navigator.clipboard.writeText(mdText).then(() => {
                const original = copyMdBtn.innerText;
                copyMdBtn.innerText = 'Copied!';
                setTimeout(() => copyMdBtn.innerText = original, 2000);
            });
        };

        // Edit Button
        const editBtn = document.createElement('button');
        editBtn.className = 'copy-btn edit-btn';
        editBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px">edit</span> 编辑';
        editBtn.onclick = () => openEditMessageModal(wrapper, text);

        // Delete Button
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'copy-btn delete-btn';
        deleteBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px">delete</span> 删除';
        deleteBtn.onclick = () => deleteMessage(wrapper);

        copyToolbar.appendChild(copyTextBtn);
        copyToolbar.appendChild(copyMdBtn);
        copyToolbar.appendChild(editBtn);
        copyToolbar.appendChild(deleteBtn);
        contentDiv.appendChild(copyToolbar);
    }

    wrapper.appendChild(contentDiv);
    chatBox.appendChild(wrapper);

    // 隐藏欢迎语
    const welcome = document.querySelector('.welcome-banner');
    if (welcome) welcome.style.display = 'none';

    chatBox.scrollTop = chatBox.scrollHeight;
    return contentDiv;
}

// 模态框通用控制
export function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
}
export function openModal(modalId) {
    document.getElementById(modalId).classList.add('show');
}

// 编辑消息模态框
window.openEditMessageModal = function(messageWrapper, text) {
    const messageId = messageWrapper.dataset.messageId;
    const messageRole = messageWrapper.dataset.messageRole;
    
    let contentText = '';
    if (Array.isArray(text)) {
        contentText = text.filter(t => t.type === 'text').map(t => t.text).join('\n');
    } else {
        contentText = text;
    }
    
    document.getElementById('editMessageId').value = messageId;
    document.getElementById('editMessageRole').value = messageRole;
    document.getElementById('editMessageContent').value = contentText;
    
    openModal('editMessageModal');
};

window.closeEditMessageModal = function() {
    closeModal('editMessageModal');
    document.getElementById('editMessageContent').value = '';
};

window.saveEditedMessage = async function() {
    const messageId = document.getElementById('editMessageId').value;
    const messageRole = document.getElementById('editMessageRole').value;
    const newContent = document.getElementById('editMessageContent').value.trim();
    
    if (!newContent) {
        alert('消息内容不能为空');
        return;
    }
    
    const messageWrapper = document.querySelector(`[data-message-id="${messageId}"]`);
    if (!messageWrapper) {
        alert('找不到要编辑的消息');
        return;
    }
    
    // 获取当前会话文件
    const sessionFile = state.currentSessionFile;
    
    if (!sessionFile) {
        alert('无法获取会话信息');
        return;
    }
    
    try {
        const response = await fetch('/api/edit_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message_id: messageId,
                role: messageRole,
                content: newContent,
                session_file: sessionFile
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || errorData.error || '编辑失败');
        }
        
        const result = await response.json();
        
        // 更新UI
        const bodyDiv = messageWrapper.querySelector('.msg-body');
        bodyDiv.innerHTML = marked.parse(newContent);
        bodyDiv.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
        
        // 更新state.conversationHistory
        const msgIndex = state.conversationHistory.findIndex(msg => 
            msg.id === messageId && msg.role === messageRole
        );
        if (msgIndex !== -1) {
            state.conversationHistory[msgIndex].content = newContent;
        }
        
        // 重新渲染LaTeX
        if (typeof renderMathInElement === 'function') {
            renderMathInElement(bodyDiv, {
                delimiters: [
                    { left: '$$', right: '$$', display: true },
                    { left: '$', right: '$', display: false },
                    { left: '\\[', right: '\\]', display: true },
                    { left: '\\(', right: '\\)', display: false }
                ],
                throwOnError: false
            });
        }
        
        closeEditMessageModal();
        
    } catch (error) {
        console.error('编辑消息失败:', error);
        alert('编辑消息失败: ' + error.message);
    }
};

// 删除消息
window.deleteMessage = async function(messageWrapper) {
    const messageId = messageWrapper.dataset.messageId;
    const messageRole = messageWrapper.dataset.messageRole;
    
    if (!confirm(`确定要删除这条${messageRole === 'user' ? '用户' : 'AI'}消息吗？`)) {
        return;
    }
    
    // 获取当前会话文件
    const sessionFile = state.currentSessionFile;
    
    if (!sessionFile) {
        alert('无法获取会话信息');
        return;
    }
    
    try {
        const response = await fetch('/api/delete_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message_id: messageId,
                role: messageRole,
                session_file: sessionFile
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || errorData.error || '删除失败');
        }
        
        const result = await response.json();
        
        // 从UI中移除消息
        messageWrapper.remove();
        
        // 更新state.conversationHistory，移除已删除的消息
        state.conversationHistory = state.conversationHistory.filter(msg => 
            !(msg.id === messageId && msg.role === messageRole)
        );
        
        // 如果没有消息了，显示欢迎语
        const chatBox = document.getElementById('chatBox');
        const messages = chatBox.querySelectorAll('.message');
        if (messages.length === 0) {
            const welcome = document.querySelector('.welcome-banner');
            if (welcome) welcome.style.display = 'block';
        }
        
    } catch (error) {
        console.error('删除消息失败:', error);
        alert('删除消息失败: ' + error.message);
    }
};