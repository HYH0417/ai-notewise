let currentPage = 1;
const pageSize = 12;

document.addEventListener("DOMContentLoaded", async () => {
    await loadFilters();
    await loadPrompts();

    document.getElementById("search-btn").addEventListener("click", () => loadPrompts(false));
    document.getElementById("semantic-search-btn").addEventListener("click", runSemanticSearch);
    document.getElementById("search-input").addEventListener("keydown", (event) => {
        if (event.key === "Enter") loadPrompts(false);
    });
    document.getElementById("scenario-filter").addEventListener("change", () => loadPrompts(true));
    document.getElementById("pattern-filter").addEventListener("change", () => loadPrompts(true));
    document.getElementById("clear-filters").addEventListener("click", clearFilters);
    document.getElementById("prev-page").addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage -= 1;
            loadPrompts();
        }
    });
    document.getElementById("next-page").addEventListener("click", () => {
        currentPage += 1;
        loadPrompts();
    });
});

async function loadFilters() {
    const [scenarios, patterns] = await Promise.all([api.config.scenarios(), api.config.patterns()]);
    fillSelect("scenario-filter", scenarios.scenarios || []);
    fillSelect("pattern-filter", patterns.patterns || []);
}

function fillSelect(id, values) {
    const select = document.getElementById(id);
    values.forEach((value) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        select.appendChild(option);
    });
}

async function loadPrompts(reset = false) {
    if (reset) currentPage = 1;
    const container = document.getElementById("prompt-list");
    container.innerHTML = '<div class="loading">加载中...</div>';

    const query = document.getElementById("search-input").value.trim();
    if (query) {
        const results = await api.search.simple(query, { top_k: 50 });
        renderSearchResults(results);
        return;
    }

    const result = await api.prompts.list({
        skip: (currentPage - 1) * pageSize,
        limit: pageSize,
        scenario: document.getElementById("scenario-filter").value,
        pattern: document.getElementById("pattern-filter").value,
    });
    renderPromptList(result.items || [], result.total || 0);
}

function renderPromptList(items, total) {
    const container = document.getElementById("prompt-list");
    if (!items.length) {
        container.innerHTML = '<div class="empty-state">暂无 Skills，先导入一个文件夹或新增一条。</div>';
        document.getElementById("pagination").style.display = "none";
        return;
    }
    container.innerHTML = items.map(renderSkillCard).join("");
    hydrateFavoriteButtons(items);

    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    document.getElementById("pagination").style.display = totalPages > 1 ? "flex" : "none";
    document.getElementById("page-info").textContent = `${currentPage} / ${totalPages}，共 ${total} 条`;
}

function renderSearchResults(results) {
    const items = results.map((item) => ({
        id: item.prompt_id,
        title: item.title,
        scenario: item.scenario,
        model: `${Math.round((item.similarity || 0) * 100)}% match`,
        usage_count: 0,
        tags: [],
        versions: [{ id: 0, content: item.content }],
    }));
    renderPromptList(items, items.length);
    document.getElementById("pagination").style.display = "none";
}

async function runSemanticSearch() {
    const query = document.getElementById("search-input").value.trim();
    if (!query) {
        showToast("请输入搜索内容", "error");
        return;
    }
    const results = await api.search.semantic({ query, top_k: 50 });
    renderSearchResults(results);
}

function clearFilters() {
    document.getElementById("search-input").value = "";
    document.getElementById("scenario-filter").value = "";
    document.getElementById("pattern-filter").value = "";
    loadPrompts(true);
}
