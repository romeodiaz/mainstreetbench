document.getElementById('cancel-order').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!window.confirm('Cancel this order?')) return;
  const form = event.target;
  const button = form.querySelector('button');
  button.disabled = true;
  try {
    const payload = Object.fromEntries(new FormData(form));
    const response = await fetch(`/api/orders/${form.dataset.orderId}/cancel`, {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error);
    window.location.reload();
  } catch (error) {
    document.getElementById('cancel-error').textContent = error.message || 'Could not cancel. Please try again.';
    button.disabled = false;
  }
});
