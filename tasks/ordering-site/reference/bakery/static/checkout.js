// Checkout: editable cart, pickup times for the chosen day, and a live total from the server
// (the server owns pricing, so what we show is exactly what we'll charge).

function money(value) {
  return `$${Number(value).toFixed(2)}`;
}

function setQty(sku, qty) {
  const cart = readCart()
    .map((line) => (line.sku === sku ? { ...line, qty } : line))
    .filter((line) => line.qty > 0);
  writeCart(cart);
  renderLines();
  refreshQuote();
}

function renderLines() {
  const cart = readCart();
  const table = document.getElementById("cart-lines");
  if (!cart.length) {
    table.innerHTML = "<tr><td>Your cart is empty. <a href='/'>Back to the menu</a></td></tr>";
    return;
  }
  table.innerHTML = cart.map((line) => `
    <tr data-sku="${line.sku}">
      <td>${line.name}</td>
      <td><label>Quantity of ${line.name}
        <input type="number" class="qty" min="0" max="50" value="${line.qty}" data-sku="${line.sku}"></label></td>
      <td>${money(line.qty * line.price)}</td>
      <td><button type="button" class="remove" data-sku="${line.sku}">Remove ${line.name}</button></td>
    </tr>`).join("");
}

document.getElementById("cart-lines").addEventListener("change", (event) => {
  if (event.target.classList.contains("qty")) {
    const qty = Math.max(0, Math.min(50, parseInt(event.target.value, 10) || 0));
    setQty(event.target.dataset.sku, qty);
  }
});

document.getElementById("cart-lines").addEventListener("click", (event) => {
  const button = event.target.closest("button.remove");
  if (button) setQty(button.dataset.sku, 0);
});

let quoteRequest = 0;
async function refreshQuote() {
  const box = document.getElementById("quote");
  const form = new FormData(document.getElementById("checkout"));
  const items = readCart().map((l) => ({ sku: l.sku, qty: l.qty }));
  if (!items.length) {
    box.innerHTML = "";
    return;
  }
  const request = ++quoteRequest;
  const response = await fetch("/api/quote", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items, promo_code: form.get("promo_code"), gift_card_code: form.get("gift_card_code") }),
  });
  const data = await response.json();
  if (request !== quoteRequest) return;
  if (!response.ok) {
    box.innerHTML = `<p class="error">${data.error}</p>`;
    return;
  }
  const rows = [["Subtotal", money(data.subtotal)], ["Coupon", `−${money(data.discount)}`],
    ["Sales tax", money(data.tax)], ["Total", money(data.total)]];
  if (data.gift_card_applied) {
    rows.push(["Gift card", `−${money(data.gift_card_applied)}`],
      ["Left on gift card", money(data.gift_card_balance_after)]);
  }
  rows.push(["Pay at pickup", money(data.amount_due)]);
  box.innerHTML = `<table class="lines">${rows.map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join("")}</table>` +
    (data.notes || []).map((n) => `<p class="error">${n}</p>`).join("");
}

for (const name of ["promo_code", "gift_card_code"]) {
  document.querySelector(`[name=${name}]`).addEventListener("input", () => refreshQuote());
}

document.getElementById("checkout").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const payload = {
    customer: { name: form.get("name"), email: form.get("email"), phone: form.get("phone") },
    pickup_date: form.get("pickup_date"),
    pickup_slot: form.get("pickup_slot"),
    promo_code: form.get("promo_code"),
    gift_card_code: form.get("gift_card_code"),
    items: readCart().map((l) => ({ sku: l.sku, qty: l.qty })),
  };
  const response = await fetch("/api/orders", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    document.getElementById("checkout-error").textContent = data.error;
    return;
  }
  writeCart([]);
  window.location = data.confirmation_url;
});

async function loadSlots() {
  const date = document.querySelector("[name=pickup_date]").value;
  const select = document.querySelector("[name=pickup_slot]");
  if (!date) return;
  const response = await fetch(`/api/slots?date=${encodeURIComponent(date)}`);
  const data = await response.json();
  if (!response.ok || !data.open) {
    select.innerHTML = `<option value="">${response.ok ? "We're closed that day" : data.error}</option>`;
    return;
  }
  const open = data.slots.filter((s) => s.available);
  select.innerHTML = open.length
    ? open.map((s) => `<option value="${s.time}">${s.time} (${s.remaining} left)</option>`).join("")
    : "<option value=''>No times left that day</option>";
}

document.querySelector("[name=pickup_date]").addEventListener("change", loadSlots);
renderLines();
refreshQuote();
