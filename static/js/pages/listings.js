Pages.listingDetail = async (params) => {
  const listing = await Api.getListing(params.id);
  const user = Auth.getUser();
  const isOwner = user && String(listing.seller_id) === String(user.id);
  const isFixed = listing.listing_type === "fixed";
  const isNegotiable = listing.listing_type === "negotiable";
  const isBuyer = Auth.isBuyer();
  const isActive = listing.status === "active";

  const mainImage = listing.images?.[0]?.image || listing.primary_image;
  const thumbs = (listing.images || []).map((img, i) =>
    `<img src="${Utils.escapeHtml(img.image)}" data-index="${i}" class="${i === 0 ? "active" : ""}" alt="">`
  ).join("");

  let actions = "";
  if (isActive && !isOwner) {
    if (isFixed && isBuyer) {
      actions += `<button class="btn btn-primary" id="add-cart-btn">Savatga qo'shish</button>`;
      actions += `<button class="btn btn-outline" id="buy-now-btn">Darhol buyurtma</button>`;
    }
    if (isNegotiable && isBuyer) {
      actions += `<button class="btn btn-primary" id="rfq-btn">RFQ yuborish</button>`;
    }
    if (isBuyer) {
      actions += `<button class="btn btn-ghost" id="wishlist-btn">Sevimlilarga</button>`;
    }
  }
  if (isOwner) {
    actions += `<a href="/listings/${listing.id}/edit" class="btn btn-outline" data-link>Tahrirlash</a>`;
  }
  if (listing.seller_id) {
    actions += `<a href="/sellers/${listing.seller_id}" class="btn btn-ghost" data-link>Sotuvchi profili</a>`;
  }

  const price = isNegotiable
    ? "Kelishiladi"
    : Utils.formatPrice(listing.price, listing.currency);

  return `
    <div class="detail-layout">
      <div>
        <div class="gallery-main" id="gallery-main">
          ${mainImage ? `<img src="${Utils.escapeHtml(mainImage)}" alt="" id="main-img">` : `<div class="placeholder" style="height:100%;display:flex;align-items:center;justify-content:center;font-size:4rem">📦</div>`}
        </div>
        ${thumbs ? `<div class="gallery-thumbs" id="gallery-thumbs">${thumbs}</div>` : ""}
      </div>
      <div class="detail-info">
        <span class="tag ${isNegotiable ? "tag-negotiable" : "tag-fixed"}">${Utils.listingTypeLabel(listing.listing_type)}</span>
        <span class="tag tag-active">${Utils.statusLabel(listing.status)}</span>
        <h1>${Utils.escapeHtml(listing.title)}</h1>
        <div class="detail-price">${price}</div>
        <p>${Utils.escapeHtml(listing.description)}</p>
        <ul class="listing-meta" style="list-style:none;padding:0;line-height:1.8">
          <li><strong>Sotuvchi:</strong> ${Utils.escapeHtml(listing.seller_name || "—")}</li>
          <li><strong>Manzil:</strong> ${Utils.escapeHtml(listing.region?.name_uz || "")}, ${Utils.escapeHtml(listing.district || "")}</li>
          <li><strong>Miqdor:</strong> ${listing.quantity_available} ${Utils.unitLabel(listing.unit)}</li>
          ${listing.minimum_order_quantity ? `<li><strong>Min buyurtma:</strong> ${listing.minimum_order_quantity} ${Utils.unitLabel(listing.unit)}</li>` : ""}
          <li><strong>Kategoriya:</strong> ${Utils.escapeHtml(listing.category?.name_uz || "")}</li>
          ${listing.is_perishable ? "<li><strong>Tez buziladigan mahsulot</strong></li>" : ""}
          ${listing.expires_at ? `<li><strong>Muddati:</strong> ${Utils.formatDateTime(listing.expires_at)}</li>` : ""}
        </ul>
        <div class="detail-actions">${actions}</div>
      </div>
    </div>
    <div id="order-modal" hidden></div>
    <div id="rfq-modal" hidden></div>`;
};

Pages.listingDetailMount = (app, params) => {
  app.querySelectorAll("#gallery-thumbs img").forEach((thumb) => {
    thumb.addEventListener("click", () => {
      const main = app.querySelector("#main-img");
      if (main) main.src = thumb.src;
      app.querySelectorAll("#gallery-thumbs img").forEach((t) => t.classList.remove("active"));
      thumb.classList.add("active");
    });
  });

  const listingId = params.id;

  app.querySelector("#add-cart-btn")?.addEventListener("click", async () => {
    if (!Auth.requireBuyer()) return;
    const qty = prompt("Miqdor kiriting:", "1");
    if (!qty) return;
    try {
      await Api.addToCart(listingId, qty);
      toast("Savatga qo'shildi", "success");
      Auth.updateCartBadge();
    } catch (err) {
      toast(Utils.parseApiErrors(err.data)[0], "error");
    }
  });

  app.querySelector("#wishlist-btn")?.addEventListener("click", async () => {
    if (!Auth.requireBuyer()) return;
    try {
      await Api.addToWishlist(listingId);
      toast("Sevimlilarga qo'shildi", "success");
    } catch (err) {
      toast(Utils.parseApiErrors(err.data)[0], "error");
    }
  });

  app.querySelector("#buy-now-btn")?.addEventListener("click", () => {
    if (!Auth.requireBuyer()) return;
    Pages.showOrderModal(app, listingId);
  });

  app.querySelector("#rfq-btn")?.addEventListener("click", () => {
    if (!Auth.requireBuyer()) return;
    Pages.showRFQModal(app, listingId);
  });
};

Pages.showOrderModal = async (app, listingId) => {
  const listing = await Api.getListing(listingId);
  const modal = app.querySelector("#order-modal");
  modal.hidden = false;
  modal.innerHTML = `
    <div class="form-card" style="max-width:480px;margin:2rem auto">
      <h3>Buyurtma berish — ${Utils.escapeHtml(listing.title)}</h3>
      <form id="direct-order-form" class="form-grid">
        <div class="form-field">
          <label>Miqdor</label>
          <input name="quantity" type="number" step="0.001" min="0.001" value="${listing.minimum_order_quantity || 1}" required>
        </div>
        <div class="form-field">
          <label>Yetkazish usuli</label>
          <select name="fulfillment_method" id="fulfillment-select">
            <option value="pickup">O'zi olib ketish</option>
            <option value="delivery">Yetkazib berish</option>
          </select>
        </div>
        <div class="form-field" id="address-field" hidden>
          <label>Yetkazish manzili</label>
          <textarea name="delivery_address"></textarea>
        </div>
        <div class="form-field">
          <label>Izoh</label>
          <textarea name="buyer_note"></textarea>
        </div>
        <div id="order-error"></div>
        <div class="btn-group">
          <button type="submit" class="btn btn-primary">Buyurtma berish</button>
          <button type="button" class="btn btn-ghost" id="cancel-order-modal">Bekor</button>
        </div>
      </form>
    </div>`;

  const fulfillment = modal.querySelector("#fulfillment-select");
  const addressField = modal.querySelector("#address-field");
  fulfillment.addEventListener("change", () => {
    addressField.hidden = fulfillment.value !== "delivery";
  });

  modal.querySelector("#cancel-order-modal").addEventListener("click", () => {
    modal.hidden = true;
    modal.innerHTML = "";
  });

  modal.querySelector("#direct-order-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = modal.querySelector("#order-error");
    errEl.innerHTML = "";
    const fd = new FormData(e.target);
    try {
      const order = await Api.createOrder({
        listing: listingId,
        quantity: fd.get("quantity"),
        fulfillment_method: fd.get("fulfillment_method"),
        delivery_address: fd.get("delivery_address") || "",
        buyer_note: fd.get("buyer_note") || "",
      });
      toast("Buyurtma yaratildi", "success");
      modal.hidden = true;
      Router.navigate(`/orders/${order.id}`);
    } catch (err) {
      errEl.innerHTML = Utils.renderErrors(Utils.parseApiErrors(err.data));
    }
  });
};

Pages.showRFQModal = async (app, listingId) => {
  const listing = await Api.getListing(listingId);
  const modal = app.querySelector("#rfq-modal");
  modal.hidden = false;
  modal.innerHTML = `
    <div class="form-card" style="max-width:480px;margin:2rem auto">
      <h3>RFQ yuborish — ${Utils.escapeHtml(listing.title)}</h3>
      <form id="rfq-form" class="form-grid">
        <div class="form-field">
          <label>So'ralgan miqdor</label>
          <input name="quantity_requested" type="number" step="0.001" min="0.001" required>
        </div>
        <div class="form-field">
          <label>Taklif narx (birlik)</label>
          <input name="proposed_price" type="number" step="0.01">
        </div>
        <div class="form-field">
          <label>Xabar</label>
          <textarea name="message" required></textarea>
        </div>
        <div id="rfq-error"></div>
        <div class="btn-group">
          <button type="submit" class="btn btn-primary">Yuborish</button>
          <button type="button" class="btn btn-ghost" id="cancel-rfq-modal">Bekor</button>
        </div>
      </form>
    </div>`;

  modal.querySelector("#cancel-rfq-modal").addEventListener("click", () => {
    modal.hidden = true;
    modal.innerHTML = "";
  });

  modal.querySelector("#rfq-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = modal.querySelector("#rfq-error");
    errEl.innerHTML = "";
    const fd = new FormData(e.target);
    const payload = {
      listing: listingId,
      quantity_requested: fd.get("quantity_requested"),
      message: fd.get("message"),
    };
    const price = fd.get("proposed_price");
    if (price) payload.proposed_price = price;
    try {
      const rfq = await Api.createRFQ(payload);
      toast("RFQ yuborildi", "success");
      modal.hidden = true;
      Router.navigate(`/rfq/${rfq.id}`);
    } catch (err) {
      errEl.innerHTML = Utils.renderErrors(Utils.parseApiErrors(err.data));
    }
  });
};

Pages.myListings = async (_params, searchParams) => {
  const page = Number(searchParams.get("page") || 1);
  const data = await Api.getMyListings({ page });
  const listings = data.results || data;
  const totalPages = data.count ? Math.ceil(data.count / 20) : 1;

  return `
    <div class="page-header">
      <h1>Mening e'lonlarim</h1>
      <a href="/listings/create" class="btn btn-primary" data-link>Yangi e'lon</a>
    </div>
    ${Components.listingGrid(listings)}
    ${Components.pagination(page, totalPages)}`;
};

Pages.myListingsMount = (app, _params, searchParams) => {
  Components.bindListingCards(app);
  Components.bindPagination(app, (p) => {
    Router.navigate("/my-listings", { page: p });
  });
};

Pages.listingForm = async (params, _search, isEdit = false) => {
  const { regions, categories } = await Components.loadCatalog();
  let listing = null;
  if (isEdit) listing = await Api.getListing(params.id);

  const user = Auth.getUser();
  const verified = user?.seller_profile?.is_verified;

  return `
    <div class="page-header">
      <h1>${isEdit ? "E'lonni tahrirlash" : "Yangi e'lon"}</h1>
      ${!verified ? `<p style="color:var(--color-warning)">E'lon faol qilish uchun admin tasdiqlashi kerak. Hozir "paused" holatida saqlashingiz mumkin.</p>` : ""}
    </div>
    <div class="form-card" style="max-width:640px;margin:0">
      <form id="listing-form" class="form-grid">
        <div class="form-field">
          <label>Sarlavha *</label>
          <input name="title" required value="${Utils.escapeHtml(listing?.title || "")}">
        </div>
        <div class="form-field">
          <label>Tavsif *</label>
          <textarea name="description" required>${Utils.escapeHtml(listing?.description || "")}</textarea>
        </div>
        <div class="form-grid-2">
          <div class="form-field">
            <label>Kategoriya *</label>
            <select name="category" required>${Components.categoryOptions(categories, listing?.category?.id || "", false)}</select>
          </div>
          <div class="form-field">
            <label>Viloyat *</label>
            <select name="region" required>
              <option value="">Tanlang</option>
              ${Components.regionOptions(regions, listing?.region?.id || "")}
            </select>
          </div>
        </div>
        <div class="form-field">
          <label>Tuman *</label>
          <input name="district" required value="${Utils.escapeHtml(listing?.district || "")}">
        </div>
        <div class="form-grid-2">
          <div class="form-field">
            <label>Narx turi *</label>
            <select name="listing_type" id="listing-type">
              <option value="fixed" ${listing?.listing_type === "fixed" ? "selected" : ""}>Belgilangan</option>
              <option value="negotiable" ${listing?.listing_type === "negotiable" ? "selected" : ""}>Kelishiladi</option>
            </select>
          </div>
          <div class="form-field" id="price-field">
            <label>Narx</label>
            <input name="price" type="number" step="0.01" value="${listing?.price ?? ""}">
          </div>
        </div>
        <div class="form-grid-2">
          <div class="form-field">
            <label>Miqdor *</label>
            <input name="quantity_available" type="number" step="0.001" required value="${listing?.quantity_available ?? ""}">
          </div>
          <div class="form-field">
            <label>O'lchov birligi *</label>
            <select name="unit">
              ${["kg", "litre", "piece", "box", "ton", "other"].map((u) =>
                `<option value="${u}" ${listing?.unit === u ? "selected" : ""}>${Utils.unitLabel(u)}</option>`
              ).join("")}
            </select>
          </div>
        </div>
        <div class="form-grid-2">
          <div class="form-field">
            <label>Min buyurtma miqdori</label>
            <input name="minimum_order_quantity" type="number" step="0.001" value="${listing?.minimum_order_quantity ?? ""}">
          </div>
          <div class="form-field">
            <label>Valyuta</label>
            <input name="currency" value="${Utils.escapeHtml(listing?.currency || "UZS")}">
          </div>
        </div>
        <div class="form-grid-2">
          <div class="form-field">
            <label>Holat</label>
            <select name="status">
              <option value="active" ${listing?.status === "active" ? "selected" : ""}>Faol</option>
              <option value="paused" ${listing?.status === "paused" || !listing ? "selected" : ""}>To'xtatilgan</option>
            </select>
          </div>
          <div class="form-field">
            <label>Muddati (ixtiyoriy)</label>
            <input name="expires_at" type="datetime-local" value="${listing?.expires_at ? listing.expires_at.slice(0, 16) : ""}">
          </div>
        </div>
        <div class="checkbox-field">
          <input type="checkbox" id="is_perishable" name="is_perishable" ${listing?.is_perishable ? "checked" : ""}>
          <label for="is_perishable">Tez buziladigan</label>
        </div>
        <div class="form-field">
          <label>Rasmlar ${isEdit ? "qo'shish" : "(ixtiyoriy, maks. 5 ta)"}</label>
          <input type="file" id="image-upload" accept="image/*" ${isEdit ? "" : "multiple"}>
          ${isEdit ? `
            <div id="listing-images" style="margin-top:0.5rem">
              ${(listing?.images || []).map((img) => `
                <div style="display:flex;align-items:center;gap:0.5rem;margin:0.25rem 0">
                  <img src="${Utils.escapeHtml(img.image)}" style="width:48px;height:48px;object-fit:cover;border-radius:4px">
                  <button type="button" class="btn btn-ghost btn-sm" data-delete-image="${img.id}">O'chirish</button>
                </div>`).join("")}
            </div>` : `
            <p class="listing-meta" style="margin-top:0.25rem">Tanlangan rasmlar e'lon yaratilgach yuklanadi.</p>`}
        </div>
        <div id="listing-error"></div>
        <div class="btn-group">
          <button type="submit" class="btn btn-primary">${isEdit ? "Saqlash" : "Yaratish"}</button>
          ${isEdit ? `<button type="button" class="btn btn-danger" id="delete-listing">O'chirish</button>` : ""}
        </div>
      </form>
    </div>`;
};

Pages.listingFormMount = (app, params, _search, isEdit = false) => {
  const typeSelect = app.querySelector("#listing-type");
  const priceField = app.querySelector("#price-field");
  const togglePrice = () => {
    priceField.hidden = typeSelect.value === "negotiable";
  };
  typeSelect?.addEventListener("change", togglePrice);
  togglePrice();

  app.querySelector("#listing-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = app.querySelector("#listing-error");
    errEl.innerHTML = "";
    const fd = new FormData(e.target);
    const payload = {
      title: fd.get("title"),
      description: fd.get("description"),
      category: Number(fd.get("category")),
      region: Number(fd.get("region")),
      district: fd.get("district"),
      listing_type: fd.get("listing_type"),
      quantity_available: fd.get("quantity_available"),
      unit: fd.get("unit"),
      currency: fd.get("currency") || "UZS",
      status: fd.get("status"),
      is_perishable: app.querySelector("#is_perishable").checked,
    };
    if (fd.get("price") && fd.get("listing_type") === "fixed") payload.price = fd.get("price");
    if (fd.get("minimum_order_quantity")) payload.minimum_order_quantity = fd.get("minimum_order_quantity");
    if (fd.get("expires_at")) payload.expires_at = new Date(fd.get("expires_at")).toISOString();

    try {
      if (isEdit) {
        await Api.updateListing(params.id, payload);
        toast("E'lon yangilandi", "success");
        Router.navigate(`/listings/${params.id}`);
      } else {
        const listing = await Api.createListing(payload);
        const imageInput = app.querySelector("#image-upload");
        const files = imageInput?.files ? Array.from(imageInput.files).slice(0, 5) : [];
        for (let i = 0; i < files.length; i++) {
          await Api.uploadListingImage(listing.id, files[i], i + 1);
        }
        toast(files.length ? "E'lon va rasmlar yaratildi" : "E'lon yaratildi", "success");
        Router.navigate(files.length ? `/listings/${listing.id}` : `/listings/${listing.id}/edit`);
      }
    } catch (err) {
      errEl.innerHTML = Utils.renderErrors(Utils.parseApiErrors(err.data));
    }
  });

  app.querySelector("#delete-listing")?.addEventListener("click", async () => {
    if (!confirm("E'lonni o'chirmoqchimisiz?")) return;
    try {
      await Api.deleteListing(params.id);
      toast("E'lon o'chirildi", "success");
      Router.navigate("/my-listings");
    } catch (err) {
      toast(Utils.parseApiErrors(err.data)[0], "error");
    }
  });

  if (isEdit) {
    app.querySelector("#image-upload")?.addEventListener("change", async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      try {
        await Api.uploadListingImage(params.id, file);
        toast("Rasm yuklandi", "success");
        Router.render(location.pathname);
      } catch (err) {
        toast(Utils.parseApiErrors(err.data)[0], "error");
      }
    });
  }

  app.querySelectorAll("[data-delete-image]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await Api.deleteListingImage(params.id, btn.dataset.deleteImage);
        toast("Rasm o'chirildi", "success");
        Router.render(location.pathname);
      } catch (err) {
        toast(Utils.parseApiErrors(err.data)[0], "error");
      }
    });
  });
};

Pages.createListing = (params, search) => Pages.listingForm(params, search, false);
Pages.createListingMount = (app, params, search) => Pages.listingFormMount(app, params, search, false);

Pages.editListing = (params, search) => Pages.listingForm(params, search, true);
Pages.editListingMount = (app, params, search) => Pages.listingFormMount(app, params, search, true);
