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
    await loadSlots();
    return;
  }
  writeCart([]);
  window.location = `/order/${data.id}`;
});

renderLines();

const dateInput = document.querySelector('[name="pickup_date"]');
const slotInput = document.querySelector('[name="pickup_slot"]');
let slotRequest = 0;
async function loadSlots() {
  const request = ++slotRequest;
  const selected = slotInput.value;
  slotInput.disabled = true;
  slotInput.replaceChildren(new Option("Loading pickup times…", ""));
  if (!dateInput.value) {
    slotInput.replaceChildren(new Option("Choose a date first", ""));
    return;
  }
  try {
    const response = await fetch(`/api/slots?date=${encodeURIComponent(dateInput.value)}`);
    const data = await response.json();
    if (request !== slotRequest) return;
    if (!response.ok) throw new Error(data.error);
    slotInput.replaceChildren(new Option(data.open ? "Choose a pickup time" : "Closed Mondays", ""));
    for (const slot of data.slots) {
      const option = new Option(`${slot.time} (${slot.remaining} places left)`, slot.time);
      option.disabled = !slot.available;
      slotInput.add(option);
      if (slot.available && slot.time === selected) slotInput.value = selected;
    }
    slotInput.disabled = !data.slots.some((slot) => slot.available);
    if (data.open && slotInput.disabled) slotInput.options[0].text = "No pickup times available";
  } catch (error) {
    if (request !== slotRequest) return;
    slotInput.replaceChildren(new Option("Could not load pickup times", ""));
    document.getElementById("checkout-error").textContent = error.message;
  }
}
dateInput.addEventListener("change", loadSlots);
const menuDate = new URLSearchParams(location.search).get("date");
if (menuDate) dateInput.value = menuDate;
if (dateInput.value) loadSlots();
