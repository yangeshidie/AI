// app/static/js/workflow-editor.js
/**
 * 工作流编辑器
 * 基于拖拽的节点编辑器，支持节点连接
 */

class WorkflowEditor {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.nodes = [];
        this.edges = [];
        this.selectedNode = null;
        this.draggedNode = null;
        this.isDragging = false;
        this.dragOffset = { x: 0, y: 0 };
        this.connectingFrom = null;
        this.isConnecting = false;

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadConfigs();
    }

    async loadConfigs() {
        try {
            const response = await fetch('/api/workflows/configs');
            const data = await response.json();
            this.configs = data.configs || [];
        } catch (error) {
            console.error('加载配置失败:', error);
            this.configs = [];
        }
    }

    setupEventListeners() {
        document.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        document.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        document.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }

    addNode(type) {
        const nodeId = `node_${Date.now()}`;
        const node = {
            node_id: nodeId,
            node_type: type,
            position: { x: 100 + Math.random() * 200, y: 100 + Math.random() * 200 },
            data: this.getDefaultNodeData(type)
        };

        this.nodes.push(node);
        this.renderNode(node);
    }

    getDefaultNodeData(type) {
        const defaults = {
            llm: {
                config_id: '',
                model: 'gpt-3.5-turbo',
                system_prompt: '',
                temperature: 0.7,
                user_message: '{{user_input}}',
                enable_structured_output: false,
                structured_output_schema: null
            },
            rag: {
                kb_ids: [],
                query: '{{user_input}}',
                top_k: 3
            },
            code: {
                code: '# 在这里编写 Python 代码\noutput = "Hello, World!"',
                timeout: 30
            },
            condition: {
                conditions: [],
                default_branch: ''
            },
            http: {
                url: '',
                method: 'GET',
                headers: {},
                body: null,
                timeout: 30
            },
            variable: {
                variable_name: '',
                default_value: '',
                variable_type: 'string'
            },
            template: {
                template: 'Hello, {{name}}!'
            }
        };

        return defaults[type] || {};
    }

    renderNode(node) {
        const nodesLayer = document.getElementById('nodesLayer');
        const nodeEl = document.createElement('div');
        nodeEl.className = `workflow-node node-${node.node_type}`;
        nodeEl.id = node.node_id;
        nodeEl.style.left = `${node.position.x}px`;
        nodeEl.style.top = `${node.position.y}px`;

        const nodeLabels = {
            llm: 'LLM',
            rag: 'RAG',
            code: '代码',
            condition: '条件',
            http: 'HTTP',
            variable: '变量',
            template: '模板'
        };

        nodeEl.innerHTML = `
            <div class="node-header">
                <span class="node-title">${nodeLabels[node.node_type]}</span>
                <button class="node-delete" data-node-id="${node.node_id}">×</button>
            </div>
            <div class="node-body">
                <span class="node-id">${node.node_id}</span>
            </div>
            <div class="node-port node-port-input" data-port-type="input" data-node-id="${node.node_id}"></div>
            <div class="node-port node-port-output" data-port-type="output" data-node-id="${node.node_id}"></div>
        `;

        nodesLayer.appendChild(nodeEl);
    }

    deleteNode(nodeId) {
        this.nodes = this.nodes.filter(n => n.node_id !== nodeId);
        this.edges = this.edges.filter(e => e.source !== nodeId && e.target !== nodeId);
        
        const nodeEl = document.getElementById(nodeId);
        if (nodeEl) {
            nodeEl.remove();
        }
        
        this.renderConnections();
    }

    handleMouseDown(e) {
        const portEl = e.target.closest('.node-port');
        const nodeEl = e.target.closest('.workflow-node');
        const deleteBtn = e.target.closest('.node-delete');
        const propertyPanel = e.target.closest('.node-properties');

        if (deleteBtn) {
            e.stopPropagation();
            const nodeId = deleteBtn.dataset.nodeId;
            this.deleteNode(nodeId);
            return;
        }

        if (portEl) {
            e.stopPropagation();
            const portType = portEl.dataset.portType;
            const nodeId = portEl.dataset.nodeId;

            if (portType === 'output') {
                this.isConnecting = true;
                this.connectingFrom = { nodeId, portEl };
                portEl.classList.add('connecting');
            }
            return;
        }

        if (nodeEl) {
            e.stopPropagation();
            this.draggedNode = nodeEl;
            this.isDragging = true;
            const rect = nodeEl.getBoundingClientRect();
            this.dragOffset = {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            };
            this.selectNode(nodeEl.id);
        } else if (!propertyPanel) {
            this.deselectNode();
        }
    }

    handleMouseMove(e) {
        if (this.isDragging && this.draggedNode) {
            const canvas = document.getElementById('workflowCanvas');
            const canvasRect = canvas.getBoundingClientRect();
            const x = e.clientX - canvasRect.left - this.dragOffset.x;
            const y = e.clientY - canvasRect.top - this.dragOffset.y;

            this.draggedNode.style.left = `${x}px`;
            this.draggedNode.style.top = `${y}px`;

            const node = this.nodes.find(n => n.node_id === this.draggedNode.id);
            if (node) {
                node.position = { x, y };
            }

            this.renderConnections();
        }

        if (this.isConnecting && this.connectingFrom) {
            this.renderConnectionLine(e);
        }
    }

    handleMouseUp(e) {
        if (this.isConnecting && this.connectingFrom) {
            const portEl = e.target.closest('.node-port');
            
            if (portEl && portEl.dataset.portType === 'input') {
                const targetNodeId = portEl.dataset.nodeId;
                const sourceNodeId = this.connectingFrom.nodeId;

                if (sourceNodeId !== targetNodeId) {
                    this.addEdge(sourceNodeId, targetNodeId);
                }
            }

            this.connectingFrom.portEl.classList.remove('connecting');
            this.isConnecting = false;
            this.connectingFrom = null;
            this.clearConnectionLine();
        }

        if (this.isDragging) {
            this.isDragging = false;
            this.draggedNode = null;
        }
    }

    handleKeyDown(e) {
        if (e.key === 'Delete' && this.selectedNode) {
            this.deleteNode(this.selectedNode);
        }
        if (e.key === 'Escape') {
            if (this.isConnecting) {
                this.connectingFrom.portEl.classList.remove('connecting');
                this.isConnecting = false;
                this.connectingFrom = null;
                this.clearConnectionLine();
            }
        }
    }

    addEdge(sourceId, targetId) {
        const edgeId = `edge_${sourceId}_${targetId}`;
        
        const existingEdge = this.edges.find(e => e.source === sourceId && e.target === targetId);
        if (existingEdge) return;

        const edge = {
            id: edgeId,
            source: sourceId,
            target: targetId
        };

        this.edges.push(edge);
        this.renderConnections();
    }

    renderConnections() {
        const connectionsLayer = document.getElementById('connectionsLayer');
        let svg = '';

        this.edges.forEach(edge => {
            const sourceNode = this.nodes.find(n => n.node_id === edge.source);
            const targetNode = this.nodes.find(n => n.node_id === edge.target);

            if (sourceNode && targetNode) {
                const x1 = sourceNode.position.x + 160;
                const y1 = sourceNode.position.y + 45;
                const x2 = targetNode.position.x;
                const y2 = targetNode.position.y + 45;

                svg += `
                    <path 
                        d="M ${x1} ${y1} C ${x1 + 50} ${y1}, ${x2 - 50} ${y2}, ${x2} ${y2}"
                        class="connection-path"
                        data-edge-id="${edge.id}"
                    />
                `;
            }
        });

        connectionsLayer.innerHTML = `
            <defs>
                <marker id="arrowhead" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
                    <polygon points="0 0, 12 6, 0 12" fill="#666" />
                </marker>
            </defs>
            ${svg}
            <line id="tempConnectionLine" style="display: none; stroke: #3b82f6; stroke-width: 3; stroke-dasharray: 8,4;" />
        `;
    }

    renderConnectionLine(e) {
        const canvas = document.getElementById('workflowCanvas');
        const canvasRect = canvas.getBoundingClientRect();
        const tempLine = document.getElementById('tempConnectionLine');
        
        if (!tempLine) return;

        const sourceNode = this.nodes.find(n => n.node_id === this.connectingFrom.nodeId);
        if (!sourceNode) return;

        const x1 = sourceNode.position.x + 160;
        const y1 = sourceNode.position.y + 45;
        const x2 = e.clientX - canvasRect.left;
        const y2 = e.clientY - canvasRect.top;

        tempLine.setAttribute('x1', x1);
        tempLine.setAttribute('y1', y1);
        tempLine.setAttribute('x2', x2);
        tempLine.setAttribute('y2', y2);
        tempLine.style.display = 'block';
    }

    clearConnectionLine() {
        const tempLine = document.getElementById('tempConnectionLine');
        if (tempLine) {
            tempLine.style.display = 'none';
        }
    }

    selectNode(nodeId) {
        if (this.selectedNode) {
            const prevEl = document.getElementById(this.selectedNode);
            if (prevEl) {
                prevEl.classList.remove('selected');
            }
        }

        this.selectedNode = nodeId;
        const nodeEl = document.getElementById(nodeId);
        if (nodeEl) {
            nodeEl.classList.add('selected');
        }

        this.showNodeProperties(nodeId);
    }

    deselectNode() {
        if (this.selectedNode) {
            const nodeEl = document.getElementById(this.selectedNode);
            if (nodeEl) {
                nodeEl.classList.remove('selected');
            }
        }
        this.selectedNode = null;
        document.getElementById('propertiesContent').innerHTML = '<p style="color: #666; text-align: center; padding: 20px;">选择一个节点查看属性</p>';
    }

    showNodeProperties(nodeId) {
        const node = this.nodes.find(n => n.node_id === nodeId);
        if (!node) return;

        let html = `<div class="property-group">
            <label>节点 ID</label>
            <input type="text" value="${node.node_id}" readonly>
        </div>`;

        // 添加连接信息
        const inputConnections = this.edges.filter(e => e.target === nodeId);
        const outputConnections = this.edges.filter(e => e.source === nodeId);

        if (inputConnections.length > 0 || outputConnections.length > 0) {
            html += `<div class="property-group">
                <label>连接信息</label>
                <div class="connections-info">`;
            
            if (inputConnections.length > 0) {
                html += `<div class="connection-item">
                    <span class="connection-label">输入连接:</span>
                    <ul class="connection-list">`;
                inputConnections.forEach(edge => {
                    const sourceNode = this.nodes.find(n => n.node_id === edge.source);
                    const sourceLabel = sourceNode ? `${sourceNode.node_type} (${edge.source})` : edge.source;
                    html += `<li>${sourceLabel} → ${node.node_type} (${nodeId})</li>`;
                });
                html += `</ul></div>`;
            }
            
            if (outputConnections.length > 0) {
                html += `<div class="connection-item">
                    <span class="connection-label">输出连接:</span>
                    <ul class="connection-list">`;
                outputConnections.forEach(edge => {
                    const targetNode = this.nodes.find(n => n.node_id === edge.target);
                    const targetLabel = targetNode ? `${targetNode.node_type} (${edge.target})` : edge.target;
                    html += `<li>${node.node_type} (${nodeId}) → ${targetLabel}</li>`;
                });
                html += `</ul></div>`;
            }
            
            if (inputConnections.length === 0 && outputConnections.length === 0) {
                html += `<div class="no-connections">暂无连接</div>`;
            }
            
            html += `</div></div>`;
        }

        if (node.node_type === 'llm') {
            html += this.renderLLMProperties(node);
        } else if (node.node_type === 'rag') {
            html += this.renderRAGProperties(node);
        } else if (node.node_type === 'code') {
            html += this.renderCodeProperties(node);
        } else if (node.node_type === 'condition') {
            html += this.renderConditionProperties(node);
        } else if (node.node_type === 'http') {
            html += this.renderHTTPProperties(node);
        } else if (node.node_type === 'variable') {
            html += this.renderVariableProperties(node);
        } else if (node.node_type === 'template') {
            html += this.renderTemplateProperties(node);
        }

        document.getElementById('propertiesContent').innerHTML = html;
    }

    renderLLMProperties(node) {
        const data = node.data;
        const configOptions = this.configs.map(config => 
            `<option value="${config.name}" ${data.config_id === config.name ? 'selected' : ''}>${config.name}</option>`
        ).join('');

        return `
            <div class="property-group">
                <label>配置预设</label>
                <select id="llm_config_id" onchange="workflowEditor.updateNodeData('${node.node_id}', 'config_id', this.value)">
                    <option value="">-- 选择预设 --</option>
                    ${configOptions}
                </select>
            </div>
            <div class="property-group">
                <label>模型</label>
                <input type="text" value="${data.model || ''}" onchange="workflowEditor.updateNodeData('${node.node_id}', 'model', this.value)">
            </div>
            <div class="property-group">
                <label>系统提示词</label>
                <textarea onchange="workflowEditor.updateNodeData('${node.node_id}', 'system_prompt', this.value)">${data.system_prompt || ''}</textarea>
            </div>
            <div class="property-group">
                <label>温度 (0-2)</label>
                <input type="number" step="0.1" min="0" max="2" value="${data.temperature || 0.7}" onchange="workflowEditor.updateNodeData('${node.node_id}', 'temperature', parseFloat(this.value))">
            </div>
            <div class="property-group">
                <label>用户消息模板</label>
                <textarea onchange="workflowEditor.updateNodeData('${node.node_id}', 'user_message', this.value)">${data.user_message || '{{user_input}}'}</textarea>
            </div>
            <div class="property-group">
                <label>结构化输出</label>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <input type="checkbox" id="structured_output_toggle" ${data.enable_structured_output ? 'checked' : ''} onchange="workflowEditor.toggleStructuredOutput('${node.node_id}', this.checked)">
                    <span>启用结构化输出</span>
                </div>
            </div>
            <div class="property-group" id="structured_output_schema_group" style="display: ${data.enable_structured_output ? 'block' : 'none'};">
                <label>JSON Schema</label>
                <textarea onchange="workflowEditor.updateNodeData('${node.node_id}', 'structured_output_schema', this.value)">${data.structured_output_schema || ''}</textarea>
            </div>
        `;
    }

    toggleStructuredOutput(nodeId, enabled) {
        const node = this.nodes.find(n => n.node_id === nodeId);
        if (node) {
            node.data.enable_structured_output = enabled;
            document.getElementById('structured_output_schema_group').style.display = enabled ? 'block' : 'none';
        }
    }

    renderRAGProperties(node) {
        const data = node.data;
        return `
            <div class="property-group">
                <label>知识库 ID</label>
                <input type="text" value="${data.kb_ids.join(', ') || ''}" onchange="workflowEditor.updateNodeData('${node.node_id}', 'kb_ids', this.value.split(',').map(s => s.trim()))">
            </div>
            <div class="property-group">
                <label>查询模板</label>
                <textarea onchange="workflowEditor.updateNodeData('${node.node_id}', 'query', this.value)">${data.query || '{{user_input}}'}</textarea>
            </div>
            <div class="property-group">
                <label>Top K</label>
                <input type="number" min="1" max="10" value="${data.top_k || 3}" onchange="workflowEditor.updateNodeData('${node.node_id}', 'top_k', parseInt(this.value))">
            </div>
        `;
    }

    renderCodeProperties(node) {
        const data = node.data;
        return `
            <div class="property-group">
                <label>Python 代码</label>
                <textarea onchange="workflowEditor.updateNodeData('${node.node_id}', 'code', this.value)">${data.code || ''}</textarea>
            </div>
            <div class="property-group">
                <label>超时 (秒)</label>
                <input type="number" min="1" value="${data.timeout || 30}" onchange="workflowEditor.updateNodeData('${node.node_id}', 'timeout', parseInt(this.value))">
            </div>
        `;
    }

    renderConditionProperties(node) {
        const data = node.data;
        return `
            <div class="property-group">
                <label>条件表达式 (JSON)</label>
                <textarea onchange="workflowEditor.updateNodeData('${node.node_id}', 'conditions', this.value)">${JSON.stringify(data.conditions || [], null, 2)}</textarea>
            </div>
            <div class="property-group">
                <label>默认分支</label>
                <input type="text" value="${data.default_branch || ''}" onchange="workflowEditor.updateNodeData('${node.node_id}', 'default_branch', this.value)">
            </div>
        `;
    }

    renderHTTPProperties(node) {
        const data = node.data;
        return `
            <div class="property-group">
                <label>URL</label>
                <input type="text" value="${data.url || ''}" onchange="workflowEditor.updateNodeData('${node.node_id}', 'url', this.value)">
            </div>
            <div class="property-group">
                <label>方法</label>
                <select onchange="workflowEditor.updateNodeData('${node.node_id}', 'method', this.value)">
                    <option value="GET" ${data.method === 'GET' ? 'selected' : ''}>GET</option>
                    <option value="POST" ${data.method === 'POST' ? 'selected' : ''}>POST</option>
                    <option value="PUT" ${data.method === 'PUT' ? 'selected' : ''}>PUT</option>
                    <option value="DELETE" ${data.method === 'DELETE' ? 'selected' : ''}>DELETE</option>
                </select>
            </div>
            <div class="property-group">
                <label>Headers (JSON)</label>
                <textarea onchange="workflowEditor.updateNodeData('${node.node_id}', 'headers', this.value)">${JSON.stringify(data.headers || {}, null, 2)}</textarea>
            </div>
            <div class="property-group">
                <label>Body (JSON)</label>
                <textarea onchange="workflowEditor.updateNodeData('${node.node_id}', 'body', this.value)">${data.body ? JSON.stringify(data.body, null, 2) : ''}</textarea>
            </div>
            <div class="property-group">
                <label>超时 (秒)</label>
                <input type="number" min="1" value="${data.timeout || 30}" onchange="workflowEditor.updateNodeData('${node.node_id}', 'timeout', parseInt(this.value))">
            </div>
        `;
    }

    renderVariableProperties(node) {
        const data = node.data;
        return `
            <div class="property-group">
                <label>变量名称</label>
                <input type="text" value="${data.variable_name || ''}" onchange="workflowEditor.updateNodeData('${node.node_id}', 'variable_name', this.value)">
            </div>
            <div class="property-group">
                <label>默认值</label>
                <input type="text" value="${data.default_value || ''}" onchange="workflowEditor.updateNodeData('${node.node_id}', 'default_value', this.value)">
            </div>
            <div class="property-group">
                <label>变量类型</label>
                <select onchange="workflowEditor.updateNodeData('${node.node_id}', 'variable_type', this.value)">
                    <option value="string" ${data.variable_type === 'string' ? 'selected' : ''}>字符串</option>
                    <option value="number" ${data.variable_type === 'number' ? 'selected' : ''}>数字</option>
                    <option value="boolean" ${data.variable_type === 'boolean' ? 'selected' : ''}>布尔值</option>
                    <option value="object" ${data.variable_type === 'object' ? 'selected' : ''}>对象</option>
                </select>
            </div>
        `;
    }

    renderTemplateProperties(node) {
        const data = node.data;
        return `
            <div class="property-group">
                <label>模板内容</label>
                <textarea onchange="workflowEditor.updateNodeData('${node.node_id}', 'template', this.value)">${data.template || ''}</textarea>
            </div>
        `;
    }

    updateNodeData(nodeId, key, value) {
        const node = this.nodes.find(n => n.node_id === nodeId);
        if (node) {
            try {
                if (key === 'kb_ids' || key === 'conditions' || key === 'headers' || key === 'body') {
                    node.data[key] = JSON.parse(value);
                } else {
                    node.data[key] = value;
                }
            } catch {
                node.data[key] = value;
            }
        }
    }

    saveWorkflow() {
        const workflowData = {
            nodes: this.nodes,
            edges: this.edges
        };

        fetch('/api/workflows/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(workflowData)
        })
        .then(res => res.json())
        .then(data => {
            alert('工作流保存成功！');
            console.log(data);
        })
        .catch(err => {
            alert('保存失败: ' + err.message);
        });
    }

    loadTemplate() {
        const templateName = prompt('输入模板名称 (simple_chat, rag_chat, conditional_flow):');
        if (!templateName) return;

        fetch(`/api/workflows/templates/${templateName}`)
            .then(res => res.json())
            .then(data => {
                this.clearAll();
                this.nodes = data.nodes;
                this.edges = data.edges;
                this.nodes.forEach(node => this.renderNode(node));
                this.renderConnections();
            })
            .catch(err => {
                alert('加载模板失败: ' + err.message);
            });
    }

    clearAll() {
        this.nodes = [];
        this.edges = [];
        document.getElementById('nodesLayer').innerHTML = '';
        this.renderConnections();
        this.deselectNode();
    }
}

let workflowEditor;
