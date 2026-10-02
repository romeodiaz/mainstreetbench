// Checkout: editable cart, pickup times for the chosen day, a live total from the server
// (the server owns pricing, so what we show is what we charge), and one order per click.

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = String(text ?? "");
  return div.innerHTML;
}

function money(value) {
  return `$${Number(value).toFixed(2)}`;
}

function setQty(sku, qty) {
  writeCart(readCart().map((line) => (line.sku === sku ? { ...line, qty } : line)).filter((line) => line.qty > 0));
  renderLines();
  refreshQuote();
}

function removeLine(sku) {
  writeCart(readCart().filter((line) => line.sku !== sku));
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
  table.innerHTML = "";
  for (const line of cart) {
    const row = table.insertRow();
    row.dataset.sku = line.sku;
    row.insertCell().textContent = line.name;
    const qtyCell = row.insertCell();
    const label = document.createElement("label");
    label.textContent = "Quantity ";
    const input = document.createElement("input");
    Object.assign(input, { type: "number", min: 1, max: 50, value: line.qty, className: "qty" });
    input.addEventListener("change", () => {
      const qty = parseInt(input.value, 10);
      if (Number.isInteger(qty) && qty >= 1 && qty <= 50) setQty(line.sku, qty);
      else input.value = line.qty;
    });
    label.append(input);
    qtyCell.append(label);
    row.insertCell().textContent = money(line.qty * line.price);
    const remove = document.createElement("button");
    Object.assign(remove, { type: "button", className: "remove", textContent: `Remove ${line.name}` });
    remove.addEventListener("click", () => removeLine(line.sku));
    row.insertCell().append(remove);
  }
}

let quoteRequest = 0;
async function refreshQuote() {
  const box = document.getElementById("quote");
  const form = new FormData(document.getElementById("checkout"));
  const items = readCart().map((l) => ({ sku: l.sku, qty: l.qty }));
  if (!items.length) { box.innerHTML = ""; return; }
  const request = ++quoteRequest;
  const response = await fetch("/api/quote", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items, promo_code: form.get("promo_code"), gift_card_code: form.get("gift_card_code"),
                           email: form.get("email"), pickup_date: form.get("pickup_date") }),
  });
  const data = await response.json();
  if (request !== quoteRequest) return;
  if (!response.ok) { box.innerHTML = `<p class="error">${escapeHtml(data.error)}</p>`; return; }
  const rows = [["Subtotal", money(data.subtotal)], ["Coupon", `−${money(data.discount)}`],
    ["Sales tax", money(data.tax)], ["Total", money(data.total)]];
  if (data.gift_card_applied) {
    rows.push(["Gift card", `−${money(data.gift_card_applied)}`], ["Left on gift card", money(data.gift_card_balance_after)]);
  }
  rows.push(["Pay at pickup", money(data.amount_due)]);
  box.innerHTML = `<table class="lines">${rows.map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join("")}</table>` +
    data.notes.map((n) => `<p class="error">${escapeHtml(n)}</p>`).join("");
}

for (const name of ["promo_code", "gift_card_code", "email"]) {
  document.querySelector(`[name=${name}]`).addEventListener("input", refreshQuote);
}

async function loadSlots() {
  const date = document.querySelector("[name=pickup_date]").value;
  const select = document.querySelector("[name=pickup_slot]");
  if (!date) return;
  const response = await fetch(`/api/slots?date=${encodeURIComponent(date)}`);
  const data = await response.json();
  if (!response.ok || !data.open) {
    select.innerHTML = `<option value="">${response.ok ? "We're closed that day" : escapeHtml(data.error)}</option>`;
    return;
  }
  const open = data.slots.filter((s) => s.available);
  select.innerHTML = open.length
    ? open.map((s) => `<option value="${s.time}">${s.time} (${s.remaining} left)</option>`).join("")
    : "<option value=''>No times left that day</option>";
}

const dateInput = document.querySelector("[name=pickup_date]");
dateInput.value = localStorage.getItem("cornerloaf-day") || "";
dateInput.addEventListener("change", () => { loadSlots(); refreshQuote(); });

let placing = false;
const requestId = crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random();
document.getElementById("checkout").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (placing) return;  // one order per click: ignore double clicks while the first is being placed
  placing = true;
  const button = document.getElementById("place-order");
  button.disabled = true;
  const form = new FormData(event.target);
  const payload = {
    customer: { name: form.get("name"), email: form.get("email"), phone: form.get("phone") },
    pickup_date: form.get("pickup_date"), pickup_slot: form.get("pickup_slot"),
    promo_code: form.get("promo_code"), gift_card_code: form.get("gift_card_code"),
    newsletter: form.get("newsletter") === "on",
    items: readCart().map((l) => ({ sku: l.sku, qty: l.qty })),
    request_id: requestId,  // the server ignores a repeat of the same order
  };
  let response, data;
  try {
    response = await fetch("/api/orders", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    });
    data = await response.json();
  } catch {
    response = { ok: false };
    data = { error: "We couldn't reach the bakery. Please try again." };
  }
  if (!response.ok) {
    document.getElementById("checkout-error").textContent = data.error;
    placing = false;
    button.disabled = false;
    return;
  }
  writeCart([]);
  window.location = data.confirmation_url;
});

renderLines();
loadSlots();
refreshQuote();
