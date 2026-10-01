function renderLines() {
  const cart = readCart();
  const table = document.getElementById("cart-lines");
  table.replaceChildren();
  if (!cart.length) {
    const row = table.insertRow();
    row.insertCell().textContent = 'Your cart is empty. Return to the menu to add items.';
  }
  for (const line of cart) {
    const row = table.insertRow();
    row.insertCell().textContent = `${line.qty} × ${line.name}`;
    row.insertCell().textContent = `$${(line.qty * line.price).toFixed(2)}`;
  }
}

document.getElementById("checkout").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const payload = {
    customer: { name: form.get("name"), email: form.get("email"), phone: form.get("phone") },
    pickup_date: form.get("pickup_date"),
    pickup_time: form.get("pickup_time"),
    gift_card_code: form.get("gift_card_code"),
    promo_code: form.get("promo_code"),
    items: readCart().map((l) => ({ sku: l.sku, qty: l.qty })),
  };
  const button = event.target.querySelector("button[type=submit]");
  button.disabled = true;
  try {
  const response = await fetch("/api/orders", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    document.getElementById("checkout-error").textContent = data.error;
    return;
  }
  writeCart([]);
  window.location = data.order_url;
  } catch {
    document.getElementById("checkout-error").textContent = "Could not contact the bakery. Please check your connection.";
  } finally { button.disabled = false; }
});

renderLines();

let availabilityRequest = 0;
document.querySelector('[name=pickup_date]').addEventListener('change', async (event) => {
  const request = ++availabilityRequest;
  const select = document.querySelector('[name=pickup_time]');
  const note = document.getElementById('availability');
  select.replaceChildren(new Option('Loading times…', ''));
  note.textContent = '';
  try {
    const skus = readCart().map(l => l.sku).join(',');
    const response = await fetch(`/api/pickup-times?date=${encodeURIComponent(event.target.value)}&skus=${encodeURIComponent(skus)}`);
    const data = await response.json();
    if (request !== availabilityRequest) return;
    if (!response.ok) throw new Error(data.error);
    select.replaceChildren(new Option('Choose a pickup time', ''));
    for (const slot of data.times) {
      const option = new Option(`${slot.time}${slot.remaining ? '' : ' — full'}`, slot.time);
      option.disabled = !slot.remaining;
      select.add(option);
    }
    const messages = readCart().filter(l => data.remaining[l.sku] !== undefined)
      .map(l => `${l.name}: ${data.remaining[l.sku]} left for this date${l.qty > data.remaining[l.sku] ? ' — sold out for your quantity' : ''}`);
    if (!data.times.some(t => t.remaining)) messages.unshift('No pickup times available. Choose another date.');
    note.textContent = messages.join('. ');
  } catch (error) {
    if (request !== availabilityRequest) return;
    select.replaceChildren(new Option('Choose another date', ''));
    note.textContent = error.message || 'Could not load pickup times.';
  }
});
