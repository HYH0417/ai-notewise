const API_BASE = "/api";

function getUrlParam(name) {
    return new URLSearchParams(window.location.search).get(name);
}

async function requestJson(url, options = {}) {
    const response = await fetch(`${API_BASE}${url}`, options);
    if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `HTTP ${response.status}`);
    }
    return response.json();
}

const api = {
    get: (url) => requestJson(url),
    post: (url, data = {}) => requestJson(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    }),
    put: (url, data = {}) => requestJson(url, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    }),
    delete: (url) => requestJson(url, { method: "DELETE" }),
};

api.prompts = {
    list(params = {}) {
        const filtered = Object.fromEntries(
            Object.entries(params).filter(([, value]) => value !== "" && value !== null && value !== undefined),
        );
        return api.get(`/prompts/?${new URLSearchParams(filtered)}`);
    },
    get: (id) => api.get(`/prompts/${id}`),
    create: (data) => api.post("/prompts/", data),
    update: (id, data) => api.put(`/prompts/${id}`, data),
    delete: (id) => api.delete(`/prompts/${id}`),
    copy: (id) => api.post(`/prompts/${id}/copy`),
    versions: {
        create: (promptId, data) => api.post(`/prompts/${promptId}/versions`, data),
        update: (promptId, versionId, data) => api.put(`/prompts/${promptId}/versions/${versionId}`, data),
    },
    favorite: {
        toggle: (id) => api.post(`/prompts/${id}/favorite`),
        check: (id) => api.get(`/prompts/${id}/favorite`),
        list(params = {}) {
            return api.get(`/prompts/favorites/list?${new URLSearchParams(params)}`);
        },
        batchCheck(ids) {
            return api.get(`/prompts/favorites/check?prompt_ids=${ids.join(",")}`);
        },
    },
};

api.search = {
    semantic: (data) => api.post("/search/", data),
    simple: (query, params = {}) => api.get(`/search/simple?${new URLSearchParams({ query, ...params })}`),
};

api.config = {
    dashboardStats: () => api.get("/config/dashboard-stats"),
    scenarios: () => api.get("/config/scenarios"),
    patterns: () => api.get("/config/patterns"),
    detectPatterns: (content) => api.post("/config/detect-patterns", { content }),
};

function escapeHtml(value = "") {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function formatDate(dateString) {
    if (!dateString) return "";
    return new Date(dateString).toLocaleString("zh-CN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    });
}

function renderTags(tags = []) {
    return tags.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("");
}

function renderSkillCard(skill) {
    const version = skill.versions?.find((item) => item.id === skill.current_version_id) || skill.versions?.[0];
    const excerpt = version?.content ? version.content.replace(/\s+/g, " ").slice(0, 220) : "";
    return `
        <article class="skill-card" data-id="${skill.id}">
            <div class="skill-card__top">
                <div>
                    <p class="eyebrow">${escapeHtml(skill.scenario)}</p>
                    <h3>${escapeHtml(skill.title)}</h3>
                </div>
                <button class="icon-btn favorite-btn" data-favorite-id="${skill.id}" title="收藏">☆</button>
            </div>
            <p>${escapeHtml(excerpt)}${excerpt.length >= 220 ? "..." : ""}</p>
            <div class="tag-row">${renderTags(skill.tags || [])}</div>
            <div class="meta-row">
                <span>${escapeHtml(skill.model || "General agent")}</span>
                <span>${skill.usage_count || 0} uses</span>
            </div>
        </article>
    `;
}

async function hydrateFavoriteButtons(items) {
    if (!items.length) return;
    const ids = items.map((item) => item.id);
    const state = await api.prompts.favorite.batchCheck(ids);
    document.querySelectorAll("[data-favorite-id]").forEach((button) => {
        const id = button.dataset.favoriteId;
        button.textContent = state[id] ? "★" : "☆";
        button.classList.toggle("is-active", Boolean(state[id]));
    });
}

async function toggleFavoriteFromButton(button) {
    const result = await api.prompts.favorite.toggle(button.dataset.favoriteId);
    button.textContent = result.is_favorite ? "★" : "☆";
    button.classList.toggle("is-active", result.is_favorite);
    showToast(result.is_favorite ? "已收藏" : "已取消收藏");
}

function showToast(message, type = "success") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2400);
}

document.addEventListener("click", async (event) => {
    const favoriteButton = event.target.closest("[data-favorite-id]");
    if (favoriteButton) {
        event.stopPropagation();
        await toggleFavoriteFromButton(favoriteButton);
        return;
    }

    const card = event.target.closest(".skill-card");
    if (card) {
        window.location.href = `/prompt-detail?id=${card.dataset.id}`;
    }
});
