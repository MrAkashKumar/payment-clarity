// State-transition tests against the actual app script, without a browser dependency.
const fs=require('node:fs');const vm=require('node:vm');const assert=require('node:assert/strict');
const elements=new Map();
function element(id){if(!elements.has(id))elements.set(id,{id,value:'',disabled:false,hidden:false,textContent:'',children:[],dataset:{},classList:{toggle(){}},setAttribute(k,v){this[k]=v},append(x){this.children.push(x)},replaceChildren(){this.children=[]},addEventListener(){},dispatchEvent(){this.oninput?.()}});return elements.get(id);}
const storage=new Map();const tabs=['investigation','handoff','preview'].map(x=>Object.assign(element('tab-'+x),{dataset:{tab:x}}));
const context=vm.createContext({document:{getElementById:element,querySelectorAll:()=>tabs,createElement:()=>element('new'+Math.random())},window:{addEventListener(){}},localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)},console,AbortController,setTimeout,clearTimeout,Event,URL,Blob});
const source=fs.readFileSync('web/app.js','utf8').replace(/^init\(\);$/m,'');
vm.runInContext(source,context);
const exec=s=>vm.runInContext(s,context);
exec(`state.selected='P50002';state.result={input_version:'version-one',draft:'Please confirm the payment purpose.',external_request_needed:true};loadDraft();`);
assert.equal(element('tab-preview').disabled,true);
element('review').onclick();assert.equal(element('tab-preview').disabled,false);assert.equal(exec('state.reviewed'),true);
exec("setStage('preview')");assert.equal(element('preview').hidden,false);assert.equal(element('preview-text').textContent,'Please confirm the payment purpose.');
console.log('PASS: preview requires review and shows the reviewed text');
element('draft').value='Please provide an invoice.';element('draft').oninput();assert.equal(exec('state.reviewed'),false);assert.equal(element('tab-preview').disabled,true);
console.log('PASS: editing invalidates review');
element('review').onclick();exec('loadDraft()');assert.equal(exec('state.reviewed'),true);assert.equal(element('draft').value,'Please provide an invoice.');
console.log('PASS: same-source draft and review persist');
exec("state.result.input_version='version-two';loadDraft()");assert.equal(exec('state.reviewed'),false);assert.equal(element('draft').value,'Please confirm the payment purpose.');
console.log('PASS: source version changes invalidate saved review');
exec("state.result.external_request_needed=false;state.reviewed=true;updateReview();setStage('investigation');setStage('preview')");assert.equal(element('tab-preview').disabled,true);assert.equal(exec('state.stage'),'investigation');
console.log('PASS: internal-only cases cannot open a customer preview');
