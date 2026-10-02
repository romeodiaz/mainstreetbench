// Checkout: editable cart, pickup times for the chosen day, a live total from the server
// (the server owns pricing, so what we show is what we charge), and one order per click.

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
    const hint = document.createElement("span");
    hint.className = "visually-hidden";
    hint.textContent = `Quantity of ${line.name}`;
    label.append(hint);
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
  if (!response.ok) {
    box.innerHTML = "<p class='error'></p>";
    box.firstChild.textContent = data.error;
    return;
  }
  const rows = [["Subtotal", money(data.subtotal)], ["Coupon", `−${money(data.discount)}`],
    ["Sales tax", money(data.tax)], ["Total", money(data.total)]];
  if (data.gift_card_applied) {
    rows.push(["Gift card", `−${money(data.gift_card_applied)}`], ["Left on gift card", money(data.gift_card_balance_after)]);
  }
  rows.push(["Pay at pickup", money(data.amount_due)]);
  box.innerHTML = `<table class="lines">${rows.map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join("")}</table>`;
  for (const note of data.notes) {
    const p = document.createElement("p");
    p.className = "error";
    p.textContent = note;
    box.append(p);
  }
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
    select.innerHTML = "<option value=''></option>";
    select.firstChild.textContent = response.ok ? "We're closed that day" : data.error;
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
  if (placing) return;                 // a second click or tap while the first order is still going through
  placing = true;
  const button = document.getElementById("place-order");
  const error = document.getElementById("checkout-error");
  button.disabled = true;
  error.textContent = "";
  const form = new FormData(event.target);
  const payload = {
    customer: { name: form.get("name"), email: form.get("email"), phone: form.get("phone") },
    pickup_date: form.get("pickup_date"), pickup_slot: form.get("pickup_slot"),
    promo_code: form.get("promo_code"), gift_card_code: form.get("gift_card_code"),
    newsletter: form.get("newsletter") === "on",
    items: readCart().map((l) => ({ sku: l.sku, qty: l.qty })),
    request_id: requestId,             // the server places one order per request_id, even if this is sent twice
  };
  let response, data;
  try {
    response = await fetch("/api/orders", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    });
    data = await response.json();
  } catch {
    error.textContent = "We couldn't reach the bakery. Please check your connection and try again.";
    placing = false;
    button.disabled = false;
    return;
  }
  if (!response.ok) {
    error.textContent = data.error || "Something went wrong. Please try again or call us.";
    placing = false;
    button.disabled = false;
    return;
  }
  writeCart([]);
  window.location = data.confirmation_url;
});

// Prices in a saved cart can be out of date; show today's prices (the server charges these either way).
async function refreshPrices() {
  try {
    const data = await (await fetch("/api/menu")).json();
    const prices = new Map(data.products.map((p) => [p.sku, p.price]));
    writeCart(readCart().map((line) => (prices.has(line.sku) ? { ...line, price: prices.get(line.sku) } : line)));
    renderLines();
  } catch {}
}

renderLines();
loadSlots();
refreshQuote();
refreshPrices();
