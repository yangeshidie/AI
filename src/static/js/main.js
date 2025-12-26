// static/js/main.js

import { initMarkdown, closeModal } from './utils.js';
import { switchView } from './router.js';
import * as Chat from './modules/chat.js';
import * as KB from './modules/kb.js';
import * as Files from './modules/files.js';
import * as History from './modules/history.js';
import * as Prompts from './modules/prompts.js';
import * as Settings from './modules/settings.js';

document.addEventListener('DOMContentLoaded', () => {
    initMarkdown();
    Chat.loadConfig();
    Settings.loadConfigs(); // Load stored configs
    Chat.initChatListeners();
    switchView('chat');
});

// === 暴露全局函数给 HTML onclick 调用 ===

// 导航
window.switchView = switchView;

// 聊天
window.startNewChat = Chat.startNewChat;
window.sendMessage = Chat.sendMessage;
window.fetchModels = Chat.fetchModels;
window.saveConfig = Chat.saveConfig;
window.handleFileSelect = Chat.handleFileSelect;
window.handleFileSelect = handleFileSelect;
window.clearMediaSelection = Chat.clearMediaSelection;
window.toggleStream = Chat.toggleStream;

// 知识库 KB
window.loadKBList = KB.loadKBList;
window.showCreateKBModal = KB.showCreateKBModal;
window.submitCreateKB = KB.submitCreateKB;
window.deleteKB = KB.deleteKB;

// 文件
window.handleRootUpload = Files.handleRootUpload;
window.renameFile = Files.renameFile;
window.tryDeleteFile = Files.tryDeleteFile;
window.confirmDeleteFile = Files.confirmDeleteFile;
window.closeDeleteModal = Files.closeDeleteModal;
window.changeGroup = Files.changeGroup;

// 历史记录
window.toggleHistory = History.toggleHistory;
window.loadSession = History.loadSession;
window.renameHistory = History.renameHistory;
window.deleteHistory = History.deleteHistory;

// 通用 Modal
window.closeModal = closeModal;

// 提示词
window.showPromptsModal = Prompts.showPromptsModal;
window.closePromptsModal = Prompts.closePromptsModal;
window.saveCurrentPrompt = Prompts.saveCurrentPrompt;
window.usePrompt = Prompts.usePrompt;
window.deletePromptItem = Prompts.deletePromptItem;

// 设置
window.loadConfigs = Settings.loadConfigs;
window.applyConfig = Settings.applyConfig;
window.showAddConfigModal = Settings.showAddConfigModal;
window.closeAddConfigModal = Settings.closeAddConfigModal;
window.saveNewConfig = Settings.saveNewConfig;

// 侧边栏
window.toggleSidebar = function() {
    const sidebar = document.getElementById('sidebar');
    const icon = document.getElementById('sidebarToggleIcon');
    sidebar.classList.toggle('collapsed');
    
    if (sidebar.classList.contains('collapsed')) {
        icon.innerText = 'menu';
    } else {
        icon.innerText = 'menu_open';
    }
};