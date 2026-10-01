const fs = require('fs'), vm = require('vm'), assert = require('assert');
const root = require('path').join(__dirname, '../website/bakery/static/');
for (const file of ['cart.js','menu.js','checkout.js','confirmation.js']) new vm.Script(fs.readFileSync(root+file,'utf8'));
const memory = new Map(); const handlers = {}; const elements = new Map();
function el(id) { if (!elements.has(id)) elements.set(id,{value:'',textContent:'',innerHTML:'',disabled:false,
 addEventListener:(type,fn)=>handlers[id+':'+type]=fn,append(){},insertRow(){return {dataset:{},insertCell:()=>({append(){}})}}}); return elements.get(id); }
const doc = {getElementById:el,addEventListener:(t,f)=>handlers['document:'+t]=f,
 querySelector:(q)=>el(q),createElement:()=>({append(){},addEventListener(){}})};
const fields={name:'Ana',email:'ana@example.com',phone:'555-0100',pickup_date:'2026-10-10',pickup_slot:'10:00',promo_code:'WELCOME10',newsletter:null};
let orders=0, submitted, release;
const context=vm.createContext({document:doc,localStorage:{getItem:k=>memory.get(k),setItem:(k,v)=>memory.set(k,v)},
 crypto:{randomUUID:()=> 'unique-retry-key'},FormData:class {get(k){return fields[k]}},window:{},
 fetch:async(url,opts)=>{
 if(url==='/api/orders') {orders++;submitted=JSON.parse(opts.body);await new Promise(r=>release=r);return {ok:true,json:async()=>({confirmation_url:'/order/1?key=private'})};}
 if(url==='/api/quote') {const p=JSON.parse(opts.body);assert.equal(p.promo_code,'WELCOME10');return {ok:true,json:async()=>({subtotal:9,discount:.9,tax:.67,total:8.77,amount_due:8.77,notes:[]})};}
 return {ok:true,json:async()=>({open:true,slots:[{time:'10:00',remaining:4,available:true}]})};
 }});
async function main(){
 vm.runInContext(fs.readFileSync(root+'cart.js','utf8'),context);
 vm.runInContext(`addItem('DOZEN13',"Baker's Dozen Cookies",15);`,context);
 assert.equal(JSON.parse(memory.get('cornerloaf-cart'))[0].name,"Baker's Dozen Cookies");
 vm.runInContext(fs.readFileSync(root+'menu.js','utf8'),context);
 assert.equal(JSON.parse(memory.get('cornerloaf-cart')).length,1,'menu navigation must preserve cart');
 vm.runInContext(fs.readFileSync(root+'checkout.js','utf8'),context);
 vm.runInContext(`removeLine('DOZEN13')`,context);
 assert.equal(JSON.parse(memory.get('cornerloaf-cart')).length,0);
 assert.equal(el('cart-count').textContent,0);
 vm.runInContext(`addItem('BREAD9','Sourdough Loaf',9)`,context);
 const submit=handlers['checkout:submit'];const event={preventDefault(){},target:{}};
 const first=submit(event);await submit(event);assert.equal(orders,1);assert(el('place-order').disabled);
 assert.equal(submitted.request_id,'unique-retry-key');assert.equal(submitted.newsletter,false);
 release();await first;assert.equal(context.window.location,'/order/1?key=private');assert.equal(JSON.parse(memory.get('cornerloaf-cart')).length,0);
 process.env.TZ='America/Chicago';
 const pickup={dataset:{date:'2026-10-03'}};
 vm.runInNewContext(fs.readFileSync(root+'confirmation.js','utf8'),{document:{querySelector:()=>pickup,getElementById:()=>null},Date});
 assert(pickup.textContent.startsWith('Saturday'),pickup.textContent);
 console.log('JavaScript checks passed: syntax, cart persistence/removal, quote coupon, single submission with retry ID, newsletter opt-in, confirmation day.');
}
main().catch(e=>{console.error(e);process.exitCode=1});
