Pages.orders = async () => {
  const data = await Api.getOrders();
  const orders = data.results || data;
  const user = Auth.getUser();

  if (!orders.length) {
    return `
      <div class="page-header"><h1>Buyurtmalar</h1></div>
      <div class="empty-state"><h3>Buyurtmalar yo'q</h3></div>`;
  }

  const rows = orders.map((o) => {
    const role = String(o.buyer) === String(user.id) ? "Xaridor" : "Sotuvchi";
    return `
      <tr>
        <td><a href="/orders/${o.id}" data-link>${Utils.escapeHtml(o.listing_title)}</a></td>
        <td>${role}</td>
        <td>${o.quantity}</td>
        <td>${Utils.formatPrice(o.total_price)}</td>
        <td><span class="tag tag-${o.status === "completed" ? "completed" : o.status === "cancelled" ? "cancelled" : "pending"}">${Utils.statusLabel(o.status)}</span></td>
        <td>${Utils.formatDate(o.created_at)}</td>
      </tr>`;
  }).join("");

  return `
    <div class="page-header"><h1>Buyurtmalar</h1></div>
    <div class="card">
      <table class="data-table">
        <thead>
          <tr><th>Mahsulot</th><th>Rol</th><th>Miqdor</th><th>Jami</th><th>Holat</th><th>Sana</th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
};

Pages.orderDetail = async (params) => {
  const order = await Api.getOrder(params.id);
  const user = Auth.getUser();
    const isBuyer = String(order.buyer) === String(user.id);
    const isSeller = String(order.seller) === String(user.id);

  let actions = "";
  if (isSeller) {
    if (order.status === "pending") actions += `<button class="btn btn-primary" data-action="confirm">Tasdiqlash</button>`;
    if (order.status === "confirmed") actions += `<button class="btn btn-primary" data-action="fulfilling">Bajarilmoqda</button>`;
    if (order.status === "fulfilling") actions += `<button class="btn btn-primary" data-action="delivered">Yetkazildi</button>`;
  }
  if (isBuyer && order.status === "delivered") {
    actions += `<button class="btn btn-primary" data-action="complete">Yakunlash</button>`;
  }
  if (["pending", "confirmed"].includes(order.status)) {
    actions += `<button class="btn btn-danger" data-action="cancel">Bekor qilish</button>`;
  }
  if (isBuyer && order.status === "completed") {
    actions += `<button class="btn btn-outline" id="review-btn">Sharh qoldirish</button>`;
  }

  return `
    <div class="page-header">
      <h1>Buyurtma #${order.id.slice(0, 8)}</h1>
      <p>${Utils.escapeHtml(order.listing_title)}</p>
    </div>
    <div class="card card-body">
      ${Components.orderStatusSteps(order.status)}
      <ul style="list-style:none;padding:0;line-height:1.9">
        <li><strong>Holat:</strong> ${Utils.statusLabel(order.status)}</li>
        <li><strong>Miqdor:</strong> ${order.quantity}</li>
        <li><strong>Birlik narxi:</strong> ${Utils.formatPrice(order.unit_price)}</li>
        <li><strong>Jami:</strong> ${Utils.formatPrice(order.total_price)}</li>
        <li><strong>Yetkazish:</strong> ${Utils.fulfillmentLabel(order.fulfillment_method)}</li>
        ${order.delivery_address ? `<li><strong>Manzil:</strong> ${Utils.escapeHtml(order.delivery_address)}</li>` : ""}
        ${order.buyer_note ? `<li><strong>Izoh:</strong> ${Utils.escapeHtml(order.buyer_note)}</li>` : ""}
        <li><strong>Yaratilgan:</strong> ${Utils.formatDateTime(order.created_at)}</li>
      </ul>
      <div class="btn-group" style="margin-top:1rem">${actions}</div>
    </div>
    <div id="review-panel" hidden></div>`;
};

Pages.orderDetailMount = (app, params) => {
  app.querySelectorAll("[data-action]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await Api.orderAction(params.id, btn.dataset.action);
        toast("Holat yangilandi", "success");
        Router.render(location.pathname);
      } catch (err) {
        toast(Utils.parseApiErrors(err.data)[0], "error");
      }
    });
  });

  app.querySelector("#review-btn")?.addEventListener("click", () => {
    const panel = app.querySelector("#review-panel");
    panel.hidden = false;
    panel.innerHTML = `
      <div class="form-card" style="max-width:480px;margin-top:1.5rem">
        <h3>Sharh qoldirish</h3>
        <form id="review-form" class="form-grid">
          <div class="form-field">
            <label>Baho (1-5)</label>
            <select name="rating" required>
              ${[5, 4, 3, 2, 1].map((n) => `<option value="${n}">${n}</option>`).join("")}
            </select>
          </div>
          <div class="form-field">
            <label>Izoh</label>
            <textarea name="comment"></textarea>
          </div>
          <div id="review-error"></div>
          <button type="submit" class="btn btn-primary">Yuborish</button>
        </form>
      </div>`;

    panel.querySelector("#review-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const errEl = panel.querySelector("#review-error");
      errEl.innerHTML = "";
      const fd = new FormData(e.target);
      try {
        await Api.createReview({
          order: params.id,
          rating: Number(fd.get("rating")),
          comment: fd.get("comment") || "",
        });
        toast("Sharh qo'shildi", "success");
        panel.hidden = true;
      } catch (err) {
        errEl.innerHTML = Utils.renderErrors(Utils.parseApiErrors(err.data));
      }
    });
  });
};
