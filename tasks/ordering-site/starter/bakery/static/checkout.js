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

renderLines();
