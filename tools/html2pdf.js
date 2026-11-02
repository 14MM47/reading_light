// Print HTML files to A4 PDFs with the pre-installed Chromium (Playwright).
// Usage: node tools/html2pdf.js <in1.html> <out1.pdf> [<in2.html> <out2.pdf> ...]
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const args = process.argv.slice(2);
  if (args.length === 0 || args.length % 2) {
    console.error('usage: html2pdf.js in.html out.pdf [...]');
    process.exit(2);
  }
  const browser = await chromium.launch();
  const page = await browser.newPage();
  for (let i = 0; i < args.length; i += 2) {
    const src = 'file://' + path.resolve(args[i]);
    await page.goto(src, { waitUntil: 'load' });
    await page.pdf({
      path: args[i + 1], format: 'A4', printBackground: true,
      margin: { top: '16mm', bottom: '16mm', left: '14mm', right: '14mm' },
      displayHeaderFooter: true,
      headerTemplate: '<div></div>',
      footerTemplate: '<div style="font-size:8px;width:100%;text-align:center;color:#666">' +
        'Moon reading light v0.1 &middot; <span class="title"></span> &middot; page <span class="pageNumber"></span>' +
        ' / <span class="totalPages"></span></div>',
    });
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
