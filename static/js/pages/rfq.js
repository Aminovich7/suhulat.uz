Pages.rfqList = async () => {
  const data = await Api.getRFQs();
  const rfqs = data.results || data;

  if (!rfqs.length) {
    return `
      <div class="page-header"><h1>RFQ (Narx bo'yicha kelishuv)</h1></div>
      <div class="empty-state"><h3>RFQ lar yo'q</h3><p>Kelishiladigan e'lonlardan RFQ yuboring.</p></div>`;
  }

  const rows = rfqs.map((r) => `
    <tr>
      <td><a href="/rfq/${r.id}" data-link>${Utils.escapeHtml(r.listing_title)}</a></td>
      <td>${r.quantity_requested}</td>
      <td>${r.proposed_price ? Utils.formatPrice(r.proposed_price) : "—"}</td>
      <td><span class="tag tag-${r.status === "accepted" ? "completed" : r.status === "rejected" ? "cancelled" : "pending"}">${Utils.statusLabel(r.status)}</span></td>
      <td>${Utils.formatDate(r.created_at)}</td>
    </tr>`).join("");

  return `
    <div class="page-header"><h1>RFQ ro'yxati</h1></div>
    <div class="card">
      <table class="data-table">
        <thead>
          <tr><th>E'lon</th><th>Miqdor</th><th>Taklif narx</th><th>Holat</th><th>Sana</th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
};

Pages.rfqDetail = async (params) => {
  const rfq = await Api.getRFQ(params.id);
  const user = Auth.getUser();
  const isBuyer = String(rfq.buyer) === String(user.id);
  const isSeller = String(rfq.seller_id) === String(user.id);
  const canAct = ["open", "countered"].includes(rfq.status);

  const offers = (rfq.offers || []).map((o) => `
    <li class="offer-item">
      <strong>${o.proposed_by === "buyer" ? "Xaridor" : "Sotuvchi"}</strong>
      · ${Utils.formatPrice(o.price)} × ${o.quantity}
      · <span class="tag tag-${o.status === "pending" ? "pending" : "completed"}">${Utils.statusLabel(o.status)}</span>
      ${o.message ? `<p>${Utils.escapeHtml(o.message)}</p>` : ""}
      <span class="listing-meta">${Utils.formatDateTime(o.created_at)}</span>
    </li>`).join("");

  let actions = "";
  if (canAct) {
    actions += `<button class="btn btn-primary" id="counter-btn">Javob berish</button>`;
    actions += `<button class="btn btn-outline" id="accept-btn">Qabul qilish</button>`;
    actions += `<button class="btn btn-danger" id="reject-btn">Rad etish</button>`;
  }

  return `
    <div class="page-header">
      <h1>RFQ — ${Utils.escapeHtml(rfq.listing_title)}</h1>
      <p>Holat: ${Utils.statusLabel(rfq.status)}</p>
    </div>
    <div class="card card-body">
      <ul style="list-style:none;padding:0;line-height:1.9">
        <li><strong>So'ralgan miqdor:</strong> ${rfq.quantity_requested}</li>
        <li><strong>Boshlang'ich taklif:</strong> ${rfq.proposed_price ? Utils.formatPrice(rfq.proposed_price) : "—"}</li>
        <li><strong>Xabar:</strong> ${Utils.escapeHtml(rfq.message)}</li>
        <li><strong>Rol:</strong> ${isBuyer ? "Xaridor" : isSeller ? "Sotuvchi" : "—"}</li>
      </ul>
      <h3>Takliflar zanjiri</h3>
      <ul class="offer-list">${offers || "<li>Takliflar yo'q</li>"}</ul>
      ${canAct && (isBuyer || isSeller) ? `<div class="btn-group">${actions}</div>` : ""}
    </div>
    <div id="counter-panel" hidden></div>`;
};

Pages.rfqDetailMount = (app, params) => {
  app.querySelector("#accept-btn")?.addEventListener("click", async () => {
    try {
      const order = await Api.acceptRFQ(params.id);
      toast("RFQ qabul qilindi, buyurtma yaratildi", "success");
      Router.navigate(`/orders/${order.id}`);
    } catch (err) {
      toast(Utils.parseApiErrors(err.data)[0], "error");
    }
  });

  app.querySelector("#reject-btn")?.addEventListener("click", async () => {
    if (!confirm("RFQ ni rad etasizmi?")) return;
    try {
      await Api.rejectRFQ(params.id);
      toast("RFQ rad etildi", "info");
      Router.render(location.pathname);
    } catch (err) {
      toast(Utils.parseApiErrors(err.data)[0], "error");
    }
  });

  app.querySelector("#counter-btn")?.addEventListener("click", () => {
    const panel = app.querySelector("#counter-panel");
    panel.hidden = false;
    panel.innerHTML = `
      <div class="form-card" style="max-width:480px;margin-top:1.5rem">
        <h3>Qarshi taklif</h3>
        <form id="counter-form" class="form-grid">
          <div class="form-field">
            <label>Narx (birlik)</label>
            <input name="price" type="number" step="0.01" required>
          </div>
          <div class="form-field">
            <label>Miqdor</label>
            <input name="quantity" type="number" step="0.001" required>
          </div>
          <div class="form-field">
            <label>Xabar</label>
            <textarea name="message"></textarea>
          </div>
          <div id="counter-error"></div>
          <button type="submit" class="btn btn-primary">Yuborish</button>
        </form>
      </div>`;

    panel.querySelector("#counter-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const errEl = panel.querySelector("#counter-error");
      errEl.innerHTML = "";
      const fd = new FormData(e.target);
      try {
        await Api.counterRFQ(params.id, {
          price: fd.get("price"),
          quantity: fd.get("quantity"),
          message: fd.get("message") || "",
        });
        toast("Taklif yuborildi", "success");
        Router.render(location.pathname);
      } catch (err) {
        errEl.innerHTML = Utils.renderErrors(Utils.parseApiErrors(err.data));
      }
    });
  });
};
