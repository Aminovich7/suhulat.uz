Pages.wishlist = async () => {
  const wishlist = await Api.getWishlist();
  const items = wishlist.items || [];

  if (!items.length) {
    return `
      <div class="page-header"><h1>Sevimlilar</h1></div>
      <div class="empty-state">
        <h3>Sevimlilar ro'yxati bo'sh</h3>
        <a href="/" class="btn btn-primary" data-link>E'lonlarni ko'rish</a>
      </div>`;
  }

  const listings = items.map((item) => item.listing).filter(Boolean);

  return `
    <div class="page-header">
      <h1>Sevimlilar</h1>
      <button class="btn btn-outline btn-sm" id="clear-wishlist">Tozalash</button>
    </div>
    ${Components.listingGrid(listings)}
    <div style="margin-top:1rem">
      ${items.map((item) => `
        <button class="btn btn-ghost btn-sm" data-remove="${item.id}" style="margin:0.25rem">
          ${Utils.escapeHtml(item.listing?.title || "—")} — o'chirish
        </button>`).join("")}
    </div>`;
};

Pages.wishlistMount = (app) => {
  Components.bindListingCards(app);

  app.querySelector("#clear-wishlist")?.addEventListener("click", async () => {
    if (!confirm("Sevimlilarni tozalaysizmi?")) return;
    await Api.clearWishlist();
    toast("Tozalandi", "info");
    Router.render("/wishlist");
  });

  app.querySelectorAll("[data-remove]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await Api.removeWishlistItem(btn.dataset.remove);
      Router.render("/wishlist");
    });
  });
};
