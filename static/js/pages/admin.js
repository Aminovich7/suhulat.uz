Pages.admin = async (params, searchParams) => {
  const tab = searchParams.get("tab") || "dashboard";
  const stats = tab === "dashboard" ? await Api.getAdminStats() : null;

  const tabs = [
    { id: "dashboard", label: "Statistika" },
    { id: "sellers", label: "Sotuvchilar" },
    { id: "listings", label: "E'lonlar" },
    { id: "reviews", label: "Sharhlar" },
  ];

  const tabNav = tabs
    .map(
      (t) =>
        `<a href="/admin?tab=${t.id}" data-link class="btn btn-sm ${tab === t.id ? "btn-primary" : "btn-outline"}">${t.label}</a>`
    )
    .join(" ");

  let content = "";
  if (tab === "dashboard") {
    const byStatus = stats.listings_by_status || {};
    content = `
      <div class="admin-stats">
        <div class="stat-card"><strong>${stats.sellers_pending}</strong><span>Tasdiqlanmagan sotuvchilar</span></div>
        <div class="stat-card"><strong>${stats.sellers_total}</strong><span>Jami sotuvchilar</span></div>
        <div class="stat-card"><strong>${stats.listings_total}</strong><span>Jami e'lonlar</span></div>
        <div class="stat-card"><strong>${stats.reviews_total}</strong><span>Jami sharhlar</span></div>
      </div>
      <div class="card" style="margin-top:1rem">
        <h3>E'lonlar holati bo'yicha</h3>
        <table class="data-table">
          <thead><tr><th>Holat</th><th>Soni</th></tr></thead>
          <tbody>
            ${Object.entries(byStatus)
              .map(
                ([status, count]) =>
                  `<tr><td>${Utils.statusLabel(status)}</td><td>${count}</td></tr>`
              )
              .join("")}
          </tbody>
        </table>
      </div>`;
  } else if (tab === "sellers") {
    const verified = searchParams.get("is_verified") ?? "false";
    const data = await Api.getAdminSellers({ is_verified: verified, page_size: 50 });
    const sellers = data.results || [];
    content = `
      <div class="filter-bar">
        <label>Holat:
          <select id="admin-seller-filter">
            <option value="false" ${verified === "false" ? "selected" : ""}>Tasdiqlanmagan</option>
            <option value="true" ${verified === "true" ? "selected" : ""}>Tasdiqlangan</option>
            <option value="" ${verified === "" ? "selected" : ""}>Barchasi</option>
          </select>
        </label>
      </div>
      <div class="card">
        <table class="data-table">
          <thead>
            <tr><th>Ism</th><th>Telefon</th><th>Turi</th><th>Holat</th><th>Sana</th><th></th></tr>
          </thead>
          <tbody>
            ${sellers.length ? sellers.map((s) => `
              <tr data-seller-id="${s.user_id}">
                <td>${Utils.escapeHtml(s.seller_name)}<br><small>${Utils.escapeHtml(s.full_name)}</small></td>
                <td>${Utils.escapeHtml(s.phone)}</td>
                <td>${Utils.sellerTypeLabel(s.seller_type)}</td>
                <td>${s.is_verified ? "Tasdiqlangan" : "Kutilmoqda"}${!s.is_active ? " (bloklangan)" : ""}</td>
                <td>${Utils.formatDate(s.date_joined)}</td>
                <td class="admin-actions">
                  ${!s.is_verified ? `<button class="btn btn-sm btn-primary" data-seller-approve="${s.user_id}">Tasdiqlash</button>` : ""}
                  ${s.is_verified ? `<button class="btn btn-sm btn-outline" data-seller-reject="${s.user_id}">Bekor qilish</button>` : `<button class="btn btn-sm btn-danger" data-seller-reject="${s.user_id}" data-deactivate="1">Rad etish</button>`}
                </td>
              </tr>`).join("") : `<tr><td colspan="6">Ma'lumot yo'q</td></tr>`}
          </tbody>
        </table>
      </div>`;
  } else if (tab === "listings") {
    const status = searchParams.get("status") || "";
    const params = { page_size: 50 };
    if (status) params.status = status;
    const data = await Api.getAdminListings(params);
    const listings = data.results || [];
    content = `
      <div class="filter-bar">
        <label>Holat:
          <select id="admin-listing-filter">
            <option value="">Barchasi</option>
            ${["active", "paused", "sold_out", "expired", "deleted"].map((s) =>
              `<option value="${s}" ${status === s ? "selected" : ""}>${Utils.statusLabel(s)}</option>`
            ).join("")}
          </select>
        </label>
      </div>
      <div class="card">
        <table class="data-table">
          <thead>
            <tr><th>Sarlavha</th><th>Sotuvchi</th><th>Narx</th><th>Holat</th><th>Sana</th><th></th></tr>
          </thead>
          <tbody>
            ${listings.length ? listings.map((l) => `
              <tr>
                <td><a href="/listings/${l.id}" data-link>${Utils.escapeHtml(l.title)}</a></td>
                <td>${Utils.escapeHtml(l.seller_name || l.seller_phone || "—")}</td>
                <td>${Utils.formatPrice(l.price, l.currency)}</td>
                <td>${Utils.statusLabel(l.status)}</td>
                <td>${Utils.formatDate(l.created_at)}</td>
                <td class="admin-actions">
                  ${l.status !== "active" ? `<button class="btn btn-sm btn-primary" data-listing-moderate="${l.id}" data-status="active">Faollashtirish</button>` : ""}
                  ${l.status !== "paused" ? `<button class="btn btn-sm btn-outline" data-listing-moderate="${l.id}" data-status="paused">To'xtatish</button>` : ""}
                  ${l.status !== "deleted" ? `<button class="btn btn-sm btn-danger" data-listing-moderate="${l.id}" data-status="deleted">O'chirish</button>` : ""}
                </td>
              </tr>`).join("") : `<tr><td colspan="6">Ma'lumot yo'q</td></tr>`}
          </tbody>
        </table>
      </div>`;
  } else if (tab === "reviews") {
    const data = await Api.getAdminReviews({ page_size: 50 });
    const reviews = data.results || [];
    content = `
      <div class="card">
        <table class="data-table">
          <thead>
            <tr><th>Buyurtma</th><th>Muallif</th><th>Qabul qiluvchi</th><th>Baho</th><th>Sharh</th><th></th></tr>
          </thead>
          <tbody>
            ${reviews.length ? reviews.map((r) => `
              <tr>
                <td>${Utils.escapeHtml(r.listing_title || r.order)}</td>
                <td>${Utils.escapeHtml(r.reviewer_name)}</td>
                <td>${Utils.escapeHtml(r.reviewee_name)}</td>
                <td>${r.rating}/5</td>
                <td>${Utils.escapeHtml(r.comment || "—")}</td>
                <td><button class="btn btn-sm btn-danger" data-review-delete="${r.id}">O'chirish</button></td>
              </tr>`).join("") : `<tr><td colspan="6">Ma'lumot yo'q</td></tr>`}
          </tbody>
        </table>
      </div>`;
  }

  return `
    <div class="page-header"><h1>Admin panel</h1></div>
    <div class="admin-tabs" style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:1rem">${tabNav}</div>
    ${content}`;
};

Pages.adminMount = (app) => {
  app.querySelector("#admin-seller-filter")?.addEventListener("change", (e) => {
    const val = e.target.value;
    Router.navigate("/admin", { tab: "sellers", ...(val !== "" ? { is_verified: val } : {}) });
  });

  app.querySelector("#admin-listing-filter")?.addEventListener("change", (e) => {
    const val = e.target.value;
    Router.navigate("/admin", { tab: "listings", ...(val ? { status: val } : {}) });
  });

  app.addEventListener("click", async (e) => {
    const approveBtn = e.target.closest("[data-seller-approve]");
    if (approveBtn) {
      e.preventDefault();
      try {
        await Api.approveSeller(approveBtn.dataset.sellerApprove);
        toast("Sotuvchi tasdiqlandi", "success");
        Router.navigate("/admin", { tab: "sellers", is_verified: "false" });
      } catch (err) {
        toast(Utils.parseApiErrors(err.data || {})[0] || "Xatolik", "error");
      }
      return;
    }

    const rejectBtn = e.target.closest("[data-seller-reject]");
    if (rejectBtn) {
      e.preventDefault();
      if (!confirm("Sotuvchini rad etasizmi?")) return;
      try {
        await Api.rejectSeller(rejectBtn.dataset.sellerReject, {
          deactivate_user: rejectBtn.dataset.deactivate === "1",
        });
        toast("Sotuvchi rad etildi", "success");
        Router.navigate("/admin", { tab: "sellers" });
      } catch (err) {
        toast(Utils.parseApiErrors(err.data || {})[0] || "Xatolik", "error");
      }
      return;
    }

    const modBtn = e.target.closest("[data-listing-moderate]");
    if (modBtn) {
      e.preventDefault();
      try {
        await Api.moderateListing(modBtn.dataset.listingModerate, modBtn.dataset.status);
        toast("E'lon yangilandi", "success");
        Router.render(location.pathname + location.search);
      } catch (err) {
        toast(Utils.parseApiErrors(err.data || {})[0] || "Xatolik", "error");
      }
      return;
    }

    const delBtn = e.target.closest("[data-review-delete]");
    if (delBtn) {
      e.preventDefault();
      if (!confirm("Sharhni o'chirasizmi?")) return;
      try {
        await Api.deleteAdminReview(delBtn.dataset.reviewDelete);
        toast("Sharh o'chirildi", "success");
        Router.navigate("/admin", { tab: "reviews" });
      } catch (err) {
        toast(Utils.parseApiErrors(err.data || {})[0] || "Xatolik", "error");
      }
    }
  });
};
