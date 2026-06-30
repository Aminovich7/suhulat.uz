const Auth = {
  ACCESS_KEY: "suhulat_access",
  REFRESH_KEY: "suhulat_refresh",
  USER_KEY: "suhulat_user",

  getAccessToken() {
    return localStorage.getItem(this.ACCESS_KEY);
  },

  getRefreshToken() {
    return localStorage.getItem(this.REFRESH_KEY);
  },

  getUser() {
    try {
      const raw = localStorage.getItem(this.USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  isAuthenticated() {
    return !!this.getAccessToken();
  },

  isBuyer() {
    const user = this.getUser();
    return user && (user.role === "buyer" || user.role === "both");
  },

  isSeller() {
    const user = this.getUser();
    return user && (user.role === "seller" || user.role === "both");
  },

  isStaff() {
    const user = this.getUser();
    return user && user.is_staff;
  },

  setSession(access, refresh, user) {
    localStorage.setItem(this.ACCESS_KEY, access);
    localStorage.setItem(this.REFRESH_KEY, refresh);
    if (user) localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    this.updateNav();
  },

  clearSession() {
    localStorage.removeItem(this.ACCESS_KEY);
    localStorage.removeItem(this.REFRESH_KEY);
    localStorage.removeItem(this.USER_KEY);
    this.updateNav();
  },

  async login(phone, password) {
    const data = await Api.login(phone, password);
    this.setSession(data.access, data.refresh, null);
    await this.fetchUser();
    return this.getUser();
  },

  async fetchUser() {
    if (!this.isAuthenticated()) return null;
    try {
      const user = await Api.me();
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
      this.updateNav();
      return user;
    } catch {
      this.clearSession();
      return null;
    }
  },

  async refreshToken() {
    const refresh = this.getRefreshToken();
    if (!refresh) return false;
    try {
      const data = await Api.refreshToken(refresh);
      localStorage.setItem(this.ACCESS_KEY, data.access);
      if (data.refresh) localStorage.setItem(this.REFRESH_KEY, data.refresh);
      return true;
    } catch {
      return false;
    }
  },

  async logout() {
    const refresh = this.getRefreshToken();
    try {
      if (refresh) await Api.logout(refresh);
    } catch {
      /* ignore */
    }
    this.clearSession();
    Router.navigate("/");
    toast("Tizimdan chiqdingiz", "info");
  },

  requireAuth() {
    if (!this.isAuthenticated()) {
      Router.navigate("/login", { redirect: location.pathname });
      return false;
    }
    return true;
  },

  requireBuyer() {
    if (!this.requireAuth()) return false;
    if (!this.isBuyer()) {
      toast("Bu sahifa faqat xaridorlar uchun", "error");
      Router.navigate("/");
      return false;
    }
    return true;
  },

  requireSeller() {
    if (!this.requireAuth()) return false;
    if (!this.isSeller()) {
      toast("Bu sahifa faqat sotuvchilar uchun", "error");
      Router.navigate("/");
      return false;
    }
    return true;
  },

  requireStaff() {
    if (!this.requireAuth()) return false;
    if (!this.isStaff()) {
      toast("Faqat adminlar uchun", "error");
      Router.navigate("/");
      return false;
    }
    return true;
  },

  updateNav() {
    const authed = this.isAuthenticated();
    const user = this.getUser();
    const isBuyer = this.isBuyer();
    const isSeller = this.isSeller();
    const isStaff = this.isStaff();

    document.querySelectorAll("[data-auth]").forEach((el) => {
      const role = el.dataset.auth;
      let show = authed;
      if (role === "buyer") show = authed && isBuyer;
      if (role === "seller") show = authed && isSeller;
      if (role === "staff") show = authed && isStaff;
      el.hidden = !show;
      el.style.display = show ? "" : "none";
    });

    document.querySelectorAll("[data-guest]").forEach((el) => {
      el.hidden = authed;
      el.style.display = authed ? "none" : "";
    });

    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
      logoutBtn.hidden = !authed;
      logoutBtn.style.display = authed ? "" : "none";
    }

    if (authed && user) {
      const profileLink = document.querySelector('a[href="/profile"]');
      if (profileLink) profileLink.textContent = user.full_name || "Profil";
    }
  },

  async updateCartBadge() {
    const badge = document.getElementById("cart-badge");
    if (!badge || !this.isBuyer()) {
      if (badge) badge.hidden = true;
      return;
    }
    try {
      const cart = await Api.getCart();
      const count = cart.items?.length || 0;
      badge.textContent = count;
      badge.hidden = count === 0;
    } catch {
      badge.hidden = true;
    }
  },
};
