const products = JSON.parse(document.getElementById('products').textContent);
const limitForm = document.getElementById('limits');
const productSelect = limitForm.elements.sku;
const limitInput = limitForm.elements.daily_limit;
for (const p of products) productSelect.add(new Option(p.name, p.sku));
function showLimit() {
  limitInput.value = products.find((p) => p.sku === productSelect.value).daily_limit ?? '';
}
productSelect.addEventListener('change', showLimit);
showLimit();
limitForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const sku = productSelect.value;
  const message = document.getElementById('limit-message');
  try {
    const response = await fetch(`/admin/api/products/${encodeURIComponent(sku)}`, {
      method: 'PUT', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({daily_limit: limitInput.value === '' ? null : Number(limitInput.value)}),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    products.find((p) => p.sku === sku).daily_limit = data.daily_limit;
    message.textContent = `Saved daily limit for ${data.name}.`;
  } catch (error) {
    message.textContent = error.message;
  }
});
