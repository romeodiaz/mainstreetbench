// Run: node tests/check_browser.js (from website). Exercises the scripts with a small DOM stub.
const fs = require('fs');
const vm = require('vm');
const assert = require('assert/strict');
const root = require('path').resolve(__dirname, '..');
function element() {
  return { dataset: {}, listeners: {}, children: [], disabled: false, value: '', textContent: '',
    innerHTML: '', addEventListener(type, handler) { this.listeners[type] = handler; },
    append(child) { this.children.push(child); },
    insertRow() { const row = element(); this.children.push(row); return row; },
    insertCell() { const cell = element(); this.children.push(cell); return cell; } };
}
(async () => {
  const nodes = new Map();
  const node = key => { if (!nodes.has(key)) nodes.set(key, element()); return nodes.get(key); };
  const storage = new Map();
  const values = { name: 'Ana', email: 'ana@example.com', phone: '', pickup_date: '2026-10-10',
    pickup_slot: '10:00', promo_code: 'WELCOME10', gift_card_code: '', newsletter: null };
  const calls = [];
  let resolveOrder;
  const context = vm.createContext({
    console, Map, Number, Math, Date, JSON, String,
    crypto: { randomUUID: () => 'browser-retry-id' },
    localStorage: { getItem: k => storage.get(k) ?? null, setItem: (k,v) => storage.set(k,v) },
    document: { getElementById: node, querySelector: node, createElement: element,
      addEventListener: (type,handler) => node('document').addEventListener(type,handler) },
    FormData: class { get(k) { return values[k]; } },
    window: {},
    fetch: async (url, options) => {
      calls.push({ url, body: options && JSON.parse(options.body) });
      if (url === '/api/orders') return new Promise(resolve => { resolveOrder = resolve; });
      if (url.startsWith('/api/slots')) return { ok:true, json:async()=>({open:true,slots:[]}) };
      return { ok:true, json:async()=>({ subtotal:15, discount:1.5, tax:1.11,total:14.61,
        gift_card_applied:0,amount_due:14.61,notes:[],priced_items:[{sku:'DOZEN13',unit_price:15,line_total:15}] }) };
    },
  });
  vm.runInContext(fs.readFileSync(root+'/bakery/static/cart.js','utf8'),context);
  vm.runInContext("addItem('DOZEN13', \"Baker's Dozen Cookies\", 15)",context);
  assert.equal(JSON.parse(storage.get('cornerloaf-cart'))[0].name,"Baker's Dozen Cookies");
  vm.runInContext(fs.readFileSync(root+'/bakery/static/checkout.js','utf8'),context);
  await new Promise(setImmediate);
  assert.equal(calls.find(x=>x.url==='/api/quote').body.promo_code,'WELCOME10');
  vm.runInContext("removeLine('DOZEN13')",context);
  assert.deepEqual(JSON.parse(storage.get('cornerloaf-cart')),[]);
  vm.runInContext("addItem('DOZEN13', \"Baker's Dozen Cookies\", 15)",context);
  const submit = node('checkout').listeners.submit;
  const first = submit({preventDefault(){}, target:node('checkout')});
  await submit({preventDefault(){},target:node('checkout')});
  assert.equal(calls.filter(x=>x.url==='/api/orders').length,1);
  assert.equal(node('place-order').disabled,true);
  resolveOrder({ok:false,json:async()=>({error:'Time full'})});
  await first;
  assert.equal(node('place-order').disabled,false);
  const retry=submit({preventDefault(){},target:node('checkout')});
  const orderCalls=calls.filter(x=>x.url==='/api/orders');
  assert.equal(orderCalls[0].body.request_id,orderCalls[1].body.request_id);
  resolveOrder({ok:true,json:async()=>({confirmation_url:'/order/1?key=private'})});
  await retry;
  assert.equal(context.window.location,'/order/1?key=private');
  assert.deepEqual(JSON.parse(storage.get('cornerloaf-cart')),[]);
  const pickup=element();pickup.dataset.date='2026-10-03';
  const dateContext=vm.createContext({Date,document:{querySelector:()=>pickup,getElementById:()=>null}});
  vm.runInContext(fs.readFileSync(root+'/bakery/static/confirmation.js','utf8'),dateContext);
  assert.match(pickup.textContent,/Saturday, October 3, 2026/);
  console.log('Browser-script checks passed: apostrophe cart, removal, coupon quote, double submit, retry, date.');
})().catch(error=>{console.error(error);process.exitCode=1;});
