let currentSkill = null;

document.addEventListener("DOMContentLoaded", loadSkill);

async function loadSkill() {
    const id = getUrlParam("id");
    const container = document.getElementById("detail-container");
    if (!id) {
        container.innerHTML = '<div class="empty-state">缺少 Skill ID</div>';
        return;
    }

    try {
        currentSkill = await api.prompts.get(id);
        const version = currentSkill.versions?.find((item) => item.id === currentSkill.current_version_id)
            || currentSkill.versions?.[0];
        const favorite = await api.prompts.favorite.check(id);

        container.innerHTML = `
            <section class="page-head">
                <div>
                    <p class="eyebrow">${escapeHtml(currentSkill.scenario)}</p>
                    <h2>${escapeHtml(currentSkill.title)}</h2>
                    <p>${escapeHtml(currentSkill.model || "General agent skill")}</p>
                </div>
                <div class="toolbar">
                    <button class="icon-btn ${favorite.is_favorite ? "is-active" : ""}" data-favorite-id="${currentSkill.id}">${favorite.is_favorite ? "★" : "☆"}</button>
                    <a class="btn btn-secondary" href="/api/prompts/${currentSkill.id}/download.zip">下载 ZIP</a>
                    <button class="btn btn-primary" id="copy-btn">复制 SKILL.md</button>
                    <a class="btn btn-outline" href="/prompt-edit?id=${currentSkill.id}">编辑</a>
                </div>
            </section>
            <section class="panel">
                <div class="tag-row">${renderTags(currentSkill.tags || [])}</div>
                <div class="meta-row">
                    <span>创建：${formatDate(currentSkill.created_at)}</span>
                    <span>更新：${formatDate(currentSkill.updated_at)}</span>
                    <span>使用：${currentSkill.usage_count || 0}</span>
                </div>
            </section>
            <section class="panel">
                <h3 style="margin-bottom: 12px;">Skill 内容</h3>
                <pre class="content-block">${escapeHtml(version?.content || "")}</pre>
            </section>
            <section class="panel">
                <h3 style="margin-bottom: 12px;">版本记录</h3>
                <div class="grid">${renderVersions(currentSkill.versions || [])}</div>
            </section>
        `;
        document.getElementById("copy-btn").addEventListener("click", copySkill);
    } catch (error) {
        container.innerHTML = '<div class="empty-state">加载 Skill 失败</div>';
    }
}

function renderVersions(versions) {
    if (!versions.length) return '<div class="empty-state">暂无版本</div>';
    return versions.slice().reverse().map((version) => `
        <div class="panel" style="margin-bottom:0;">
            <strong>${escapeHtml(version.version_number)}</strong>
            <span style="color:#718096; margin-left:8px;">${formatDate(version.created_at)}</span>
            ${version.change_note ? `<p>${escapeHtml(version.change_note)}</p>` : ""}
        </div>
    `).join("");
}

async function copySkill() {
    const result = await api.prompts.copy(currentSkill.id);
    await navigator.clipboard.writeText(result.content || "");
    showToast("已复制 Skill 内容");
    await loadSkill();
}
