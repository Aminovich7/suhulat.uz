document.addEventListener("DOMContentLoaded", async () => {
  // Routes
  Router.register("/", Pages.home, { onMount: Pages.homeMount });
  Router.register("/login", Pages.login, { onMount: Pages.loginMount });
  Router.register("/register/buyer", Pages.registerBuyer, { onMount: Pages.registerBuyerMount });
  Router.register("/register/seller", Pages.registerSeller, { onMount: Pages.registerSellerMount });

  Router.register("/listings/create", Pages.createListing, { auth: true, seller: true, onMount: Pages.createListingMount });
  Router.register("/listings/:id/edit", Pages.editListing, { auth: true, seller: true, onMount: Pages.editListingMount });
  Router.register("/listings/:id", Pages.listingDetail, { onMount: Pages.listingDetailMount });
  Router.register("/my-listings", Pages.myListings, { auth: true, seller: true, onMount: Pages.myListingsMount });

  Router.register("/cart", Pages.cart, { auth: true, buyer: true, onMount: Pages.cartMount });
  Router.register("/wishlist", Pages.wishlist, { auth: true, buyer: true, onMount: Pages.wishlistMount });
  Router.register("/orders", Pages.orders, { auth: true, onMount: () => {} });
  Router.register("/orders/:id", Pages.orderDetail, { auth: true, onMount: Pages.orderDetailMount });

  Router.register("/rfq", Pages.rfqList, { auth: true, onMount: () => {} });
  Router.register("/rfq/:id", Pages.rfqDetail, { auth: true, onMount: Pages.rfqDetailMount });

  Router.register("/profile", Pages.profile, { auth: true, onMount: Pages.profileMount });
  Router.register("/settings", Pages.settings, { auth: true, onMount: Pages.settingsMount });
  Router.register("/admin", Pages.admin, { auth: true, staff: true, onMount: Pages.adminMount });
  Router.register("/sellers/:id", Pages.publicSeller, { onMount: Pages.publicSellerMount });

  // Header search
  document.getElementById("header-search-form")?.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = document.getElementById("header-search-input").value.trim();
    Router.navigate("/", q ? { search: q } : {});
  });

  // Mobile nav
  document.getElementById("nav-toggle")?.addEventListener("click", () => {
    const nav = document.getElementById("main-nav");
    const open = nav.classList.toggle("open");
    document.getElementById("nav-toggle").setAttribute("aria-expanded", open);
  });

  // Logout
  document.getElementById("logout-btn")?.addEventListener("click", () => Auth.logout());

  // Init auth state then router
  if (Auth.isAuthenticated()) {
    await Auth.fetchUser();
  }
  Auth.updateNav();
  Router.init();
});
