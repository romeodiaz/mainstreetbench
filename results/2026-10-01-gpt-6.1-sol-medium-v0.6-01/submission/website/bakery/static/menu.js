// Choosing a pickup day shows what's sold out or not available that day.
const dayInput = document.getElementById("menu-day");
dayInput.value = localStorage.getItem("cornerloaf-day") || "";


async function showDay() {
  if (!dayInput.value) return;
  localStorage.setItem("cornerloaf-day", dayInput.value);
  const response = await fetch(`/api/menu?date=${encodeURIComponent(dayInput.value)}`);
  const data = await response.json();
  const note = document.getElementById("menu-day-note");
  if (!response.ok) { note.textContent = data.error; return; }
  note.textContent = "";
  for (const product of data.products) {
    const row = document.querySelector(`.item[data-sku="${product.sku}"]`);
    if (!row) continue;
    const button = row.querySelector("button.add, button.add-inline");
    const blocked = product.sold_out || !product.available;
    row.querySelector(".note").textContent = product.sold_out ? "Sold out" : (product.available ? "" : "Not available that day");
    row.toggleAttribute("data-sold-out", product.sold_out);
    if (button) button.disabled = blocked;
  }
}

dayInput.addEventListener("change", showDay);
showDay();
