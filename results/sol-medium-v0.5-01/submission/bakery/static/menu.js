const menuDate = document.getElementById('menu-date');
menuDate.value = localStorage.getItem('cornerloaf-date') || '';
let menuVersion = 0;
async function availability() {
  const version = ++menuVersion;
  document.querySelectorAll('button.add').forEach(b => { b.disabled = true; });
  if (!menuDate.value) return;
  localStorage.setItem('cornerloaf-date', menuDate.value);
  try {
    const response = await fetch(`/api/menu?date=${encodeURIComponent(menuDate.value)}`);
    const data = await response.json();
    if (version !== menuVersion) return;
    if (!response.ok) throw new Error(data.error);
    document.getElementById('menu-error').textContent = '';
    for (const product of data.products) {
      const button = document.querySelector(`button.add[data-sku="${product.sku}"]`);
      if (!button) continue;
      button.disabled = product.sold_out;
      button.textContent = product.sold_out ? 'Sold out' : 'Add';
      button.dataset.remaining = product.remaining === null ? '' : product.remaining;
    }
  } catch (error) { document.getElementById('menu-error').textContent = error.message; }
}
menuDate.addEventListener('change', availability);
availability();
