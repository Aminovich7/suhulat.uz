const Components = {
  listingCard(listing) {
    const img = listing.primary_image
      ? `<img src="${Utils.escapeHtml(listing.primary_image)}" alt="" loading="lazy">`
      : `<div class="placeholder">📦</div>`;
    const typeClass = listing.listing_type === "negotiable" ? "tag-negotiable" : "tag-fixed";
    const price = listing.listing_type === "negotiable"
      ? "Kelishiladi"
      : Utils.formatPrice(listing.price, listing.currency);

    return `
      <article class="listing-card" data-listing-id="${listing.id}">
        <div class="listing-card-image">${img}</div>
        <div class="listing-card-body">
          <span class="tag ${typeClass}">${Utils.listingTypeLabel(listing.listing_type)}</span>
          <h3>${Utils.escapeHtml(listing.title)}</h3>
          <div class="listing-price">${price}</div>
          <div class="listing-meta">
            ${Utils.escapeHtml(listing.seller_name || "")} ·
            ${Utils.escapeHtml(listing.region?.name_uz || "")}, ${Utils.escapeHtml(listing.district || "")}
          </div>
        </div>
      </article>`;
  },

  listingGrid(listings) {
    if (!listings.length) {
      return `<div class="empty-state"><h3>E'lonlar topilmadi</h3><p>Filtrlarni o'zgartirib ko'ring.</p></div>`;
    }
    return `<div class="listing-grid">${listings.map((l) => this.listingCard(l)).join("")}</div>`;
  },

  pagination(page, totalPages, onPage) {
    if (totalPages <= 1) return "";
    const prev = page > 1 ? `<button class="btn btn-outline btn-sm" data-page="${page - 1}">Oldingi</button>` : "";
    const next = page < totalPages ? `<button class="btn btn-outline btn-sm" data-page="${page + 1}">Keyingi</button>` : "";
    return `
      <div class="pagination" data-pagination>
        ${prev}
        <span>Sahifa ${page} / ${totalPages}</span>
        ${next}
      </div>`;
  },

  bindPagination(container, callback) {
    container.querySelectorAll("[data-page]").forEach((btn) => {
      btn.addEventListener("click", () => callback(Number(btn.dataset.page)));
    });
  },

  bindListingCards(container) {
    container.querySelectorAll(".listing-card").forEach((card) => {
      card.addEventListener("click", () => {
        Router.navigate(`/listings/${card.dataset.listingId}`);
      });
    });
  },

  regionOptions(regions, selected = "") {
    return regions.map((r) =>
      `<option value="${r.id}" ${String(r.id) === String(selected) ? "selected" : ""}>${Utils.escapeHtml(r.name_uz)}</option>`
    ).join("");
  },

  categoryOptions(categories, selected = "", includeAll = true) {
    let html = includeAll ? `<option value="">Barcha kategoriyalar</option>` : `<option value="">Tanlang</option>`;
    categories.forEach((cat) => {
      html += `<option value="${cat.id}" ${String(cat.id) === String(selected) ? "selected" : ""}>${Utils.escapeHtml(cat.name_uz)}</option>`;
      (cat.children || []).forEach((child) => {
        html += `<option value="${child.id}" ${String(child.id) === String(selected) ? "selected" : ""}>— ${Utils.escapeHtml(child.name_uz)}</option>`;
      });
    });
    return html;
  },

  orderStatusSteps(current) {
    const steps = ["pending", "confirmed", "fulfilling", "delivered", "completed"];
    const idx = steps.indexOf(current);
    return steps.map((s, i) => {
      let cls = "status-step";
      if (i < idx) cls += " done";
      if (i === idx) cls += " current";
      return `<span class="${cls}">${Utils.statusLabel(s)}</span>`;
    }).join("");
  },

  reviewList(reviews) {
    if (!reviews.length) return `<p class="listing-meta">Hali sharhlar yo'q.</p>`;
    return reviews.map((r) => `
      <div class="review-item">
        <div class="stars">${Utils.stars(r.rating)}</div>
        <strong>${Utils.escapeHtml(r.reviewer_name)}</strong>
        <span class="listing-meta"> · ${Utils.formatDate(r.created_at)}</span>
        <p>${Utils.escapeHtml(r.comment || "")}</p>
      </div>`).join("");
  },

  loading() {
    return `<div class="loading-screen"><div class="spinner"></div><p>Yuklanmoqda...</p></div>`;
  },

  async loadCatalog() {
    const [regions, categories] = await Promise.all([
      Api.getRegions(),
      Api.getCategories(),
    ]);
    return { regions, categories };
  },
};
