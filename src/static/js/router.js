// static/js/router.js

import { loadKBList } from './modules/kb.js';
import { loadRootFiles } from './modules/files.js';

export async function switchView(viewName) {
    // 隐藏所有 View
    document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
    // 取消所有菜单激活状态
    document.querySelectorAll('.menu-item').forEach(el => el.classList.remove('active'));

    // 激活目标
    const target = document.getElementById(`view-${viewName}`);
    if (target) target.classList.add('active');

    // 激活菜单 (简单按顺序)
    const btns = document.querySelectorAll('.menu-item');
    if (viewName === 'chat') btns[0].classList.add('active');
    if (viewName === 'agents') {
        btns[1].classList.add('active');
        loadKBList();
    }
    if (viewName === 'library') {
        btns[2].classList.add('active');
        loadRootFiles();
    }
    if (viewName === 'settings') btns[3].classList.add('active');
}