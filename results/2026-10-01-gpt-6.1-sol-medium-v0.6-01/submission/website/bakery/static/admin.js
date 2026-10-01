document.addEventListener("click", async (event) => {
  const button = event.target.closest(".activate-gift-cards");
  if (!button || button.disabled) return;
  if (!window.confirm(`Have you received the full $${Number(button.dataset.amount).toFixed(2)} due for order #${button.dataset.orderId}? This only activates the gift cards; it does not take payment.`)) return;
  button.disabled = true;
  try {
    const response = await fetch(`/admin/api/orders/${button.dataset.orderId}/activate-gift-cards`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ payment_received: true }),
    });
    if (!response.ok) { const data = await response.json(); throw new Error(data.error || "Please retry"); }
    window.location.reload();
  } catch (error) {
    document.getElementById("staff-error").textContent = error.message;
    button.disabled = false;
  }
});
