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
    const layout = await evaluate(`({width:innerWidth, scrollWidth:document.documentElement.scrollWidth, title:document.title, images:[...document.images].every(i=>i.complete && i.naturalWidth>0), downloads:[...document.querySelectorAll('a[href$=".exe"]')].map(a=>a.getAttribute('href'))})`);
    if (layout.scrollWidth > layout.width || !layout.images || !layout.downloads.length) throw new Error(JSON.stringify(layout));
    report.push(layout);
    const shot = await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});
    writeFileSync(`qa/website-${width}.png`,Buffer.from(shot.data,'base64'));
  }
  const calculator = await evaluate(`(() => {
    const set = (id, value) => { const input = document.getElementById(id); input.value = value; input.dispatchEvent(new Event('input')); };
    const text = id => document.getElementById(id).textContent;
    const defaults = [text('typing-time'), text('dictation-time'), text('time-saved')];
    if (defaults.join('|') !== '12.5 min|5.2 min|7.3 min') throw Error('Default calculation is incorrect');
    set('typing-speed', 200); set('extra-time', 3600);
    if (!text('saving-description').includes('longer')) throw Error('Negative savings not disclosed');
    set('typing-speed', 0);
    if (text('time-saved') !== '—') throw Error('Invalid speed accepted');
    set('typing-speed', 120); set('speaking-speed', 120); set('extra-time', 0);
    if (!text('saving-description').includes('same time')) throw Error('Equal times incorrect');
    set('typing-speed', 40); set('extra-time', 60); set('word-count', 1000);
    if (text('typing-time') !== '25.0 min') throw Error('Word-count control failed');
    set('word-count', 500);
    document.querySelectorAll('details')[1].open = true;
    return {defaults, negativeSavings: 'passed', invalidInput: 'passed', equalTimes: 'passed', wordCount: 'passed'};
  })()`);
  await evaluate(`document.getElementById('demo-button').click()`);
  await sleep(2200);
  const demo = await evaluate(`({text:document.getElementById('example-result').textContent, disabled:document.getElementById('demo-button').disabled})`);
  if (!demo.text.includes('8:30') || demo.disabled) throw new Error('Demo did not finish');
  const url = await evaluate(`document.querySelector('a[href$=".exe"]').href`);
  const metadata = await (await fetch('http://127.0.0.1:8765/downloads/release.json')).json();
  const response = await fetch(url, {method:'HEAD'});
  const download = {status:response.status, bytes:Number(response.headers.get('content-length')), expected:metadata.bytes};
  if(download.status!==200 || download.bytes!==download.expected) throw new Error('Release asset is not published or is the wrong size');
  console.log(JSON.stringify({layouts:report,calculator,demo,download},null,2));
} finally { ws.close(); }
