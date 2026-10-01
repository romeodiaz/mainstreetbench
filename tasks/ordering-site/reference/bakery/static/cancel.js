document.getElementById("cancel-order").addEventListener("click", async (event) => {
  const button = event.target;
  if (!window.confirm("Cancel this order?")) return;
  button.disabled = true;
  const response = await fetch(`/api/orders/${button.dataset.orderId}/cancel`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key: button.dataset.key }),
  });
  if (response.ok) {
    window.location.reload();
    return;
  }
  const data = await response.json();
  document.getElementById("cancel-error").textContent = data.error;
  button.disabled = false;
});
