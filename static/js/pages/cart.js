Pages.cart = async () => {
  const cart = await Api.getCart();
  const items = cart.items || [];

  if (!items.length) {
    return `
      <div class="page-header"><h1>Savat</h1></div>
      <div class="empty-state">
        <h3>Savat bo'sh</h3>
        <a href="/" class="btn btn-primary" data-link>E'lonlarni ko'rish</a>
      </div>`;
  }

  const rows = items.map((item) => {
    const l = item.listing;
    const lineTotal = item.total_price != null
      ? Utils.formatPrice(item.total_price, l.currency)
      : "—";
    return `
      <tr data-item-id="${item.id}">
        <td><a href="/listings/${l.id}" data-link>${Utils.escapeHtml(l.title)}</a></td>
        <td>${Utils.formatPrice(l.price, l.currency)}</td>
        <td>
          <input type="number" class="cart-qty" value="${item.quantity}" min="0.001" step="0.001" style="width:80px">
        </td>
        <td>${lineTotal}</td>
        <td><button class="btn btn-ghost btn-sm remove-item">O'chirish</button></td>
      </tr>`;
  }).join("");

  return `
    <div class="page-header">
      <h1>Savat</h1>
      <p>${cart.total_items} ta mahsulot · Jami: ${Utils.formatPrice(cart.total_price)}</p>
    </div>
    <div class="card">
      <table class="data-table">
        <thead>
          <tr><th>Mahsulot</th><th>Narx</th><th>Miqdor</th><th>Jami</th><th></th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    <div class="btn-group" style="margin-top:1.5rem">
      <button class="btn btn-primary" id="checkout-btn">Buyurtma berish</button>
      <button class="btn btn-outline" id="clear-cart-btn">Savatni tozalash</button>
    </div>
    <div id="checkout-panel" hidden></div>`;
};

Pages.cartMount = (app) => {
  app.querySelectorAll(".remove-item").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const row = btn.closest("tr");
      try {
        await Api.removeCartItem(row.dataset.itemId);
        toast("O'chirildi", "info");
        Router.render("/cart");
      } catch (err) {
        toast(Utils.parseApiErrors(err.data)[0], "error");
      }
    });
  });

  app.querySelectorAll(".cart-qty").forEach((input) => {
    input.addEventListener("change", async () => {
      const row = input.closest("tr");
      try {
        await Api.updateCartItem(row.dataset.itemId, input.value);
        Router.render("/cart");
      } catch (err) {
        toast(Utils.parseApiErrors(err.data)[0], "error");
      }
    });
  });

  app.querySelector("#clear-cart-btn")?.addEventListener("click", async () => {
    if (!confirm("Savatni tozalaysizmi?")) return;
    await Api.clearCart();
    toast("Savat tozalandi", "info");
    Router.render("/cart");
  });

  app.querySelector("#checkout-btn")?.addEventListener("click", () => {
    const panel = app.querySelector("#checkout-panel");
    panel.hidden = false;
    panel.innerHTML = `
      <div class="form-card" style="max-width:480px;margin-top:1.5rem">
        <h3>Buyurtma ma'lumotlari</h3>
        <form id="checkout-form" class="form-grid">
          <div class="form-field">
            <label>Yetkazish usuli</label>
            <select name="fulfillment_method" id="checkout-fulfillment">
              <option value="pickup">O'zi olib ketish</option>
              <option value="delivery">Yetkazib berish</option>
            </select>
          </div>
          <div class="form-field" id="checkout-address" hidden>
            <label>Yetkazish manzili</label>
            <textarea name="delivery_address"></textarea>
          </div>
          <div class="form-field">
            <label>Izoh</label>
            <textarea name="buyer_note"></textarea>
          </div>
          <div id="checkout-error"></div>
          <button type="submit" class="btn btn-primary">Buyurtmalarni yaratish</button>
        </form>
      </div>`;

    const fulfillment = panel.querySelector("#checkout-fulfillment");
    const address = panel.querySelector("#checkout-address");
    fulfillment.addEventListener("change", () => {
      address.hidden = fulfillment.value !== "delivery";
    });

    panel.querySelector("#checkout-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const errEl = panel.querySelector("#checkout-error");
      errEl.innerHTML = "";
      const fd = new FormData(e.target);
      const common = {
        fulfillment_method: fd.get("fulfillment_method"),
        delivery_address: fd.get("delivery_address") || "",
        buyer_note: fd.get("buyer_note") || "",
      };

      try {
        const cart = await Api.getCart();
        const orders = [];
        for (const item of cart.items) {
          if (item.listing.listing_type !== "fixed") continue;
          const order = await Api.createOrder({
            listing: item.listing.id,
            quantity: item.quantity,
            ...common,
          });
          orders.push(order);
        }
        await Api.clearCart();
        toast(`${orders.length} ta buyurtma yaratildi`, "success");
        if (orders.length === 1) {
          Router.navigate(`/orders/${orders[0].id}`);
        } else {
          Router.navigate("/orders");
        }
      } catch (err) {
        errEl.innerHTML = Utils.renderErrors(Utils.parseApiErrors(err.data));
      }
    });
  });
};
