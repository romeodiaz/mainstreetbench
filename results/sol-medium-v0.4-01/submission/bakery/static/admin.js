document.addEventListener('click', async (event) => {
  const button = event.target.closest('.activate-cards');
  if (!button) return;
  if (!window.confirm('Confirm payment has been collected for this order before activating its gift cards.')) return;
  button.disabled = true;
  try {
    const response = await fetch(`/admin/api/orders/${button.dataset.orderId}/activate-gift-cards`, {method: 'POST'});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    window.location.reload();
  } catch (error) {
    document.getElementById('admin-error').textContent = error.message;
    button.disabled = false;
  }
});

document.getElementById('import-card').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!window.confirm('Have you verified payment and the remaining balance for this existing card?')) return;
  const form = event.target;
  const fields = new FormData(form);
  const button = form.querySelector('button');
  button.disabled = true;
  try {
    const response = await fetch('/admin/api/gift-cards', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({order_id: Number(fields.get('order_id')), code: fields.get('code'), balance: fields.get('balance')})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    window.location.reload();
  } catch (error) {
    document.getElementById('admin-error').textContent = error.message;
    button.disabled = false;
  }
});
