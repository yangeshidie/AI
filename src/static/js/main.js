// static/js/main.js

import { initMarkdown, closeModal } from './utils.js';
import { switchView } from './router.js';
import * as Chat from './modules/chat.js';
import * as KB from './modules/kb.js';
import * as Files from './modules/files.js';
import * as History from './modules/history.js';
import * as Prompts from './modules/prompts.js';

document.addEventListener('DOMContentLoaded', () => {
    initMarkdown();
    Chat.loadConfig();
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

// 历史记录
window.toggleHistory = History.toggleHistory;
window.loadSession = History.loadSession;
window.renameHistory = History.renameHistory;
window.deleteHistory = History.deleteHistory;
window.changeGroup = Files.changeGroup;
// 通用 Modal
window.closeModal = closeModal;

// 提示词
window.showPromptsModal = Prompts.showPromptsModal;
window.closePromptsModal = Prompts.closePromptsModal;
window.saveCurrentPrompt = Prompts.saveCurrentPrompt;
window.usePrompt = Prompts.usePrompt;
window.deletePromptItem = Prompts.deletePromptItem;