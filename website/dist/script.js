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
  document.getElementById('download-size').textContent = `${(release.bytes / 1000000).toFixed(1)} MB installer EXE`;
}).catch(() => { /* The direct download remains usable without metadata. */ });

// Transparent task-time estimate: speech time includes user-selected overhead.
const controls = ['word-count', 'typing-speed', 'speaking-speed', 'extra-time'].map(id => document.getElementById(id));
function updateEstimate() {
  if (controls.some(input => !input.validity.valid || input.value === '')) {
    document.getElementById('time-saved').textContent = '—';
    document.getElementById('saving-description').textContent = 'Enter values within the indicated limits.';
    return;
  }
  const [words, typing, speaking, extra] = controls.map(input => Number(input.value));
  const typeMinutes = words / typing;
  const voiceMinutes = words / speaking + extra / 60;
  const saved = typeMinutes - voiceMinutes;
  const max = Math.max(typeMinutes, voiceMinutes);
  document.getElementById('word-count-label').textContent = words.toLocaleString();
  document.getElementById('typing-time').textContent = `${typeMinutes.toFixed(1)} min`;
  document.getElementById('dictation-time').textContent = `${voiceMinutes.toFixed(1)} min`;
  document.getElementById('typing-bar').style.width = `${typeMinutes / max * 100}%`;
  document.getElementById('dictation-bar').style.width = `${voiceMinutes / max * 100}%`;
  document.getElementById('time-saved').textContent = `${Math.abs(saved).toFixed(1)} min`;
  document.getElementById('saving-description').textContent = saved > .001
    ? `saved on this task · ${Math.round(saved / typeMinutes * 100)}% less time`
    : saved < -.001 ? 'longer with dictation in this example' : 'about the same time in this example';
}
controls.forEach(input => input.addEventListener('input', updateEstimate));
updateEstimate();
