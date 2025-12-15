// static/js/state.js

export const state = {
    config: { apiUrl: "", apiKey: "", model: "" },
    conversationHistory: [],
    currentSessionFile: "",
    currentKB: null, // null = General Chat, Object = KB Chat
    fileToDelete: null // 用于删除确认弹窗
};

// 简单的 Setter 帮助函数
export function setConfig(newConfig) { state.config = newConfig; }
export function setSessionFile(fileName) { state.currentSessionFile = fileName; }
export function setCurrentKB(kb) { state.currentKB = kb; }
export function setFileToDelete(file) { state.fileToDelete = file; }
export function clearHistory() { state.conversationHistory = []; }
export function pushToHistory(msg) { state.conversationHistory.push(msg); }