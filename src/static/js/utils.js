// static/js/utils.js
import { state } from './state.js';

// =============================================================================
// 请求重试机制
// =============================================================================

/**
 * 带重试机制的 fetch 请求
 * @param {string} url - 请求 URL
 * @param {object} options - fetch 选项
 * @param {number} maxRetries - 最大重试次数（默认 3）
 * @param {number} retryDelay - 重试延迟（毫秒，默认 1000）
 * @returns {Promise<Response>}
 */
export async function fetchWithRetry(url, options = {}, maxRetries = 3, retryDelay = 1000) {
    let lastError = null;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            const response = await fetch(url, options);
            
            // 如果响应成功，直接返回
            if (response.ok) {
                return response;
            }
            
            // 如果是客户端错误（4xx），不重试
            if (response.status >= 400 && response.status < 500) {
                return response;
            }
            
            // 服务器错误（5xx）或网络错误，准备重试
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            
        } catch (error) {
            lastError = error;
            
            // 最后一次尝试失败，不再重试
            if (attempt === maxRetries) {
                console.error(`请求失败，已重试 ${maxRetries} 次:`, url, error);
                throw error;
            }
            
            // 等待后重试
            console.warn(`请求失败，${retryDelay}ms 后进行第 ${attempt + 1} 次重试:`, url, error);
            await new Promise(resolve => setTimeout(resolve, retryDelay * (attempt + 1)));
        }
    }
    
    throw lastError;
}

// 初始化 Markdown
export function initMarkdown() {
    marked.setOptions({
        breaks: true,
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
        showToast('warning', '提示', '消息内容不能为空');
        return;
    }
    
    const messageWrapper = document.querySelector(`[data-message-id="${messageId}"]`);
    if (!messageWrapper) {
        showToast('error', '错误', '找不到要编辑的消息');
        return;
    }
    
    // 获取当前会话文件
    const sessionFile = state.currentSessionFile;
    
    if (!sessionFile) {
        showToast('error', '错误', '无法获取会话信息');
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
        showToast('error', '编辑失败', error.message);
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
        showToast('error', '错误', '无法获取会话信息');
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
        showToast('error', '删除失败', error.message);
    }
};

// =============================================================================
// Toast 提示组件
// =============================================================================

const Toast = {
    container: null,

    init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    },

    show(type, title, message, duration = 4000) {
        this.init();

        const icons = {
            success: 'check_circle',
            error: 'error',
            warning: 'warning',
            info: 'info'
        };

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-icon">
                <span class="material-symbols-outlined">${icons[type]}</span>
            </div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="Toast.remove(this.parentElement)">
                <span class="material-symbols-outlined">close</span>
            </button>
            <div class="toast-progress" style="animation-duration: ${duration}ms"></div>
        `;

        this.container.appendChild(toast);

        setTimeout(() => {
            this.remove(toast);
        }, duration);
    },

    remove(toast) {
        if (toast && toast.parentElement) {
            toast.classList.add('hiding');
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, 300);
        }
    },

    success(title, message, duration) {
        this.show('success', title, message, duration);
    },

    error(title, message, duration) {
        this.show('error', title, message, duration);
    },

    warning(title, message, duration) {
        this.show('warning', title, message, duration);
    },

    info(title, message, duration) {
        this.show('info', title, message, duration);
    }
};

window.Toast = Toast;
window.showToast = (type, title, message, duration) => {
    Toast.show(type, title, message, duration);
};

// =============================================================================
// 全局错误捕获机制
// =============================================================================

// 全局错误处理器
window.onerror = function(message, source, lineno, colno, error) {
    console.error('全局错误捕获:', { message, source, lineno, colno, error });
    showToast('error', '系统错误', `${message}`);
    return false;
};

// 未捕获的 Promise 拒绝处理器
window.onunhandledrejection = function(event) {
    console.error('未捕获的 Promise 拒绝:', event.reason);
    const errorMessage = event.reason?.message || String(event.reason);
    showToast('error', '异步错误', errorMessage);
    event.preventDefault();
};

// 网络请求错误拦截器
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    try {
        const response = await originalFetch(...args);
        
        // 检查响应状态
        if (!response.ok) {
            const url = args[0];
            console.error(`HTTP 错误: ${response.status} ${response.statusText}`, url);
            
            // 不显示 Toast 的错误（已经在其他地方处理了）
            const skipToast = url.includes('/api/chat') || url.includes('/api/models');
            
            if (!skipToast) {
                try {
                    const errorData = await response.json();
                    const errorMessage = errorData.detail || errorData.error || `HTTP ${response.status}`;
                    showToast('error', '请求失败', errorMessage);
                } catch (e) {
                    showToast('error', '请求失败', `HTTP ${response.status}`);
                }
            }
        }
        
        return response;
    } catch (error) {
        console.error('网络请求失败:', error);
        showToast('error', '网络错误', '请检查网络连接');
        throw error;
    }
};

// 控制台错误拦截（开发环境）
if (console.error) {
    const originalError = console.error;
    console.error = function(...args) {
        originalError.apply(console, args);
        
        // 只在生产环境显示 Toast
        if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
            const message = args.map(arg => 
                typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
            ).join(' ');
            
            if (message && !message.includes('DevTools')) {
                showToast('error', '控制台错误', message.substring(0, 100));
            }
        }
    };
}

// =============================================================================
// 加载状态指示器
// =============================================================================

const Loading = {
    overlay: null,
    spinner: null,
    text: null,
    counter: 0,

    init() {
        if (!this.overlay) {
            this.overlay = document.createElement('div');
            this.overlay.className = 'loading-overlay';
            this.overlay.innerHTML = `
                <div style="text-align: center;">
                    <div class="loading-spinner"></div>
                    <div class="loading-text" id="loadingText">加载中...</div>
                </div>
            `;
            document.body.appendChild(this.overlay);
            this.spinner = this.overlay.querySelector('.loading-spinner');
            this.text = this.overlay.querySelector('#loadingText');
        }
    },

    show(message = '加载中...') {
        this.init();
        this.counter++;
        
        if (this.text) {
            this.text.textContent = message;
        }
        
        this.overlay.classList.add('show');
    },

    hide() {
        this.counter--;
        
        if (this.counter <= 0) {
            this.counter = 0;
            if (this.overlay) {
                this.overlay.classList.remove('show');
            }
        }
    },

    setButtonLoading(button, isLoading) {
        if (isLoading) {
            button.classList.add('btn-loading');
            button.disabled = true;
        } else {
            button.classList.remove('btn-loading');
            button.disabled = false;
        }
    }
};

window.showLoading = (message) => Loading.show(message);
window.hideLoading = () => Loading.hide();
window.setButtonLoading = (button, isLoading) => Loading.setButtonLoading(button, isLoading);

// =============================================================================
// 消息搜索功能
// =============================================================================

const Search = {
    results: [],
    currentIndex: -1,
    query: '',

    toggle() {
        const searchBar = document.getElementById('searchBar');
        const isVisible = searchBar.style.display !== 'none';
        
        if (isVisible) {
            searchBar.style.display = 'none';
            this.clear();
        } else {
            searchBar.style.display = 'block';
            const input = document.getElementById('searchInput');
            input.focus();
        }
    },

    search(query) {
        this.query = query.toLowerCase();
        this.results = [];
        this.currentIndex = -1;
        
        if (!this.query) {
            this.clear();
            return;
        }

        const messages = document.querySelectorAll('#chatBox .message');
        messages.forEach((message, index) => {
            const text = message.textContent.toLowerCase();
            if (text.includes(this.query)) {
                this.results.push({
                    element: message,
                    index: index
                });
            }
        });

        this.updateCount();
        this.highlightResults();

        if (this.results.length > 0) {
            this.navigateTo(0);
        }
    },

    navigate(direction) {
        if (this.results.length === 0) return;

        this.currentIndex += direction;

        if (this.currentIndex < 0) {
            this.currentIndex = this.results.length - 1;
        } else if (this.currentIndex >= this.results.length) {
            this.currentIndex = 0;
        }

        this.navigateTo(this.currentIndex);
    },

    navigateTo(index) {
        this.results.forEach((result, i) => {
            if (i === index) {
                result.element.classList.add('current-match');
                result.element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else {
                result.element.classList.remove('current-match');
            }
        });

        this.updateCount();
    },

    highlightResults() {
        const messages = document.querySelectorAll('#chatBox .message');
        messages.forEach(message => {
            message.classList.remove('highlight', 'current-match');
        });

        this.results.forEach(result => {
            result.element.classList.add('highlight');
        });
    },

    clear() {
        this.results = [];
        this.currentIndex = -1;
        this.query = '';

        const messages = document.querySelectorAll('#chatBox .message');
        messages.forEach(message => {
            message.classList.remove('highlight', 'current-match');
        });

        this.updateCount();
    },

    updateCount() {
        const countElement = document.getElementById('searchCount');
        if (this.results.length === 0) {
            countElement.textContent = '0/0';
        } else {
            countElement.textContent = `${this.currentIndex + 1}/${this.results.length}`;
        }
    }
};

window.toggleSearch = () => Search.toggle();
window.handleSearch = (query) => Search.search(query);
window.navigateSearch = (direction) => Search.navigate(direction);

// =============================================================================
// 导出对话功能
// =============================================================================

const Export = {
    formats: ['txt', 'md', 'json'],

    export(format = 'md') {
        const chatBox = document.getElementById('chatBox');
        const messages = chatBox.querySelectorAll('.message');
        
        if (messages.length === 0) {
            showToast('warning', '提示', '没有可导出的消息');
            return;
        }

        const title = document.getElementById('chat-title').textContent || 'chat';
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `${title}_${timestamp}.${format}`;

        let content = '';

        switch (format) {
            case 'txt':
                content = this.exportToText(messages);
                break;
            case 'md':
                content = this.exportToMarkdown(messages);
                break;
            case 'json':
                content = this.exportToJson(messages);
                break;
            default:
                showToast('error', '错误', '不支持的导出格式');
                return;
        }

        this.downloadFile(content, filename, this.getMimeType(format));
        showToast('success', '导出成功', `已导出为 ${format.toUpperCase()} 格式`);
    },

    exportToText(messages) {
        let content = `对话导出\n${'='.repeat(50)}\n\n`;
        content += `标题: ${document.getElementById('chat-title').textContent}\n`;
        content += `副标题: ${document.getElementById('chat-subtitle').textContent}\n`;
        content += `导出时间: ${new Date().toLocaleString()}\n\n`;
        content += `${'='.repeat(50)}\n\n`;

        messages.forEach((message, index) => {
            const role = message.dataset.messageRole || 'unknown';
            const text = message.textContent.trim();
            
            content += `[${index + 1}] ${role.toUpperCase()}\n`;
            content += `${'─'.repeat(30)}\n`;
            content += `${text}\n\n`;
        });

        return content;
    },

    exportToMarkdown(messages) {
        let content = `# ${document.getElementById('chat-title').textContent}\n\n`;
        content += `**副标题**: ${document.getElementById('chat-subtitle').textContent}\n\n`;
        content += `**导出时间**: ${new Date().toLocaleString()}\n\n`;
        content += `---\n\n`;

        messages.forEach((message) => {
            const role = message.dataset.messageRole || 'unknown';
            const text = message.textContent.trim();
            
            content += `### ${role === 'user' ? '👤 用户' : '🤖 AI'}\n\n`;
            content += `${text}\n\n`;
            content += `---\n\n`;
        });

        return content;
    },

    exportToJson(messages) {
        const data = {
            title: document.getElementById('chat-title').textContent,
            subtitle: document.getElementById('chat-subtitle').textContent,
            exportTime: new Date().toISOString(),
            messages: []
        };

        messages.forEach((message) => {
            const role = message.dataset.messageRole || 'unknown';
            const text = message.textContent.trim();
            
            data.messages.push({
                role: role,
                content: text,
                timestamp: new Date().toISOString()
            });
        });

        return JSON.stringify(data, null, 2);
    },

    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },

    getMimeType(format) {
        const mimeTypes = {
            'txt': 'text/plain',
            'md': 'text/markdown',
            'json': 'application/json'
        };
        return mimeTypes[format] || 'text/plain';
    },

    showExportModal() {
        const format = window.prompt('请选择导出格式 (txt/md/json):', 'md');
        if (format && this.formats.includes(format.toLowerCase())) {
            this.export(format.toLowerCase());
        } else if (format) {
            showToast('error', '错误', '不支持的导出格式，请选择 txt/md/json');
        }
    }
};

window.exportChat = () => Export.showExportModal();