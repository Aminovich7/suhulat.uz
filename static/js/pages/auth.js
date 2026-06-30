Pages.login = async (_params, searchParams) => {
  const redirect = searchParams.get("redirect") || "/";
  return `
    <div class="page-header" style="text-align:center">
      <h1>Tizimga kirish</h1>
      <p>Telefon raqam va parolingiz bilan kiring</p>
    </div>
    <div class="form-card">
      <form id="login-form" class="form-grid">
        <div class="form-field">
          <label for="phone">Telefon</label>
          <input type="tel" id="phone" name="phone" placeholder="+998901234567" required>
          <span class="hint">Format: +998XXXXXXXXX</span>
        </div>
        <div class="form-field">
          <label for="password">Parol</label>
          <input type="password" id="password" name="password" required minlength="8">
        </div>
        <div id="login-error"></div>
        <button type="submit" class="btn btn-primary btn-block">Kirish</button>
      </form>
      <p style="text-align:center;margin-top:1rem;font-size:0.875rem">
        Hisobingiz yo'qmi?
        <a href="/register/buyer" data-link>Xaridor</a> yoki
        <a href="/register/seller" data-link>Sotuvchi</a> sifatida ro'yxatdan o'ting.
      </p>
    </div>
    <input type="hidden" id="login-redirect" value="${Utils.escapeHtml(redirect)}">`;
};

Pages.loginMount = (app) => {
  app.querySelector("#login-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = app.querySelector("#login-error");
    errEl.innerHTML = "";
    const phone = app.querySelector("#phone").value.trim();
    const password = app.querySelector("#password").value;
    try {
      await Auth.login(phone, password);
      toast("Xush kelibsiz!", "success");
      const redirect = app.querySelector("#login-redirect").value || "/";
      Router.navigate(redirect);
    } catch (err) {
      errEl.innerHTML = Utils.renderErrors(Utils.parseApiErrors(err.data));
    }
  });
};

Pages.registerBuyer = async () => {
  const { regions } = await Components.loadCatalog();
  return `
    <div class="page-header" style="text-align:center">
      <h1>Xaridor sifatida ro'yxatdan o'tish</h1>
    </div>
    <div class="form-card" style="max-width:560px">
      <form id="register-buyer-form" class="form-grid">
        <div class="form-grid-2">
          <div class="form-field">
            <label>Telefon *</label>
            <input name="phone" type="tel" placeholder="+998901234567" required>
          </div>
          <div class="form-field">
            <label>To'liq ism *</label>
            <input name="full_name" required>
          </div>
        </div>
        <div class="form-field">
          <label>Email</label>
          <input name="email" type="email">
        </div>
        <div class="form-grid-2">
          <div class="form-field">
            <label>Parol *</label>
            <input name="password" type="password" minlength="8" required>
          </div>
          <div class="form-field">
            <label>Parolni tasdiqlash *</label>
            <input name="password_confirm" type="password" minlength="8" required>
          </div>
        </div>
        <div class="form-grid-2">
          <div class="form-field">
            <label>Viloyat *</label>
            <select name="region_id" required>
              <option value="">Tanlang</option>
              ${Components.regionOptions(regions)}
            </select>
          </div>
          <div class="form-field">
            <label>Tuman *</label>
            <input name="district" required>
          </div>
        </div>
        <div class="checkbox-field">
          <input type="checkbox" id="is_business" name="is_business_buyer">
          <label for="is_business">Biznes xaridor</label>
        </div>
        <div class="form-field" id="company-field" hidden>
          <label>Kompaniya nomi</label>
          <input name="company_name">
        </div>
        <div id="register-error"></div>
        <button type="submit" class="btn btn-primary btn-block">Ro'yxatdan o'tish</button>
      </form>
      <p style="text-align:center;margin-top:1rem;font-size:0.875rem">
        Sotuvchi bo'lasizmi? <a href="/register/seller" data-link>Sotuvchi ro'yxati</a>
      </p>
    </div>`;
};

Pages.registerBuyerMount = (app) => {
  const bizCheck = app.querySelector("#is_business");
  const companyField = app.querySelector("#company-field");
  bizCheck?.addEventListener("change", () => {
    companyField.hidden = !bizCheck.checked;
  });

  app.querySelector("#register-buyer-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = app.querySelector("#register-error");
    errEl.innerHTML = "";
    const fd = new FormData(e.target);
    if (fd.get("password") !== fd.get("password_confirm")) {
      errEl.innerHTML = Utils.renderErrors(["Parollar mos kelmadi"]);
      return;
    }
    const payload = {
      phone: fd.get("phone"),
      password: fd.get("password"),
      full_name: fd.get("full_name"),
      email: fd.get("email") || "",
      region_id: Number(fd.get("region_id")),
      district: fd.get("district"),
      is_business_buyer: bizCheck.checked,
      company_name: fd.get("company_name") || "",
    };
    try {
      await Api.registerBuyer(payload);
      toast("Ro'yxatdan o'tdingiz! Endi kiring.", "success");
      Router.navigate("/login");
    } catch (err) {
      errEl.innerHTML = Utils.renderErrors(Utils.parseApiErrors(err.data));
    }
  });
};

Pages.registerSeller = async () => {
  const { regions } = await Components.loadCatalog();
  return `
    <div class="page-header" style="text-align:center">
      <h1>Sotuvchi sifatida ro'yxatdan o'tish</h1>
    </div>
    <div class="form-card" style="max-width:560px">
      <form id="register-seller-form" class="form-grid">
        <div class="form-grid-2">
          <div class="form-field">
            <label>Telefon *</label>
            <input name="phone" type="tel" placeholder="+998901234567" required>
          </div>
          <div class="form-field">
            <label>To'liq ism *</label>
            <input name="full_name" required>
          </div>
        </div>
        <div class="form-field">
          <label>Email</label>
          <input name="email" type="email">
        </div>
        <div class="form-grid-2">
          <div class="form-field">
            <label>Parol *</label>
            <input name="password" type="password" minlength="8" required>
          </div>
          <div class="form-field">
            <label>Parolni tasdiqlash *</label>
            <input name="password_confirm" type="password" minlength="8" required>
          </div>
        </div>
        <div class="form-field">
          <label>Sotuvchi / biznes nomi *</label>
          <input name="seller_name" required>
        </div>
        <div class="form-field">
          <label>Sotuvchi turi *</label>
          <select name="seller_type" required>
            <option value="surplus">Ortiqcha mahsulot</option>
            <option value="maker">Ishlab chiqaruvchi</option>
            <option value="wholesale">Ulgurji</option>
          </select>
        </div>
        <div class="form-grid-2">
          <div class="form-field">
            <label>Viloyat *</label>
            <select name="region_id" required>
              <option value="">Tanlang</option>
              ${Components.regionOptions(regions)}
            </select>
          </div>
          <div class="form-field">
            <label>Tuman *</label>
            <input name="district" required>
          </div>
        </div>
        <div class="form-field">
          <label>Tavsif</label>
          <textarea name="description"></textarea>
        </div>
        <div id="register-error"></div>
        <button type="submit" class="btn btn-primary btn-block">Ro'yxatdan o'tish</button>
      </form>
    </div>`;
};

Pages.registerSellerMount = (app) => {
  app.querySelector("#register-seller-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = app.querySelector("#register-error");
    errEl.innerHTML = "";
    const fd = new FormData(e.target);
    if (fd.get("password") !== fd.get("password_confirm")) {
      errEl.innerHTML = Utils.renderErrors(["Parollar mos kelmadi"]);
      return;
    }
    const payload = {
      phone: fd.get("phone"),
      password: fd.get("password"),
      full_name: fd.get("full_name"),
      email: fd.get("email") || "",
      seller_name: fd.get("seller_name"),
      seller_type: fd.get("seller_type"),
      region_id: Number(fd.get("region_id")),
      district: fd.get("district"),
      description: fd.get("description") || "",
    };
    try {
      await Api.registerSeller(payload);
      toast("Ro'yxatdan o'tdingiz! Endi kiring.", "success");
      Router.navigate("/login");
    } catch (err) {
      errEl.innerHTML = Utils.renderErrors(Utils.parseApiErrors(err.data));
    }
  });
};

Pages.settings = async () => {
  const user = Auth.getUser() || await Auth.fetchUser();
  return `
    <div class="page-header"><h1>Sozlamalar</h1></div>
    <div class="form-card" style="max-width:560px;margin-bottom:1.5rem">
      <h3 style="margin-top:0">Profil ma'lumotlari</h3>
      <form id="account-form" class="form-grid">
        <div class="form-field">
          <label>To'liq ism</label>
          <input name="full_name" value="${Utils.escapeHtml(user?.full_name || "")}">
        </div>
        <div class="form-field">
          <label>Email</label>
          <input name="email" type="email" value="${Utils.escapeHtml(user?.email || "")}">
        </div>
        <div id="account-error"></div>
        <button type="submit" class="btn btn-primary">Saqlash</button>
      </form>
    </div>
    <div class="form-card" style="max-width:560px">
      <h3 style="margin-top:0">Parolni o'zgartirish</h3>
      <form id="password-form" class="form-grid">
        <div class="form-field">
          <label>Joriy parol</label>
          <input name="old_password" type="password" required>
        </div>
        <div class="form-field">
          <label>Yangi parol</label>
          <input name="new_password" type="password" minlength="8" required>
        </div>
        <div class="form-field">
          <label>Yangi parolni tasdiqlash</label>
          <input name="new_password_confirm" type="password" minlength="8" required>
        </div>
        <div id="password-error"></div>
        <button type="submit" class="btn btn-primary">Parolni yangilash</button>
      </form>
    </div>`;
};

Pages.settingsMount = (app) => {
  app.querySelector("#account-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = app.querySelector("#account-error");
    errEl.innerHTML = "";
    const fd = new FormData(e.target);
    try {
      await Api.updateMe({
        full_name: fd.get("full_name"),
        email: fd.get("email") || "",
      });
      await Auth.fetchUser();
      toast("Profil yangilandi", "success");
    } catch (err) {
      errEl.innerHTML = Utils.renderErrors(Utils.parseApiErrors(err.data));
    }
  });

  app.querySelector("#password-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = app.querySelector("#password-error");
    errEl.innerHTML = "";
    const fd = new FormData(e.target);
    if (fd.get("new_password") !== fd.get("new_password_confirm")) {
      errEl.innerHTML = Utils.renderErrors(["Yangi parollar mos kelmadi"]);
      return;
    }
    try {
      await Api.changePassword({
        old_password: fd.get("old_password"),
        new_password: fd.get("new_password"),
        new_password_confirm: fd.get("new_password_confirm"),
      });
      toast("Parol yangilandi", "success");
      e.target.reset();
    } catch (err) {
      errEl.innerHTML = Utils.renderErrors(Utils.parseApiErrors(err.data));
    }
  });
};
