import { writeFileSync, mkdirSync } from 'node:fs';
const tabs = await (await fetch('http://127.0.0.1:9222/json/list')).json();
const tab = tabs.find(t => t.type === 'page' && t.url.startsWith('http://127.0.0.1:8765'));
if (!tab) throw new Error('Local preview tab not found');
const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
let nextId = 1;
const waiting = new Map();
ws.onmessage = ({data}) => {
  const message = JSON.parse(data);
  if (waiting.has(message.id)) {
    const {resolve, reject, timer} = waiting.get(message.id);
    clearTimeout(timer); waiting.delete(message.id);
    if (message.error) reject(new Error(JSON.stringify(message.error))); else resolve(message.result);
  }
};
function send(method, params = {}) { return new Promise((resolve,reject) => {
  const id = nextId++;
  const timer = setTimeout(() => reject(new Error(`Timeout: ${method}`)), 15000);
  waiting.set(id,{resolve,reject,timer}); ws.send(JSON.stringify({id,method,params}));
}); }
async function evaluate(expression) {
  const response = await send('Runtime.evaluate',{expression, returnByValue:true, awaitPromise:true});
  if (response.exceptionDetails) throw new Error(JSON.stringify(response.exceptionDetails));
  return response.result.value;
}
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
mkdirSync('qa', {recursive:true});
try {
  await send('Page.enable');
  await send('Page.bringToFront');
  await send('Page.navigate', {url:'http://127.0.0.1:8765/'});
  await sleep(1200);
  await evaluate(`[...document.images].forEach(i=>i.loading='eager')`);
  await sleep(1000);
  const report = [];
  for (const width of [1440, 390, 320]) {
    await send('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:width<700});
    await sleep(250);
    const layout = await evaluate(`({width:innerWidth, scrollWidth:document.documentElement.scrollWidth, title:document.title, images:[...document.images].every(i=>i.complete && i.naturalWidth>0), downloads:[...document.querySelectorAll('a[download]')].map(a=>a.getAttribute('href'))})`);
    if (layout.scrollWidth > layout.width || !layout.images || !layout.downloads.length) throw new Error(JSON.stringify(layout));
    report.push(layout);
    const shot = await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});
    writeFileSync(`qa/website-${width}.png`,Buffer.from(shot.data,'base64'));
  }
  await evaluate(`document.getElementById('demo-button').click()`);
  await sleep(2200);
  const demo = await evaluate(`({text:document.getElementById('example-result').textContent, disabled:document.getElementById('demo-button').disabled})`);
  if (!demo.text.includes('8:30') || demo.disabled) throw new Error('Demo did not finish');
  const download = await evaluate(`(async()=>{const r=await fetch(document.querySelector('a[download]').href); const b=new Uint8Array(await r.arrayBuffer());return {status:r.status,bytes:b.length,zip:b[0]===80&&b[1]===75}})()`);
  if(download.status!==200 || !download.zip) throw new Error('Broken download');
  console.log(JSON.stringify({layouts:report,demo,download},null,2));
} finally { ws.close(); }
