let currentTestId = null;
let currentRatingA = 0;
let currentRatingB = 0;

document.addEventListener('DOMContentLoaded', async () => {
    await loadPrompts();
    await loadModelConfigs();
    await loadTestHistory();
    
    setupRatingInputs();
});

async function loadPrompts() {
    try {
        const prompts = await api.prompts.list({ limit: 100 });
        
        const selectA = document.getElementById('prompt-a-select');
        const selectB = document.getElementById('prompt-b-select');
        
        prompts.forEach(p => {
            const optionA = document.createElement('option');
            optionA.value = p.id;
            optionA.textContent = p.title;
            selectA.appendChild(optionA);
            
            const optionB = document.createElement('option');
            optionB.value = p.id;
            optionB.textContent = p.title;
            selectB.appendChild(optionB);
        });
    } catch (error) {
        console.error('加载提示词列表失败:', error);
    }
}

async function loadModelConfigs() {
    try {
        const configs = await api.config.models.list();
        
        const select = document.getElementById('model-config-select');
        
        configs.forEach(c => {
            const option = document.createElement('option');
            option.value = c.id;
            option.textContent = `${c.name}${c.is_default ? ' (默认)' : ''}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载模型配置失败:', error);
    }
}

async function loadPromptAVersions() {
    const promptId = document.getElementById('prompt-a-select').value;
    await loadVersions(promptId, 'version-a-select');
}

async function loadPromptBVersions() {
    const promptId = document.getElementById('prompt-b-select').value;
    await loadVersions(promptId, 'version-b-select');
}

async function loadVersions(promptId, selectId) {
    const select = document.getElementById(selectId);
    select.innerHTML = '<option value="">请选择版本</option>';
    
    if (!promptId) return;
    
    try {
        const versions = await api.prompts.versions.list(promptId);
        
        versions.forEach(v => {
            const option = document.createElement('option');
            option.value = v.id;
            option.textContent = `版本 ${v.version_number}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载版本失败:', error);
    }
}

function setupRatingInputs() {
    setupRatingInput('rating-a-input', (rating) => { currentRatingA = rating; });
    setupRatingInput('rating-b-input', (rating) => { currentRatingB = rating; });
}

function setupRatingInput(elementId, callback) {
    const container = document.getElementById(elementId);
    const stars = container.querySelectorAll('.star');
    
    stars.forEach(star => {
        star.addEventListener('click', () => {
            const rating = parseInt(star.dataset.rating);
            
            stars.forEach(s => {
                s.classList.remove('filled');
                if (parseInt(s.dataset.rating) <= rating) {
                    s.classList.add('filled');
                }
            });
            
            callback(rating);
        });
    });
}

async function runABTest() {
    const versionAId = document.getElementById('version-a-select').value;
    const versionBId = document.getElementById('version-b-select').value;
    const testInput = document.getElementById('test-input').value.trim();
    const modelConfigId = document.getElementById('model-config-select').value;
    
    if (!versionAId || !versionBId || !testInput) {
        showToast('请填写所有必填项', 'error');
        return;
    }
    
    if (versionAId === versionBId) {
        showToast('请选择不同的版本进行对比', 'error');
        return;
    }
    
    const btn = document.querySelector('.btn-primary');
    btn.textContent = '测试中...';
    btn.disabled = true;
    
    try {
        const result = await api.abTest.run({
            version_a_id: parseInt(versionAId),
            version_b_id: parseInt(versionBId),
            test_input: testInput,
            model_config_id: modelConfigId ? parseInt(modelConfigId) : null
        });
        
        currentTestId = result.id;
        currentRatingA = 0;
        currentRatingB = 0;
        
        document.getElementById('output-a').textContent = result.output_a || '无输出';
        document.getElementById('output-b').textContent = result.output_b || '无输出';
        
        document.getElementById('rating-a-input').querySelectorAll('.star').forEach(s => s.classList.remove('filled'));
        document.getElementById('rating-b-input').querySelectorAll('.star').forEach(s => s.classList.remove('filled'));
        
        document.getElementById('evaluation').value = '';
        document.getElementById('results-card').style.display = 'block';
        
        showToast('A/B 测试完成');
    } catch (error) {
        console.error('A/B 测试失败:', error);
        showToast('测试失败，请检查模型配置', 'error');
    } finally {
        btn.textContent = '运行 A/B 测试';
        btn.disabled = false;
    }
}

async function saveTestResult() {
    if (!currentTestId) {
        showToast('请先运行测试', 'error');
        return;
    }
    
    const evaluation = document.getElementById('evaluation').value.trim();
    
    try {
        await api.abTest.update(currentTestId, {
            rating_a: currentRatingA || null,
            rating_b: currentRatingB || null,
            evaluation
        });
        
        showToast('测试结果保存成功');
        await loadTestHistory();
    } catch (error) {
        console.error('保存测试结果失败:', error);
        showToast('保存失败，请重试', 'error');
    }
}

function resetTest() {
    currentTestId = null;
    currentRatingA = 0;
    currentRatingB = 0;
    
    document.getElementById('output-a').textContent = '';
    document.getElementById('output-b').textContent = '';
    document.getElementById('evaluation').value = '';
    document.getElementById('rating-a-input').querySelectorAll('.star').forEach(s => s.classList.remove('filled'));
    document.getElementById('rating-b-input').querySelectorAll('.star').forEach(s => s.classList.remove('filled'));
    document.getElementById('results-card').style.display = 'none';
}

async function loadTestHistory() {
    try {
        const tests = await api.abTest.list({ limit: 20 });
        const container = document.getElementById('test-history');
        
        if (tests.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="icon">📊</div>
                    <p>暂无测试记录</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = tests.map(test => `
            <div style="padding: 15px; border-bottom: 1px solid #e2e8f0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <strong>测试 #${test.id}</strong>
                    <span>${formatDate(test.created_at)}</span>
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>测试输入：</strong>${test.test_input.substring(0, 80)}${test.test_input.length > 80 ? '...' : ''}
                </div>
                <div style="display: flex; gap: 20px;">
                    <div>
                        <span class="tag tag-primary">版本 A</span>
                        ${renderStars(test.rating_a)}
                    </div>
                    <div>
                        <span class="tag tag-success">版本 B</span>
                        ${renderStars(test.rating_b)}
                    </div>
                </div>
                ${test.evaluation ? `
                    <div style="margin-top: 10px; padding: 10px; background: #f8fafc; border-radius: 6px;">
                        <strong>评价：</strong>${test.evaluation}
                    </div>
                ` : ''}
            </div>
        `).join('');
    } catch (error) {
        console.error('加载测试历史失败:', error);
    }
}
