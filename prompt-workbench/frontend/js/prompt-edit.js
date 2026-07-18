let editMode = false;

document.addEventListener("DOMContentLoaded", async () => {
    await loadScenarios();
    addFolderImportUI();

    const id = getUrlParam("id");
    if (id) {
        editMode = true;
        document.getElementById("page-title").textContent = "编辑 Agent Skill";
        await loadSkillForEdit(id);
    }

    document.getElementById("detect-btn").addEventListener("click", detectTags);
    document.getElementById("prompt-form").addEventListener("submit", saveSkill);
});

async function loadScenarios() {
    const select = document.getElementById("scenario");
    const data = await api.config.scenarios();
    select.innerHTML = '<option value="">请选择分类</option>';
    (data.scenarios || []).forEach((scenario) => {
        const option = document.createElement("option");
        option.value = scenario;
        option.textContent = scenario;
        select.appendChild(option);
    });
}

function addFolderImportUI() {
    const form = document.getElementById("prompt-form");
    const importPanel = document.createElement("section");
    importPanel.className = "panel";
    importPanel.innerHTML = `
        <h3 style="margin-bottom:10px;">导入完整 Skill 文件夹</h3>
        <div class="toolbar">
            <input id="folder-input" type="file" webkitdirectory directory multiple class="form-control">
            <button id="folder-import-btn" type="button" class="btn btn-secondary">上传文件夹</button>
        </div>
        <p style="color:#718096;">会保留目录结构；如果文件夹里有 SKILL.md 或 README.md，会自动作为 skill 内容。</p>
    `;
    form.before(importPanel);
    document.getElementById("folder-import-btn").addEventListener("click", importFolder);
}

async function importFolder() {
    const input = document.getElementById("folder-input");
    if (!input.files.length) {
        showToast("请选择一个文件夹", "error");
        return;
    }

    const formData = new FormData();
    for (const file of input.files) {
        formData.append("files", file, file.webkitRelativePath || file.name);
    }
    formData.append("title", document.getElementById("title").value.trim());
    formData.append("scenario", document.getElementById("scenario").value || "Agent Patterns");
    formData.append("tags", document.getElementById("tags").value.trim());
    formData.append("model", document.getElementById("model").value.trim());

    const response = await fetch("/api/prompts/import-folder", { method: "POST", body: formData });
    if (!response.ok) {
        showToast("文件夹上传失败", "error");
        return;
    }
    const skill = await response.json();
    showToast("文件夹已导入");
    window.location.href = `/prompt-detail?id=${skill.id}`;
}

async function loadSkillForEdit(id) {
    const skill = await api.prompts.get(id);
    const version = skill.versions?.find((item) => item.id === skill.current_version_id) || skill.versions?.[0];
    document.getElementById("prompt-id").value = skill.id;
    document.getElementById("title").value = skill.title;
    document.getElementById("scenario").value = skill.scenario;
    document.getElementById("model").value = skill.model || "";
    document.getElementById("tags").value = (skill.tags || []).join(", ");
    document.getElementById("content").value = version?.content || "";
}

async function detectTags() {
    const content = document.getElementById("content").value.trim();
    if (!content) return;
    const result = await api.config.detectPatterns(content);
    const current = document.getElementById("tags").value.split(",").map((item) => item.trim()).filter(Boolean);
    document.getElementById("tags").value = [...new Set([...current, ...(result.suggested_tags || [])])].join(", ");
    showToast("已识别标签");
}

async function saveSkill(event) {
    event.preventDefault();
    const title = document.getElementById("title").value.trim();
    const scenario = document.getElementById("scenario").value;
    const model = document.getElementById("model").value.trim();
    const content = document.getElementById("content").value.trim();
    const tags = document.getElementById("tags").value.split(",").map((item) => item.trim()).filter(Boolean);
    const changeNote = document.getElementById("change-note").value.trim();

    if (!title || !scenario || !content) {
        showToast("请填写必填项", "error");
        return;
    }

    if (editMode) {
        const id = document.getElementById("prompt-id").value;
        await api.prompts.update(id, { title, scenario, model: model || null, tags });
        await api.prompts.versions.create(id, { content, change_note: changeNote || "Updated skill content" });
        window.location.href = `/prompt-detail?id=${id}`;
    } else {
        const skill = await api.prompts.create({ title, scenario, model: model || null, tags, content, change_note: changeNote || "Initial skill" });
        window.location.href = `/prompt-detail?id=${skill.id}`;
    }
}
