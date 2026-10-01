function renderLines() {
  const cart = readCart();
  const table = document.getElementById("cart-lines");
  table.innerHTML = cart.length
    ? cart.map((l) => `<tr><td>${l.qty} × ${l.name}</td><td>$${(l.qty * l.price).toFixed(2)}</td></tr>`).join("")
    : "<tr><td>Your cart is empty. <a href='/'>Back to the menu</a></td></tr>";
}

document.getElementById("checkout").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const payload = {
    customer: { name: form.get("name"), email: form.get("email"), phone: form.get("phone") },
    pickup_date: form.get("pickup_date"),
    pickup_slot: form.get("pickup_slot"),
    promo_code: form.get("promo_code"),
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
  window.location = `/order/${data.id}`;
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
