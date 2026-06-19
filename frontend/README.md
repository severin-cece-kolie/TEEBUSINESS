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
- `static/css/tailwind.generated.css`: generated output. It is kept separate
  from `output.css` and is not linked by templates during the parity phase.

`static/css/premium.css`, the Tailwind CDN scripts, and their inline
compatibility configurations remain active for now.

The source list includes both Django template trees and the Python form modules
that assign Tailwind classes to Django widgets.

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
