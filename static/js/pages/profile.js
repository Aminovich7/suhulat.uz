Pages.profile = async () => {
  const user = Auth.getUser() || await Auth.fetchUser();
  const isBuyer = Auth.isBuyer();
  const isSeller = Auth.isSeller();

  let profileHtml = "";

  if (isBuyer) {
    const profile = await Api.getBuyerProfile();
    const { regions } = await Components.loadCatalog();
    profileHtml += `
      <div class="tab-panel active" id="buyer-panel">
        <form id="buyer-profile-form" class="form-grid" style="max-width:560px">
          <div class="form-field">
            <label>Viloyat</label>
            <select name="region_id">
              ${Components.regionOptions(regions, profile.region?.id || "")}
            </select>
          </div>
          <div class="form-field">
            <label>Tuman</label>
            <input name="district" value="${Utils.escapeHtml(profile.district || "")}">
          </div>
          <div class="checkbox-field">
            <input type="checkbox" id="biz-buyer" name="is_business_buyer" ${profile.is_business_buyer ? "checked" : ""}>
            <label for="biz-buyer">Biznes xaridor</label>
          </div>
          <div class="form-field" id="biz-name-field">
            <label>Kompaniya nomi</label>
            <input name="company_name" value="${Utils.escapeHtml(profile.company_name || "")}">
          </div>
          <div id="buyer-error"></div>
          <button type="submit" class="btn btn-primary">Saqlash</button>
        </form>
      </div>`;
  }

  if (isSeller) {
    const profile = await Api.getSellerProfile();
    const { regions } = await Components.loadCatalog();
    profileHtml += `
      <div class="tab-panel ${!isBuyer ? "active" : ""}" id="seller-panel">
        <form id="seller-profile-form" class="form-grid" style="max-width:560px">
          <div class="form-field">
            <label>Sotuvchi nomi</label>
            <input name="seller_name" value="${Utils.escapeHtml(profile.seller_name || "")}" required>
          </div>
          <div class="form-field">
            <label>Turi</label>
            <select name="seller_type">
              ${["surplus", "maker", "wholesale"].map((t) =>
                `<option value="${t}" ${profile.seller_type === t ? "selected" : ""}>${Utils.sellerTypeLabel(t)}</option>`
              ).join("")}
            </select>
          </div>
          <div class="form-field">
            <label>Viloyat</label>
            <select name="region_id">
              ${Components.regionOptions(regions, profile.region?.id || "")}
            </select>
          </div>
          <div class="form-field">
            <label>Tuman</label>
            <input name="district" value="${Utils.escapeHtml(profile.district || "")}">
          </div>
          <div class="form-field">
            <label>Tavsif</label>
            <textarea name="description">${Utils.escapeHtml(profile.description || "")}</textarea>
          </div>
          <p class="listing-meta">
            Tasdiqlangan: ${profile.is_verified ? "Ha ✓" : "Yo'q (admin kutmoqda)"} ·
            Reyting: ${Utils.stars(profile.rating)} (${profile.total_reviews} sharh)
          </p>
          <div id="seller-error"></div>
          <button type="submit" class="btn btn-primary">Saqlash</button>
        </form>
      </div>`;
  }

  const tabs = [];
  if (isBuyer) tabs.push(`<button class="tab active" data-tab="buyer-panel">Xaridor profili</button>`);
  if (isSeller) tabs.push(`<button class="tab ${!isBuyer ? "active" : ""}" data-tab="seller-panel">Sotuvchi profili</button>`);

  return `
    <div class="page-header">
      <h1>${Utils.escapeHtml(user.full_name)}</h1>
      <p>${Utils.escapeHtml(user.phone)} · ${user.role}</p>
    </div>
    ${tabs.length > 1 ? `<div class="tabs">${tabs.join("")}</div>` : ""}
    ${profileHtml}`;
};

Pages.profileMount = (app) => {
  app.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      app.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      app.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      app.querySelector(`#${tab.dataset.tab}`)?.classList.add("active");
    });
  });

  app.querySelector("#buyer-profile-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = app.querySelector("#buyer-error");
    errEl.innerHTML = "";
    const fd = new FormData(e.target);
    try {
      await Api.updateBuyerProfile({
        region_id: Number(fd.get("region_id")),
        district: fd.get("district"),
        is_business_buyer: app.querySelector("#biz-buyer").checked,
        company_name: fd.get("company_name") || "",
      });
      toast("Profil yangilandi", "success");
    } catch (err) {
      errEl.innerHTML = Utils.renderErrors(Utils.parseApiErrors(err.data));
    }
  });

  app.querySelector("#seller-profile-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = app.querySelector("#seller-error");
    errEl.innerHTML = "";
    const fd = new FormData(e.target);
    try {
      await Api.updateSellerProfile({
        seller_name: fd.get("seller_name"),
        seller_type: fd.get("seller_type"),
        region_id: Number(fd.get("region_id")),
        district: fd.get("district"),
        description: fd.get("description") || "",
      });
      await Auth.fetchUser();
      toast("Profil yangilandi", "success");
    } catch (err) {
      errEl.innerHTML = Utils.renderErrors(Utils.parseApiErrors(err.data));
    }
  });
};

Pages.publicSeller = async (params) => {
  const [data, reviewsData] = await Promise.all([
    Api.getPublicSeller(params.id),
    Api.getSellerReviews(params.id),
  ]);
  const profile = data.profile;
  const listings = data.listings || [];
  const reviews = reviewsData.results || reviewsData || data.reviews || [];

  return `
    <div class="page-header">
      <h1>${Utils.escapeHtml(profile.seller_name)}</h1>
      <p>${Utils.sellerTypeLabel(profile.seller_type)} · ${Utils.escapeHtml(profile.region?.name_uz || "")}, ${Utils.escapeHtml(profile.district || "")}</p>
      <p class="stars">${Utils.stars(profile.rating)} (${profile.total_reviews} sharh)</p>
    </div>
    ${profile.description ? `<div class="card card-body" style="margin-bottom:1.5rem"><p>${Utils.escapeHtml(profile.description)}</p></div>` : ""}
    <h2>E'lonlar</h2>
    ${Components.listingGrid(listings)}
    <h2 style="margin-top:2rem">Sharhlar</h2>
    <div class="card card-body">${Components.reviewList(reviews)}</div>`;
};

Pages.publicSellerMount = (app) => {
  Components.bindListingCards(app);
};
