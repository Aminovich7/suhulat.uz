const API_BASE = "/api";

const Api = {
  async request(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    const access = Auth.getAccessToken();

    if (access && !options.skipAuth) {
      headers.Authorization = `Bearer ${access}`;
    }

    if (options.body && !(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(options.body);
    }

    let response = await fetch(`${API_BASE}${path}`, { ...options, headers });

    if (response.status === 401 && !options.skipRefresh && Auth.getRefreshToken()) {
      const refreshed = await Auth.refreshToken();
      if (refreshed) {
        headers.Authorization = `Bearer ${Auth.getAccessToken()}`;
        response = await fetch(`${API_BASE}${path}`, { ...options, headers });
      } else {
        Auth.clearSession();
        Router.navigate("/login");
        throw new Error("Sessiya tugadi. Qayta kiring.");
      }
    }

    if (response.status === 204) return null;

    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
      ? await response.json()
      : await response.text();

    if (!response.ok) {
      const err = new Error("API error");
      err.status = response.status;
      err.data = data;
      throw err;
    }

    return data;
  },

  get(path, params) {
    const qs = params ? Utils.queryString(params) : "";
    return this.request(`${path}${qs}`);
  },

  post(path, body, opts) {
    return this.request(path, { method: "POST", body, ...opts });
  },

  patch(path, body) {
    return this.request(path, { method: "PATCH", body });
  },

  put(path, body) {
    return this.request(path, { method: "PUT", body });
  },

  delete(path) {
    return this.request(path, { method: "DELETE" });
  },

  // Auth
  login(phone, password) {
    return this.post("/auth/login/", { phone, password }, { skipAuth: true, skipRefresh: true });
  },

  registerBuyer(data) {
    return this.post("/auth/register/buyer/", data, { skipAuth: true });
  },

  registerSeller(data) {
    return this.post("/auth/register/seller/", data, { skipAuth: true });
  },

  logout(refresh) {
    return this.post("/auth/logout/", { refresh });
  },

  refreshToken(refresh) {
    return this.post("/auth/token/refresh/", { refresh }, { skipAuth: true, skipRefresh: true });
  },

  me() {
    return this.get("/auth/me/");
  },

  updateMe(data) {
    return this.patch("/auth/me/", data);
  },

  changePassword(data) {
    return this.post("/auth/change-password/", data);
  },

  // Profiles
  getBuyerProfile() {
    return this.get("/profiles/buyer/me/");
  },

  updateBuyerProfile(data) {
    return this.patch("/profiles/buyer/me/", data);
  },

  getSellerProfile() {
    return this.get("/profiles/seller/me/");
  },

  updateSellerProfile(data) {
    return this.patch("/profiles/seller/me/", data);
  },

  getPublicSeller(userId) {
    return this.get(`/profiles/sellers/${userId}/`);
  },

  // Catalog
  getRegions() {
    return this.get("/regions/");
  },

  getRegion(id) {
    return this.get(`/regions/${id}/`);
  },

  getCategories() {
    return this.get("/categories/");
  },

  getCategory(id) {
    return this.get(`/categories/${id}/`);
  },

  // Listings
  getListings(params) {
    return this.get("/listings/", params);
  },

  getMyListings(params) {
    return this.get("/listings/", { ...params, mine: "true" });
  },

  getListing(id) {
    return this.get(`/listings/${id}/`);
  },

  createListing(data) {
    return this.post("/listings/", data);
  },

  updateListing(id, data) {
    return this.patch(`/listings/${id}/`, data);
  },

  deleteListing(id) {
    return this.delete(`/listings/${id}/`);
  },

  uploadListingImage(listingId, file, order = 1) {
    const form = new FormData();
    form.append("image", file);
    form.append("order", order);
    return this.request(`/listings/${listingId}/images/`, { method: "POST", body: form });
  },

  deleteListingImage(listingId, imageId) {
    return this.delete(`/listings/${listingId}/images/${imageId}/`);
  },

  // Cart
  getCart() {
    return this.get("/cart/");
  },

  addToCart(listingId, quantity) {
    return this.post("/cart/add_item/", { listing_id: listingId, quantity });
  },

  updateCartItem(itemId, quantity) {
    return this.post("/cart/update_item/", { item_id: itemId, quantity });
  },

  removeCartItem(itemId) {
    return this.post("/cart/remove_item/", { item_id: itemId });
  },

  clearCart() {
    return this.delete("/cart/clear/");
  },

  // Wishlist
  getWishlist() {
    return this.get("/wishlist/");
  },

  addToWishlist(listingId) {
    return this.post("/wishlist/add_item/", { listing_id: listingId });
  },

  removeWishlistItem(itemId) {
    return this.post("/wishlist/remove_item/", { item_id: itemId });
  },

  clearWishlist() {
    return this.delete("/wishlist/clear/");
  },

  // Orders
  getOrders() {
    return this.get("/orders/");
  },

  getOrder(id) {
    return this.get(`/orders/${id}/`);
  },

  createOrder(data) {
    return this.post("/orders/", data);
  },

  orderAction(id, action, note = "") {
    return this.post(`/orders/${id}/${action}/`, note ? { note } : {});
  },

  // RFQ
  getRFQs() {
    return this.get("/rfq/");
  },

  getRFQ(id) {
    return this.get(`/rfq/${id}/`);
  },

  createRFQ(data) {
    return this.post("/rfq/", data);
  },

  counterRFQ(id, data) {
    return this.post(`/rfq/${id}/counter/`, data);
  },

  acceptRFQ(id) {
    return this.post(`/rfq/${id}/accept/`, {});
  },

  rejectRFQ(id) {
    return this.post(`/rfq/${id}/reject/`, {});
  },

  // Reviews
  createReview(data) {
    return this.post("/reviews/", data);
  },

  getSellerReviews(sellerId) {
    return this.get(`/reviews/seller/${sellerId}/`);
  },

  // Admin
  getAdminStats() {
    return this.get("/admin/stats/");
  },

  getAdminSellers(params) {
    return this.get("/admin/sellers/", params);
  },

  approveSeller(userId) {
    return this.post(`/admin/sellers/${userId}/approve/`, {});
  },

  rejectSeller(userId, body = {}) {
    return this.post(`/admin/sellers/${userId}/reject/`, body);
  },

  getAdminListings(params) {
    return this.get("/admin/listings/", params);
  },

  moderateListing(id, status) {
    return this.post(`/admin/listings/${id}/moderate/`, { status });
  },

  getAdminReviews(params) {
    return this.get("/admin/reviews/", params);
  },

  deleteAdminReview(id) {
    return this.delete(`/admin/reviews/${id}/`);
  },
};
