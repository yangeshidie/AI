// static/js/utils.js

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
export function appendMessage(role, text, raw = false) {
    const chatBox = document.getElementById('chatBox');

    const wrapper = document.createElement('div');
    wrapper.className = `message ${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'msg-content';

    // 消息主体容器
    const bodyDiv = document.createElement('div');
    bodyDiv.className = 'msg-body';

    // Helper function to render text
    const renderText = (content) => {
        const div = document.createElement('div');
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

        copyToolbar.appendChild(copyTextBtn);
        copyToolbar.appendChild(copyMdBtn);
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