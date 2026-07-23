import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const developmentPreviewMeta =
  /<meta(?=[^>]*\bname=["']codex-preview["'])(?=[^>]*\bcontent=["']development["'])[^>]*>/i;

test("exports the FanTread product landing page for GitHub Pages", async () => {
  const html = await readFile(new URL("../out/index.html", import.meta.url), "utf8");

  assert.doesNotMatch(html, developmentPreviewMeta);
  assert.match(
    html,
    /<title>FanTread — Turn any link into what you actually need<\/title>/i,
  );
  assert.match(html, /把网页，读成/);
  assert.match(html, /你真正需要的内容。/);
  assert.match(html, /npm install -g fantread/);
  assert.match(html, /FanTread 与 FastCut 作者/);
  assert.match(html, /https:\/\/github\.com\/7757\/FanTread/);
  assert.match(html, /https:\/\/www\.npmjs\.com\/package\/fantread/);
  assert.match(
    html,
    /<meta property="og:image" content="https:\/\/7757\.github\.io\/FanTread\/og\.png"\/?>/i,
  );
  assert.match(html, /(?:src|href)="\/FanTread\/_next\//i);
  assert.doesNotMatch(html, /Your site is taking shape|react-loading-skeleton/);
});

test("keeps static metadata, source, and public assets aligned", async () => {
  const [page, layout, css, packageJson, socialImage, exportedImage, noJekyll] =
    await Promise.all([
      readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
      readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
      readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
      readFile(new URL("../package.json", import.meta.url), "utf8"),
      readFile(new URL("../public/og.png", import.meta.url)),
      readFile(new URL("../out/og.png", import.meta.url)),
      readFile(new URL("../out/.nojekyll", import.meta.url)),
    ]);

  assert.match(page, /npm install -g fantread/);
  assert.match(page, /type Locale = "zh" \| "en"/);
  assert.match(page, /https:\/\/github\.com\/7757/);
  assert.match(page, /https:\/\/avatars\.githubusercontent\.com/);
  assert.match(layout, /https:\/\/7757\.github\.io\/FanTread\//);
  assert.match(layout, /name: "musk"/);
  assert.doesNotMatch(layout, /headers\(\)|x-forwarded-host/);
  assert.match(css, /--lime:\s*#caff69/);
  assert.match(css, /prefers-reduced-motion:\s*reduce/);
  assert.match(packageJson, /"name": "fantread-website"/);
  assert.match(packageJson, /"build": "next build"/);
  assert.doesNotMatch(packageJson, /vinext|wrangler|react-loading-skeleton/);
  assert.doesNotMatch(page + layout, /codex-preview|_sites-preview/);

  const pngSignature = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
  assert.deepEqual([...socialImage.subarray(0, 8)], pngSignature);
  assert.deepEqual([...exportedImage.subarray(0, 8)], pngSignature);
  assert.ok(socialImage.byteLength > 100_000);
  assert.equal(noJekyll.toString("utf8").trim(), "");
});
