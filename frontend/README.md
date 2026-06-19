# Frontend assets

TEEBUSINESS remains a server-rendered Django application. Node is used only to
compile Tailwind CSS v4; there is no React, Vite, SPA, or frontend API workflow
in the active application. The unused historical React/Vite `dist/` build was
removed after a repository-wide dependency audit.

## Canonical files

- `frontend/tailwind.css`: hand-authored Tailwind v4 source. It contains source
  discovery paths, theme tokens, v3 parity defaults, and the small
  `.btn-luxury`/form compatibility rules.
- `frontend/safelist.txt`: complete classes used in Django or Alpine branches
  that cannot always be inferred safely from static template scanning.
- `frontend/check-tailwind-classes.mjs`: verifies the dynamic classes and
  safelist against the compiled CSS.
- `static/css/tailwind.css`: generated, minified CSS served by Django. Do not
  edit it manually.
- `static/css/premium.css`: active hand-authored storefront components for
  heroes, panels, filters, auth layouts, product cards, and product detail.

The detailed inventory and cleanup decisions are recorded in
`frontend/ASSET_AUDIT.md`.

Legacy Tailwind v3 inputs/configuration, the unused static design-system CSS,
the retired browser-side currency helper, and unreferenced favicon variants
were removed after a repository-wide reference audit.

## Installation and commands

Install the exact locked dependencies:

```bash
npm ci
```

Compile readable CSS once:

```bash
npm run dev
```

Watch templates and source files during development:

```bash
npm run watch
```

Create the minified deployable CSS:

```bash
npm run build
```

Verify Django/Alpine conditional classes:

```bash
npm run check:css
```

## CSS loading order

The storefront loads:

1. `static/css/tailwind.css`;
2. `static/css/premium.css`;
3. template-specific `extra_head` / `extra_css` styles.

Authentication pages load `static/css/tailwind.css`, then their existing
inline custom styles and optional `extra_css`. Django admin uses Unfold's own
assets and does not consume the storefront Tailwind CSS.

## Git and deployment policy

Version these sources:

- `package.json` and `package-lock.json`;
- everything under `frontend/`;
- hand-authored files under `static/`;
- `static/css/tailwind.css`.

Ignore `node_modules/` and `staticfiles/`. The compiled Tailwind file remains
versioned because no deployment automation currently proves that Node runs
before Django `collectstatic`. A deployment should therefore use the checked-in
CSS or explicitly run:

```bash
npm ci
npm run build
.venv/bin/python manage.py collectstatic --noinput
```

After changing templates, forms, `frontend/tailwind.css`, or the safelist, run
both `npm run build` and `npm run check:css` and commit the regenerated CSS.
