const { chromium } = require('C:/Users/TRENDINGPC/projects/AI-job-search/apps/e2e/node_modules/playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push('[console] ' + m.text()); });
  page.on('pageerror', e => errors.push('[pageerror] ' + e.message));
  await page.goto('file:///C:/Users/TRENDINGPC/projects/AI-job-search/graphify-out/graph.html', { waitUntil: 'load', timeout: 60000 });
  await page.waitForTimeout(6000);
  const info = await page.evaluate(() => {
    const c = document.querySelector('#graph canvas');
    const nw = window.__net; // not exposed; check via body text
    return {
      canvases: document.querySelectorAll('#graph canvas').length,
      canvasSize: c ? c.width + 'x' + c.height : null,
      hasNetworkText: document.body.innerText.includes('commonlib'),
      hasNetwork: typeof window.network !== 'undefined',
      hasVis: typeof window.vis !== 'undefined',
    };
  });
  console.log('INFO', JSON.stringify(info));
  console.log('ERRORS (' + errors.length + '):');
  errors.slice(0, 20).forEach(e => console.log('  ' + e));
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})();
