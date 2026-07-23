# FanTread Website

The bilingual official website for
[FanTread](https://github.com/7757/FanTread), an open-source terminal reader
powered by DeepSeek.

Production: <https://7757.github.io/FanTread/>

## Local development

Requires Node.js 22.13 or newer.

```bash
npm install
npm run dev
```

Open <http://localhost:3000/FanTread/>.

## Verification

```bash
npm test
```

The test command creates the static GitHub Pages export and checks the rendered
product content, metadata, public links, author section, and social preview
asset.

## Structure

- `app/` — page, metadata, and responsive styling
- `public/og.png` — social sharing preview
- `tests/` — rendered HTML and asset checks
- `.github/workflows/pages.yml` — automated GitHub Pages deployment

## Author

Created by [musk (@7757)](https://github.com/7757).

FanTread and this website are released under the MIT License.
