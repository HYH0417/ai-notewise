document.addEventListener("DOMContentLoaded", async () => {
    await loadDashboard();

    document.getElementById("quick-search-btn").addEventListener("click", runQuickSearch);
    document.getElementById("quick-search").addEventListener("keydown", (event) => {
        if (event.key === "Enter") runQuickSearch();
    });
});

async function loadDashboard() {
    try {
        const data = await api.config.dashboardStats();
        const stats = data.stats;
        document.getElementById("total-prompts").textContent = stats.total_prompts;
        document.getElementById("weekly-new").textContent = stats.weekly_new;
        document.getElementById("avg-rating").textContent = stats.avg_rating;
        document.getElementById("popular-scenario").textContent = stats.popular_scenarios?.[0]?.scenario || "-";
        renderMiniList("recent-prompts", data.recent_prompts || []);
        renderMiniList("popular-prompts", data.popular_prompts || []);
    } catch (error) {
        showToast("加载总览失败", "error");
    }
}

function renderMiniList(id, items) {
    const container = document.getElementById(id);
    if (!items.length) {
        container.innerHTML = '<div class="empty-state">暂无 Skills</div>';
        return;
    }
    container.innerHTML = items.map((item) => renderSkillCard({ ...item, versions: [] })).join("");
}

async function runQuickSearch() {
    const query = document.getElementById("quick-search").value.trim();
    const container = document.getElementById("quick-search-results");
    if (!query) return;
    container.innerHTML = '<div class="loading">搜索中...</div>';

    try {
        const results = await api.search.semantic({ query, top_k: 6 });
        if (!results.length) {
            container.innerHTML = '<div class="empty-state">没有匹配的 Skill</div>';
            return;
        }
        container.innerHTML = results.map((item) => renderSkillCard({
            id: item.prompt_id,
            title: item.title,
            scenario: item.scenario,
            model: `${Math.round((item.similarity || 0) * 100)}% match`,
            usage_count: 0,
            tags: [],
            versions: [{ id: 0, content: item.content }],
        })).join("");
    } catch (error) {
        container.innerHTML = '<div class="empty-state">搜索失败</div>';
    }
}
