document.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button || button.disabled) return;
  const action = button.dataset.action;
  const message = action === "payment-received"
    ? "Confirm you have actually received the full remaining payment for this order? This activates any gift cards purchased."
    : "Cancel this order? Gift credit is restored and unused cards purchased are voided. Any cash or card refund must be handled separately.";
  if (!window.confirm(message)) return;
  button.disabled = true;
  try {
    const response = await fetch(`/admin/api/orders/${button.dataset.orderId}/${action}`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: "{}",
    });
    if (response.ok) { window.location.reload(); return; }
    const data = await response.json();
    document.getElementById("admin-error").textContent = data.error;
  } catch (error) {
    document.getElementById("admin-error").textContent = "Connection interrupted. Reload to check the order status before trying again.";
  }
  button.disabled = false;
});
