# Frontend build

This directory contains the progressive Tailwind CSS v4 workflow for the
server-rendered Django application. It does not introduce React, Vite, or a
separate frontend application.

## Files

- `tailwind.css`: canonical Tailwind v4 source, source paths, theme tokens, and
  the small custom rules currently present in `static/css/output.css`.
- `safelist.txt`: complete utility names used in Alpine/Django conditional
  states. Add entries only when a class cannot be detected as a literal string
  in a scanned source file.
- `tailwind-workflow.mjs`: runs the official CLI and prepares the temporary
  CDN-compatible preview described below.
- `static/css/tailwind.generated.css`: generated output. It is kept separate
  from `output.css` and is loaded before the Tailwind CDN during parity checks.

`static/css/premium.css`, the Tailwind CDN scripts, and their inline
compatibility configurations remain active for now.

The source list includes both Django template trees and the Python form modules
that assign Tailwind classes to Django widgets.

## Temporary CDN compatibility

Tailwind v4 emits typed CSS `@property` registrations for internal variables.
When the v3 CDN runtime is loaded on the same page, those registrations reject
some legacy gradient values and visibly change hero overlays.

Tailwind v4 also emits individual `scale`, `translate`, and `rotate`
properties, while the CDN v3 runtime emits a composed `transform`. Applying
both doubles some transforms.

During this coexistence phase, `tailwind-workflow.mjs` removes those
registrations and individual transform declarations from the generated
preview. The CDN remains authoritative for gradients and transforms; the other
utilities and theme remain v4. Remove this post-processing step when the CDN is
removed so the final standalone v4 build keeps Tailwind's native output.

## Commands

Install dependencies:

```bash
npm install
```

Compile once for local inspection:

```bash
npm run dev
```

Recompile while editing templates or CSS:

```bash
npm run watch
```

Create the minified production candidate:

```bash
npm run build
```

After every build, keep using the CDN until desktop/mobile visual comparison
has confirmed parity for the storefront, authentication pages, cart/checkout,
customer account, and admin boundaries.
