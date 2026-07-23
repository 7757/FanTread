import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const developmentPreviewMeta =
  /<meta(?=[^>]*\bname=["']codex-preview["'])(?=[^>]*\bcontent=["']development["'])[^>]*>/i;

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the FanTread product landing page", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
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
    /<meta property="og:image" content="http:\/\/localhost(?::3000)?\/og\.png"\/>/i,
  );
  assert.doesNotMatch(html, /Your site is taking shape|react-loading-skeleton/);
});

test("keeps finished metadata, source, and social assets aligned", async () => {
  const [page, layout, css, packageJson, socialImage] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
    readFile(new URL("../public/og.png", import.meta.url)),
  ]);

  assert.match(page, /npm install -g fantread/);
  assert.match(page, /type Locale = "zh" \| "en"/);
  assert.match(page, /https:\/\/github\.com\/7757/);
  assert.match(page, /https:\/\/avatars\.githubusercontent\.com/);
  assert.match(layout, /generateMetadata/);
  assert.match(layout, /x-forwarded-host/);
  assert.match(layout, /\/og\.png/);
  assert.match(layout, /name: "musk"/);
  assert.match(css, /--lime:\s*#caff69/);
  assert.match(css, /prefers-reduced-motion:\s*reduce/);
  assert.match(packageJson, /"name": "fantread-website"/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);
  assert.doesNotMatch(page + layout, /codex-preview|_sites-preview/);

  assert.deepEqual([...socialImage.subarray(0, 8)], [
    0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
  ]);
  assert.ok(socialImage.byteLength > 100_000);
});
