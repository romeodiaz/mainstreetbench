const cancelButton = document.getElementById('cancel-order');
cancelButton.hidden = cancelButton.dataset.status !== 'placed';
cancelButton.addEventListener('click', async () => {
  cancelButton.disabled = true;
  try {
    const response = await fetch(`/api/orders/${cancelButton.dataset.id}/cancel`, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({cancel_token: cancelButton.dataset.token})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    window.location.reload();
  } catch (error) {
    document.getElementById('cancel-error').textContent = error.message;
    cancelButton.disabled = false;
  }
});
