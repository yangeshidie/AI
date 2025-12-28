// static/js/state.js

export const state = {
    config: { apiUrl: "", apiKey: "", model: "" },
    conversationHistory: [],
    currentSessionFile: "",
    currentKB: null, // null = General Chat, Object = KB Chat
    fileToDelete: null, // 用于删除确认弹窗
    streamEnabled: false // 流式传输开关，默认关闭
};

// 简单的 Setter 帮助函数
export function setConfig(newConfig) { state.config = newConfig; }
export function setSessionFile(fileName) { state.currentSessionFile = fileName; }
export function setCurrentKB(kb) { state.currentKB = kb; }
export function setFileToDelete(file) { state.fileToDelete = file; }
export function clearHistory() { state.conversationHistory = []; }
export function pushToHistory(msg) {
    if (!msg.id) {
        msg.id = Date.now() + Math.random().toString(36).substr(2, 9);
    }
    state.conversationHistory.push(msg);
}