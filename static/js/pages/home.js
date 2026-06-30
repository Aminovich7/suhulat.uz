const Pages = {};

Pages.home = async (_params, searchParams) => {
  const params = {
    search: searchParams.get("search") || "",
    category: searchParams.get("category") || "",
    region: searchParams.get("region") || "",
    listing_type: searchParams.get("listing_type") || "",
    seller_type: searchParams.get("seller_type") || "",
    price_min: searchParams.get("price_min") || "",
    price_max: searchParams.get("price_max") || "",
    page: searchParams.get("page") || "1",
  };

  const { regions, categories } = await Components.loadCatalog();

  let filterLabel = "";
  if (params.seller_type) {
    filterLabel = Utils.sellerTypeLabel(params.seller_type);
  } else if (params.category) {
    try {
      const cat = await Api.getCategory(params.category);
      filterLabel = cat.name_uz;
    } catch { /* ignore */ }
  } else if (params.region) {
    try {
      const reg = await Api.getRegion(params.region);
      filterLabel = reg.name_uz;
    } catch { /* ignore */ }
  }

  const data = await Api.getListings(params);
  const listings = data.results || data;
  const totalPages = data.count ? Math.ceil(data.count / 20) : 1;
  const page = Number(params.page) || 1;

  const sellerTabs = [
    { value: "", label: "Hammasi" },
    { value: "surplus", label: "Hosil" },
    { value: "maker", label: "Hunarmand" },
    { value: "wholesale", label: "Optom" },
  ];
  const tabsHtml = sellerTabs.map((tab) => {
    const active = params.seller_type === tab.value ? "active" : "";
    const q = { ...params, seller_type: tab.value || undefined, page: undefined };
    if (!tab.value) delete q.seller_type;
    const href = Utils.queryString(q) ? `/${Utils.queryString(q)}` : "/";
    return `<a href="${href}" class="tab ${active}" data-link>${tab.label}</a>`;
  }).join("");

  return `
    <section class="hero">
      <h1>Suhulat bozori</h1>
      <p>Ortiqcha mahsulot, ishlab chiqaruvchi va ulgurji savdo — O'zbekiston bo'ylab.</p>
    </section>
    <div class="layout-with-sidebar">
      <aside class="filters-panel">
        <h3>Filtrlar</h3>
        <form id="filters-form" class="form-grid">
          <div class="form-field">
            <label for="f-search">Qidiruv</label>
            <input type="search" id="f-search" name="search" value="${Utils.escapeHtml(params.search)}">
          </div>
          <div class="form-field">
            <label for="f-category">Kategoriya</label>
            <select id="f-category" name="category">${Components.categoryOptions(categories, params.category)}</select>
          </div>
          <div class="form-field">
            <label for="f-region">Viloyat</label>
            <select id="f-region" name="region">
              <option value="">Barcha viloyatlar</option>
              ${Components.regionOptions(regions, params.region)}
            </select>
          </div>
          <div class="form-field">
            <label for="f-type">Narx turi</label>
            <select id="f-type" name="listing_type">
              <option value="">Hammasi</option>
              <option value="fixed" ${params.listing_type === "fixed" ? "selected" : ""}>Belgilangan</option>
              <option value="negotiable" ${params.listing_type === "negotiable" ? "selected" : ""}>Kelishiladi</option>
            </select>
          </div>
          <div class="form-field">
            <label for="f-min">Min narx</label>
            <input type="number" id="f-min" name="price_min" value="${Utils.escapeHtml(params.price_min)}">
          </div>
          <div class="form-field">
            <label for="f-max">Max narx</label>
            <input type="number" id="f-max" name="price_max" value="${Utils.escapeHtml(params.price_max)}">
          </div>
          <button type="submit" class="btn btn-primary btn-block">Qo'llash</button>
        </form>
      </aside>
      <section>
        <nav class="tabs seller-type-tabs" aria-label="Sotuvchi turi">
          ${tabsHtml}
        </nav>
        <div class="page-header">
          <h1>E'lonlar ${filterLabel ? `— ${Utils.escapeHtml(filterLabel)}` : ""} ${data.count != null ? `<span class="listing-meta">(${data.count})</span>` : ""}</h1>
        </div>
        ${Components.listingGrid(listings)}
        ${Components.pagination(page, totalPages)}
      </section>
    </div>`;
};

Pages.homeMount = (app) => {
  const form = app.querySelector("#filters-form");
  form?.addEventListener("submit", (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const q = Object.fromEntries(new URLSearchParams(location.search));
    fd.forEach((v, k) => { if (v) q[k] = v; });
    delete q.page;
    Router.navigate("/", q);
  });

  Components.bindListingCards(app);
  Components.bindPagination(app, (p) => {
    const q = Object.fromEntries(new URLSearchParams(location.search));
    q.page = p;
    Router.navigate("/", q);
  });
};
