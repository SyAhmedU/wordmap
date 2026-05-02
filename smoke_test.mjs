// Smoke test: load index.html into jsdom, populate window.__WORDS_DATA__ from data.js,
// inject d3 from node_modules, run boot(), and verify the treemap rendered cells.
import jsdomPkg from 'jsdom';
import * as d3 from 'd3';
import fs from 'fs';
const { JSDOM } = jsdomPkg;

const html = fs.readFileSync('index.html', 'utf-8')
  // Remove the CDN d3 script and the data.js script — we'll inject manually
  .replace(/<script src="https:\/\/cdnjs[^"]+"><\/script>/, '')
  .replace(/<script src="data\.js"><\/script>/, '');

const dataJs = fs.readFileSync('data.js', 'utf-8');

const dom = new JSDOM(html, {
  runScripts: 'outside-only',
  pretendToBeVisual: true,
});

// Inject d3 into the window
dom.window.d3 = d3;
// Run data.js to set window.__WORDS_DATA__
dom.window.eval(dataJs);

// Set viewport size (jsdom doesn't lay out so we manually set clientWidth/Height)
Object.defineProperty(dom.window.HTMLElement.prototype, 'clientWidth', { get() { return 1400; }});
Object.defineProperty(dom.window.HTMLElement.prototype, 'clientHeight', { get() { return 700; }});

// Now run the inline script (extract from html)
const inlineScript = html.match(/<script>([\s\S]+?)<\/script>/g).pop().replace(/<\/?script>/g, '');
try {
  dom.window.eval(inlineScript);
} catch (e) {
  console.error('Inline script error:', e.message, '\n', e.stack);
  process.exit(1);
}

// Wait a tick for boot() (it's async)
await new Promise(r => setTimeout(r, 300));

const doc = dom.window.document;
const cells = doc.querySelectorAll('g.cell');
const groups = doc.querySelectorAll('g.group');
const yearLabel = doc.getElementById('year-label').textContent;
const stats = {
  mentions: doc.getElementById('stat-mentions').textContent,
  terms: doc.getElementById('stat-terms').textContent,
  topShare: doc.getElementById('stat-top-share').textContent,
  fastest: doc.getElementById('stat-fastest').textContent,
};

console.log('Year shown:', yearLabel);
console.log('Group rectangles:', groups.length);
console.log('Term cells rendered:', cells.length);
console.log('Stats:', stats);

if (cells.length === 0) {
  console.error('FAIL: no cells rendered');
  process.exit(1);
}
if (groups.length === 0) {
  console.error('FAIL: no group rectangles');
  process.exit(1);
}

// Sample first 5 cells - get their position and color
console.log('\nFirst 5 cells:');
for (let i = 0; i < Math.min(5, cells.length); i++) {
  const cell = cells[i];
  const rect = cell.querySelector('rect');
  const text = cell.querySelector('text.term-name');
  console.log(`  ${text?.textContent || '(no label)'} — fill=${rect?.getAttribute('fill')} size=${rect?.getAttribute('width')}x${rect?.getAttribute('height')}`);
}

// Verify scrubbing to year 1980
console.log('\n--- Scrubbing to 1980 ---');
dom.window.state.year = 1980;
dom.window.applyAll();
await new Promise(r => setTimeout(r, 100));
const cells80 = doc.querySelectorAll('g.cell');
console.log('Year 1980 cells:', cells80.length);
console.log('Year 1980 stats:', {
  mentions: doc.getElementById('stat-mentions').textContent,
  terms: doc.getElementById('stat-terms').textContent,
  topShare: doc.getElementById('stat-top-share').textContent,
});

// Try a different metric
console.log('\n--- Switching metric to "share" ---');
dom.window.state.metric = 's';
dom.window.applyAll();
await new Promise(r => setTimeout(r, 50));
const cellsShare = doc.querySelectorAll('g.cell');
console.log('Cells after metric switch:', cellsShare.length);

console.log('\n✓ Smoke test PASSED');
