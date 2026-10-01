const checkout = document.getElementById('checkout');
const submit = checkout.querySelector('button[type="submit"]');
const errorBox = document.getElementById('checkout-error');
const quoteBox = document.getElementById('quote');
const dateInput = checkout.elements.pickup_date;
const timeInput = checkout.elements.pickup_time;
let revision = 0;
let placing = false;
const dollars = n => '$' + Number(n).toFixed(2);
dateInput.value = localStorage.getItem('cornerloaf-date') || '';
function payload() {
  const form = new FormData(checkout);
  return {
    customer: {name: form.get('name'), email: form.get('email'), phone: form.get('phone')},
    pickup_date: form.get('pickup_date'), pickup_time: form.get('pickup_time'),
    promo_code: form.get('promo_code'), gift_card_code: form.get('gift_card_code'),
    items: readCart().map(l => ({sku: l.sku, qty: l.qty}))
  };
}
function renderLines() {
  const table = document.getElementById('cart-lines');
  table.replaceChildren();
  for (const line of readCart()) {
    const row = table.insertRow();
    row.insertCell().textContent = line.name;
    const input = document.createElement('input');
    input.type = 'number'; input.min = 1; input.max = 50; input.step = 1; input.value = line.qty;
    input.setAttribute('aria-label', `Quantity of ${line.name}`);
    input.addEventListener('change', () => {
      const qty = Number(input.value);
      if (!Number.isInteger(qty) || qty < 1 || qty > 50) { input.value = line.qty; return; }
      const cart = readCart(); cart.find(l => l.sku === line.sku).qty = qty;
      writeCart(cart); renderLines(); refresh(true);
    });
    row.insertCell().append(input);
    row.insertCell().textContent = dollars(line.qty * line.price);
    const remove = document.createElement('button');
    remove.type = 'button'; remove.textContent = 'Remove';
    remove.addEventListener('click', () => { writeCart(readCart().filter(l => l.sku !== line.sku)); renderLines(); refresh(true); });
    row.insertCell().append(remove);
  }
  if (!readCart().length) table.insertRow().insertCell().textContent = 'Your cart is empty. Add items from the menu.';
}
async function refresh(updateSlots = false) {
  const version = ++revision;
  submit.disabled = true;
  quoteBox.textContent = 'Updating total…';
  errorBox.textContent = '';
  try {
    if (updateSlots) {
      const previous = timeInput.value;
      const response = await fetch(`/api/pickup-slots?date=${encodeURIComponent(dateInput.value)}&skus=${encodeURIComponent(readCart().map(l => l.sku).join(','))}`);
      const data = await response.json();
      if (version !== revision) return;
      if (!response.ok) throw new Error(data.error);
      timeInput.replaceChildren(new Option('Choose a pickup time', ''));
      for (const slot of data.slots) {
        const option = new Option(slot.time + (slot.available ? '' : ' — unavailable'), slot.time);
        option.disabled = !slot.available; timeInput.append(option);
      }
      if (data.slots.some(s => s.time === previous && s.available)) timeInput.value = previous;
    }
    if (!timeInput.value) throw new Error('Choose an available pickup time to see your total.');
    const response = await fetch('/api/quote', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload())});
    const data = await response.json();
    if (version !== revision) return;
    if (!response.ok) throw new Error(data.error);
    quoteBox.replaceChildren();
    for (const [label, key] of [['Subtotal','subtotal'], ['Coupon discount','discount'], ['Sales tax','tax'], ['Total','total'], ['Gift card payment','gift_card_applied'], ['Due at pickup','amount_due']]) {
      const p = document.createElement('p'); p.textContent = `${label}: ${dollars(data[key])}`; quoteBox.append(p);
    }
    if (data.gift_card_balance !== null) {
      const p = document.createElement('p'); p.textContent = `Gift card balance after payment: ${dollars(data.gift_card_balance)}`; quoteBox.append(p);
    }
    submit.disabled = placing;
  } catch (error) {
    if (version !== revision) return;
    quoteBox.textContent = ''; errorBox.textContent = error.message;
  }
}
checkout.addEventListener('input', event => {
  if (['pickup_date', 'pickup_time', 'promo_code', 'gift_card_code'].includes(event.target.name)) {
    if (event.target === dateInput) localStorage.setItem('cornerloaf-date', dateInput.value);
    refresh(event.target === dateInput);
  }
});
checkout.addEventListener('submit', async event => {
  event.preventDefault();
  if (submit.disabled || placing) return;
  placing = true; ++revision; submit.disabled = true;
  try {
    const response = await fetch('/api/orders', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload())});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    writeCart([]); window.location = `/order/${data.id}`;
  } catch (error) {
    placing = false; errorBox.textContent = error.message;
    quoteBox.textContent = 'Please update your selection to refresh the total.';
  }
});
renderLines(); refresh(true);
