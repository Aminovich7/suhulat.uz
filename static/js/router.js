const Router = {
  routes: [],
  currentParams: {},

  register(path, handler, options = {}) {
    this.routes.push({ path, handler, ...options });
  },

  match(pathname) {
    for (const route of this.routes) {
      const paramNames = [];
      const pattern = route.path.replace(/:([^/]+)/g, (_, name) => {
        paramNames.push(name);
        return "([^/]+)";
      });
      const regex = new RegExp(`^${pattern}$`);
      const match = pathname.match(regex);
      if (match) {
        const params = {};
        paramNames.forEach((name, i) => {
          params[name] = decodeURIComponent(match[i + 1]);
        });
        return { route, params };
      }
    }
    return null;
  },

  async navigate(path, query = {}) {
    const url = new URL(path, window.location.origin);
    Object.entries(query).forEach(([k, v]) => {
      if (v != null) url.searchParams.set(k, v);
    });
    history.pushState({}, "", url.pathname + url.search);
    await this.render(url.pathname + url.search);
  },

  async render(fullPath) {
    const [pathname, search = ""] = fullPath.split("?");
    const matched = this.match(pathname);

    document.querySelectorAll(".main-nav a[data-link]").forEach((a) => {
      a.classList.toggle("active", a.getAttribute("href") === pathname);
    });

    const app = document.getElementById("app");
    app.innerHTML = `<div class="container">${Components.loading()}</div>`;

    if (!matched) {
      app.innerHTML = `<div class="container"><div class="empty-state"><h3>Sahifa topilmadi</h3><a href="/" data-link>Bosh sahifaga</a></div></div>`;
      return;
    }

    const { route, params } = matched;
    this.currentParams = params;

    if (route.auth && !Auth.isAuthenticated()) {
      await this.navigate("/login", { redirect: pathname });
      return;
    }
    if (route.buyer && !Auth.isBuyer()) {
      toast("Bu sahifa faqat xaridorlar uchun", "error");
      await this.navigate("/");
      return;
    }
    if (route.seller && !Auth.isSeller()) {
      toast("Bu sahifa faqat sotuvchilar uchun", "error");
      await this.navigate("/");
      return;
    }
    if (route.staff && !Auth.isStaff()) {
      toast("Faqat adminlar uchun", "error");
      await this.navigate("/");
      return;
    }

    try {
      const html = await route.handler(params, new URLSearchParams(search));
      app.innerHTML = `<div class="container">${html}</div>`;
      if (route.onMount) await route.onMount(app, params, new URLSearchParams(search));
      document.getElementById("main-nav")?.classList.remove("open");
    } catch (err) {
      console.error(err);
      const msgs = err.data ? Utils.parseApiErrors(err.data) : [err.message || "Xatolik yuz berdi"];
      app.innerHTML = `<div class="container">${Utils.renderErrors(msgs)}<a href="/" class="btn btn-outline" data-link>Bosh sahifa</a></div>`;
    }

    if (Auth.isAuthenticated()) Auth.updateCartBadge();
  },

  init() {
    document.addEventListener("click", (e) => {
      const link = e.target.closest("[data-link]");
      if (link && link.href && link.origin === window.location.origin) {
        e.preventDefault();
        this.navigate(link.pathname + link.search);
      }
    });

    window.addEventListener("popstate", () => {
      this.render(location.pathname + location.search);
    });

    this.render(location.pathname + location.search);
  },
};
