document.addEventListener("DOMContentLoaded", loadFavorites);

async function loadFavorites() {
    const container = document.getElementById("favorite-list");
    container.innerHTML = '<div class="loading">加载中...</div>';
    const result = await api.prompts.favorite.list({ skip: 0, limit: 100 });
    document.getElementById("favorite-count").textContent = `${result.total || 0} 条`;
    const items = result.items || [];
    if (!items.length) {
        container.innerHTML = '<div class="empty-state">还没有收藏的 Skills</div>';
        return;
    }
    container.innerHTML = items.map(renderSkillCard).join("");
    await hydrateFavoriteButtons(items);
}
