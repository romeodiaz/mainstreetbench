// Checkout interaction checks using a minimal DOM and mocked network; no live orders.
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const path = require('path');
class Element {
  constructor() { this.listeners = {}; this.children = []; this.dataset = {}; this.value = ''; this.disabled = false; this.rows = []; }
  addEventListener(event, fn) { this.listeners[event] = fn; }
  append(child) { this.children.push(child); }
  insertRow() { const row = new Element(); this.rows.push(row); return row; }
  insertCell() { const cell = new Element(); this.children.push(cell); return cell; }
  set innerHTML(v) { this.html = v; this.rows = []; }
  get innerHTML() { return this.html || ''; }
}
const elements = new Map();
function element(key) { if (!elements.has(key)) elements.set(key, new Element()); return elements.get(key); }
const storage = () => { const data = new Map(); return { getItem: k => data.get(k) || null, setItem: (k,v) => data.set(k,String(v)), removeItem: k => data.delete(k) }; };
const values = { name:'Ana', email:'ana@example.com', phone:'555-0100', pickup_date:'2026-10-10', pickup_slot:'10:00' };
let orderCalls = [], resolveOrder, failNext = false;
const context = vm.createContext({
  document: { getElementById: element, querySelector: element, createElement: () => new Element(), addEventListener() {} },
  localStorage: storage(), sessionStorage: storage(),
  FormData: class { get(key) { return values[key] || ''; } },
  crypto: { randomUUID: (() => { let n=0; return () => `test-request-${++n}`; })() },
  window: {},
  fetch: async (url, options) => {
    if (url.startsWith('/api/slots')) return { ok:true, json:async()=>({open:true, slots:[{time:'10:00',remaining:4,available:true}]}) };
    const payload = JSON.parse(options.body);
    if (url === '/api/quote') return { ok:true, json:async()=>({subtotal:18,discount:0,tax:1.49,total:19.49,amount_due:19.49,notes:[]}) };
    orderCalls.push(payload);
    if (failNext) { failNext=false; throw new Error('connection interrupted'); }
    return await new Promise(resolve => { resolveOrder = () => resolve({ok:true,json:async()=>({confirmation_url:'/order/1?key=private'})}); });
  },
});
const source = name => fs.readFileSync(path.join(__dirname,'../bakery/static',name),'utf8');
vm.runInContext(source('cart.js'),context);
vm.runInContext('writeCart([{sku:"BREAD9",name:"Bread",price:9,qty:2},{sku:"SCONE375",name:"Scone",price:3.75,qty:1}]);',context);
vm.runInContext(source('checkout.js'),context);
const tick = () => new Promise(resolve => setImmediate(resolve));
(async () => {
  await tick();
  const table = element('cart-lines');
  const remove = table.rows[1].children[3].children[0];
  remove.listeners.click();
  await tick();
  assert.equal(JSON.parse(context.localStorage.getItem('cornerloaf-cart')).length,1,'Remove must update stored cart');
  const submit = element('checkout').listeners.submit;
  const event = {preventDefault(){},target:element('checkout')};
  const first = submit(event);
  await tick();
  await submit(event);
  assert.equal(orderCalls.length,1,'Repeated submit must not send another request');
  assert.ok(orderCalls[0].request_id,'Checkout must send retry identifier');
  assert.equal(element('place-order').disabled,true);
  resolveOrder(); await first;
  assert.equal(context.window.location,'/order/1?key=private');
  assert.equal(JSON.parse(context.localStorage.getItem('cornerloaf-cart')).length,0);
  assert.equal(context.sessionStorage.getItem('cornerloaf-pending-order'),null);
  // Simulate a fresh page: check that a failed network request leaves a reusable identifier.
  vm.runInContext('placing=false; writeCart([{sku:"BREAD9",name:"Bread",price:9,qty:2}]);',context);
  failNext=true; await submit(event);
  assert.equal(element('place-order').disabled,false);
  const failedId = orderCalls[1].request_id;
  const retry=submit(event); await tick();
  assert.equal(orderCalls[2].request_id,failedId,'Network retry must use the same identifier');
  resolveOrder(); await retry;
  console.log('Checkout passed: removal, repeated submit, network retry, private redirect and cart clearing.');
})().catch(error=>{console.error(error);process.exitCode=1;});
