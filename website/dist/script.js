'use strict';
const demoButton = document.getElementById('demo-button');
const result = document.getElementById('example-result');
const demoStatus = document.getElementById('demo-status');
let playing = false;
demoButton.addEventListener('click', async () => {
  if (playing) return;
  playing = true;
  demoButton.disabled = true;
  demoStatus.textContent = 'EXAMPLE · TRANSCRIBING';
  document.querySelector('.demo-section').classList.add('is-playing');
  const sentence = 'Our train was scheduled to arrive at 8:30, but it was an hour late.';
  result.textContent = '';
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  for (const word of sentence.split(' ')) {
    if (!reducedMotion) await new Promise(resolve => setTimeout(resolve, 85));
    result.append(document.createTextNode((result.textContent ? ' ' : '') + word));
  }
  demoStatus.textContent = 'EXAMPLE COMPLETE · PROCESSED LOCALLY';
  demoButton.textContent = 'Replay the example ↻';
  document.querySelector('.demo-section').classList.remove('is-playing');
  demoButton.disabled = false;
  playing = false;
});
fetch('downloads/release.json').then(response => {
  if (!response.ok) throw new Error('No release metadata');
  return response.json();
}).then(release => {
  document.getElementById('download-size').textContent = `${Math.ceil(release.bytes / 1024)} KB setup ZIP`;
}).catch(() => { /* The direct download remains usable without metadata. */ });
