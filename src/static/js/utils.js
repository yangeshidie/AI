// static/js/utils.js

// 初始化 Markdown
export function initMarkdown() {
    marked.setOptions({
        highlight: function(code, lang) {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        }
    });
}

// 消息上屏逻辑
export function appendMessage(role, text, raw = false) {
    const chatBox = document.getElementById('chatBox');

    const wrapper = document.createElement('div');
    wrapper.className = `message ${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'msg-content';

    if (role === 'system' || raw) {
        contentDiv.innerText = text;
    } else {
        contentDiv.innerHTML = marked.parse(text);
        contentDiv.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }

    wrapper.appendChild(contentDiv);
    chatBox.appendChild(wrapper);

    // 隐藏欢迎语
    const welcome = document.querySelector('.welcome-banner');
    if(welcome) welcome.style.display = 'none';

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