"""Exercise the actual component using a small in-process DOM test double.

A real browser accessibility and keyboard check remains a separate acceptance
criterion; this check exercises component interactions and semantic attributes.
"""
import subprocess
script = r'''
const assert = require('assert');
class Element {
  constructor(tag, doc) { this.tagName = tag.toUpperCase(); this.ownerDocument = doc; this.children=[]; this.attributes={}; this.listeners={}; this.textContent=''; this.disabled=false; }
  appendChild(c) { this.children.push(c); return c; }
  append(...cs) { this.children.push(...cs); }
  replaceChildren(...cs) { this.children=[...cs]; }
  setAttribute(k,v) { this.attributes[k]=String(v); }
  getAttribute(k) { return this.attributes[k] ?? null; }
  addEventListener(k,f) { (this.listeners[k] ??= []).push(f); }
  dispatchEvent(e) { for(const f of this.listeners[e.type] || []) f(e); }
  click() { if(!this.disabled) this.dispatchEvent({type:'click'}); }
  querySelector(selector) { const match=e=>selector.startsWith('[') ? e.getAttribute(selector.slice(1,-1))!==null : e.tagName.toLowerCase()===selector; for(const c of this.children) { if(match(c)) return c; const nested=c.querySelector(selector); if(nested) return nested; } return null; }
}
const doc={createElement(tag){ return new Element(tag,doc); }};
const root=new Element('div',doc); let retried=0;
const {mount}=require('./component');
mount(root,'loading',()=>retried++);
let status=root.querySelector('[aria-live]'); assert(status && status.textContent.includes('Loading'));
mount(root,'error',()=>retried++);
let alert=root.querySelector('[role]'); assert(alert && alert.getAttribute('role')==='alert' && alert.textContent.includes('Error'));
let retry=root.querySelector('button'); assert(retry && retry.textContent.includes('Retry')); retry.click(); assert.equal(retried,1);
mount(root,'ready',()=>retried++);
let submit=root.querySelector('button'); assert(submit && submit.textContent.includes('Submit') && !submit.disabled);
'''
r=subprocess.run(['node','-e',script],capture_output=True,text=True,timeout=10)
assert r.returncode == 0, r.stderr
