const Utils = {
  escapeHtml(str) {
    if (str == null) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  },

  formatPrice(price, currency = "UZS") {
    if (price == null) return "Kelishiladi";
    const num = Number(price);
    if (Number.isNaN(num)) return String(price);
    return `${num.toLocaleString("uz-UZ")} ${currency}`;
  },

  formatDate(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleDateString("uz-UZ", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  },

  formatDateTime(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleString("uz-UZ", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  },

  listingTypeLabel(type) {
    return type === "negotiable" ? "Kelishiladi" : "Belgilangan narx";
  },

  statusLabel(status) {
    const labels = {
      active: "Faol",
      paused: "To'xtatilgan",
      sold_out: "Tugagan",
      expired: "Muddati o'tgan",
      deleted: "O'chirilgan",
      pending: "Kutilmoqda",
      confirmed: "Tasdiqlangan",
      fulfilling: "Bajarilmoqda",
      delivered: "Yetkazilgan",
      completed: "Yakunlangan",
      cancelled: "Bekor qilingan",
      open: "Ochiq",
      countered: "Javob berilgan",
      accepted: "Qabul qilingan",
      rejected: "Rad etilgan",
    };
    return labels[status] || status;
  },

  unitLabel(unit) {
    const labels = {
      kg: "kg",
      litre: "litr",
      piece: "dona",
      box: "quti",
      ton: "tonna",
      other: "boshqa",
    };
    return labels[unit] || unit;
  },

  sellerTypeLabel(type) {
    const labels = {
      surplus: "Hosil",
      maker: "Hunarmand",
      wholesale: "Optom",
    };
    return labels[type] || type;
  },

  fulfillmentLabel(method) {
    return method === "delivery" ? "Yetkazib berish" : "O'zi olib ketish";
  },

  parseApiErrors(data) {
    if (!data) return ["Noma'lum xatolik"];
    if (typeof data.detail === "string") return [data.detail];
    if (Array.isArray(data.detail)) return data.detail.map(String);
    const messages = [];
    for (const [field, errs] of Object.entries(data)) {
      const list = Array.isArray(errs) ? errs : [errs];
      list.forEach((e) => messages.push(`${field}: ${e}`));
    }
    return messages.length ? messages : ["So'rov bajarilmadi"];
  },

  renderErrors(messages) {
    const items = messages.map((m) => `<li>${Utils.escapeHtml(m)}</li>`).join("");
    return `<div class="form-error"><strong>Xatolik:</strong><ul>${items}</ul></div>`;
  },

  queryString(params) {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== "" && v != null && v !== false) qs.set(k, v);
    });
    const s = qs.toString();
    return s ? `?${s}` : "";
  },

  debounce(fn, ms = 300) {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  },

  stars(rating) {
    const r = Math.round(Number(rating) || 0);
    return "★".repeat(r) + "☆".repeat(5 - r);
  },
};

function toast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const el = document.createElement("div");
  el.className = `toast toast-${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}
