// app/static/js/workflow-editor.js
/**
 * 工作流编辑器
 * 基于拖拽的节点编辑器
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

        this.init();
    }

    init() {
        this.container.innerHTML = `
            <div class="workflow-toolbar">
                <button class="btn btn-primary" onclick="workflowEditor.addNode('llm')">LLM 节点</button>
                <button class="btn btn-primary" onclick="workflowEditor.addNode('rag')">RAG 节点</button>
                <button class="btn btn-primary" onclick="workflowEditor.addNode('code')">代码节点</button>
                <button class="btn btn-primary" onclick="workflowEditor.addNode('condition')">条件节点</button>
                <button class="btn btn-primary" onclick="workflowEditor.addNode('http')">HTTP 节点</button>
                <button class="btn btn-primary" onclick="workflowEditor.addNode('variable')">变量节点</button>
                <button class="btn btn-primary" onclick="workflowEditor.addNode('template')">模板节点</button>
                <div class="toolbar-spacer"></div>
                <button class="btn btn-success" onclick="workflowEditor.saveWorkflow()">保存工作流</button>
                <button class="btn btn-info" onclick="workflowEditor.loadTemplate()">加载模板</button>
                <button class="btn btn-warning" onclick="workflowEditor.clearAll()">清空</button>
            </div>
            <div class="workflow-canvas" id="workflowCanvas">
                <svg class="connections-layer" id="connectionsLayer"></svg>
                <div class="nodes-layer" id="nodesLayer"></div>
            </div>
            <div class="node-properties" id="nodeProperties">
                <h3>节点属性</h3>
                <div id="propertiesContent"></div>
            </div>
        `;

        this.canvas = document.getElementById('workflowCanvas');
        this.connectionsLayer = document.getElementById('connectionsLayer');
        this.nodesLayer = document.getElementById('nodesLayer');
        this.propertiesPanel = document.getElementById('nodeProperties');
        this.propertiesContent = document.getElementById('propertiesContent');

        this.setupEventListeners();
    }

    setupEventListeners() {
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
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
                model: 'gpt-3.5-turbo',
                api_url: 'https://api.openai.com/v1',
                api_key: '',
                system_prompt: '',
                temperature: 0.7,
                user_message: '{{user_input}}'
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
                <button class="node-delete" onclick="workflowEditor.deleteNode('${node.node_id}')">×</button>
            </div>
            <div class="node-body">
                <span class="node-id">${node.node_id}</span>
            </div>
            <div class="node-port node-port-input"></div>
            <div class="node-port node-port-output"></div>
        `;

        this.nodesLayer.appendChild(nodeEl);
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
        const nodeEl = e.target.closest('.workflow-node');
        if (nodeEl) {
            this.draggedNode = nodeEl;
            this.isDragging = true;
            const rect = nodeEl.getBoundingClientRect();
            this.dragOffset = {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            };
            this.selectNode(nodeEl.id);
        } else {
            this.deselectNode();
        }
    }

    handleMouseMove(e) {
        if (this.isDragging && this.draggedNode) {
            const canvasRect = this.canvas.getBoundingClientRect();
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
    }

    handleMouseUp(e) {
        if (this.isDragging) {
            this.isDragging = false;
            this.draggedNode = null;
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
        this.propertiesContent.innerHTML = '<p>选择一个节点查看属性</p>';
    }

    showNodeProperties(nodeId) {
        const node = this.nodes.find(n => n.node_id === nodeId);
        if (!node) return;

        let html = `<div class="property-group">
            <label>节点 ID:</label>
            <input type="text" value="${node.node_id}" readonly>
        </div>`;

        for (const [key, value] of Object.entries(node.data)) {
            const displayValue = typeof value === 'object' ? JSON.stringify(value, null, 2) : value;
            html += `
                <div class="property-group">
                    <label>${key}:</label>
                    <textarea 
                        onchange="workflowEditor.updateNodeData('${nodeId}', '${key}', this.value)"
                    >${displayValue}</textarea>
                </div>
            `;
        }

        this.propertiesContent.innerHTML = html;
    }

    updateNodeData(nodeId, key, value) {
        const node = this.nodes.find(n => n.node_id === nodeId);
        if (node) {
            try {
                node.data[key] = JSON.parse(value);
            } catch {
                node.data[key] = value;
            }
        }
    }

    renderConnections() {
        let svg = '';
        this.edges.forEach(edge => {
            const sourceNode = this.nodes.find(n => n.node_id === edge.source);
            const targetNode = this.nodes.find(n => n.node_id === edge.target);

            if (sourceNode && targetNode) {
                const x1 = sourceNode.position.x + 150;
                const y1 = sourceNode.position.y + 40;
                const x2 = targetNode.position.x;
                const y2 = targetNode.position.y + 40;

                svg += `
                    <path 
                        d="M ${x1} ${y1} C ${x1 + 50} ${y1}, ${x2 - 50} ${y2}, ${x2} ${y2}"
                        stroke="#666"
                        stroke-width="2"
                        fill="none"
                        marker-end="url(#arrowhead)"
                    />
                `;
            }
        });

        this.connectionsLayer.innerHTML = `
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
                </marker>
            </defs>
            ${svg}
        `;
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
        this.nodesLayer.innerHTML = '';
        this.connectionsLayer.innerHTML = '';
        this.deselectNode();
    }
}

let workflowEditor;
