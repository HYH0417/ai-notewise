let editingModelId = null;

document.addEventListener('DOMContentLoaded', async () => {
    await loadModelConfigs();
    await loadScenarios();
});

async function loadModelConfigs() {
    try {
        const configs = await api.config.models.list();
        const container = document.getElementById('model-config-list');
        
        if (configs.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="icon">⚙️</div>
                    <p>暂无模型配置</p>
                    <button class="btn btn-primary" style="margin-top: 15px;" onclick="openModelModal()">添加配置</button>
                </div>
            `;
            return;
        }
        
        container.innerHTML = configs.map(c => `
            <div style="padding: 15px; border-bottom: 1px solid #e2e8f0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${c.name}</strong>
                        ${c.is_default ? '<span class="badge badge-success">默认</span>' : ''}
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <button class="btn btn-outline" onclick="editModelConfig(${c.id})">编辑</button>
                        <button class="btn btn-danger" style="padding: 4px 8px; font-size: 0.8rem;" 
                                onclick="deleteModelConfig(${c.id})">删除</button>
                    </div>
                </div>
                <div style="margin-top: 10px; font-size: 0.9rem; color: #64748b;">
                    <div>API Base: ${c.api_base}</div>
                    <div>模型 ID: ${c.model_id}</div>
                    <div>创建时间: ${formatDate(c.created_at)}</div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载模型配置失败:', error);
        document.getElementById('model-config-list').innerHTML = `
            <div class="empty-state">
                <div class="icon">❌</div>
                <p>加载失败，请刷新重试</p>
            </div>
        `;
    }
}

async function loadScenarios() {
    try {
        const scenarios = await api.config.scenarios();
        const container = document.getElementById('scenario-list');
        
        container.innerHTML = `
            <div style="padding: 20px; background: #f8fafc; border-radius: 8px;">
                <h4>当前场景列表：</h4>
                <div style="margin-top: 10px;">
                    ${scenarios.scenarios.map((s, i) => `
                        <span class="tag tag-primary">${i + 1}. ${s}</span>
                    `).join('')}
                </div>
                <p style="margin-top: 15px; font-size: 0.9rem; color: #64748b;">
                    场景预设目前为系统内置，如需自定义场景，请联系开发者。
                </p>
            </div>
        `;
    } catch (error) {
        console.error('加载场景失败:', error);
    }
}

function openModelModal() {
    editingModelId = null;
    document.getElementById('model-modal-title').textContent = '添加模型配置';
    document.getElementById('model-form').reset();
    document.getElementById('model-id').value = '';
    showModal('model-modal');
}

function editModelConfig(id) {
    api.config.models.get(id)
        .then(config => {
            editingModelId = id;
            document.getElementById('model-modal-title').textContent = '编辑模型配置';
            document.getElementById('model-id').value = config.id;
            document.getElementById('model-name').value = config.name;
            document.getElementById('model-api-base').value = config.api_base;
            document.getElementById('model-model-id').value = config.model_id;
            document.getElementById('model-is-default').checked = config.is_default;
            document.getElementById('model-api-key').placeholder = '保留原值请留空';
            showModal('model-modal');
        })
        .catch(error => {
            console.error('获取配置失败:', error);
            showToast('获取配置失败，请重试', 'error');
        });
}

async function saveModelConfig() {
    const name = document.getElementById('model-name').value.trim();
    const apiBase = document.getElementById('model-api-base').value.trim();
    const apiKey = document.getElementById('model-api-key').value.trim();
    const modelId = document.getElementById('model-model-id').value.trim();
    const isDefault = document.getElementById('model-is-default').checked;
    
    if (!name || !apiBase || !modelId) {
        showToast('请填写所有必填项', 'error');
        return;
    }
    
    if (!editingModelId && !apiKey) {
        showToast('请输入 API Key', 'error');
        return;
    }
    
    const data = {
        name,
        api_base: apiBase,
        model_id: modelId,
        is_default
    };
    
    if (apiKey) {
        data.api_key = apiKey;
    }
    
    try {
        if (editingModelId) {
            await api.config.models.update(editingModelId, data);
            showToast('更新成功');
        } else {
            await api.config.models.create(data);
            showToast('创建成功');
        }
        
        hideModal('model-modal');
        await loadModelConfigs();
    } catch (error) {
        console.error('保存失败:', error);
        showToast('保存失败，请重试', 'error');
    }
}

async function deleteModelConfig(id) {
    if (!confirm('确定要删除这个配置吗？')) {
        return;
    }
    
    try {
        await api.config.models.delete(id);
        showToast('删除成功');
        await loadModelConfigs();
    } catch (error) {
        console.error('删除失败:', error);
        showToast('删除失败，请重试', 'error');
    }
}
