# Frontend build

This directory contains the local Tailwind CSS v4 workflow for the
server-rendered Django application. Tailwind is compiled locally; the
storefront and authentication templates no longer load the Tailwind CDN.

## Files

- `tailwind.css`: canonical Tailwind v4 source, source paths, theme tokens, and
  the small custom rules currently present in `static/css/output.css`.
- `safelist.txt`: complete utility names used in Alpine/Django conditional
  states. Add entries only when a class cannot be detected as a literal string
  in a scanned source file.
- `check-tailwind-classes.mjs`: verifies that Alpine/Django conditional classes
  and the explicit safelist exist in the generated output.
- `static/css/tailwind.standalone.css`: canonical generated Tailwind v4 output
  loaded by the storefront and authentication templates.

`static/css/output.css` and `static/css/premium.css` remain separate and load
after Tailwind so their custom rules stay prioritized.

The source list includes both Django template trees and the Python form modules
that assign Tailwind classes to Django widgets.

The canonical source preserves the Tailwind v3 colors and the small set of
Preflight defaults established during visual parity testing.

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

Create the minified production CSS:

```bash
npm run build
```

Verify conditional and safelisted classes:

```bash
npm run check:css
```

Django admin uses Unfold's own templates and assets, so it does not load the
storefront Tailwind stylesheet.

## CSS loading order

Storefront:

1. `tailwind.standalone.css`;
2. `output.css`;
3. `premium.css`;
4. template-specific styles from `extra_head` / `extra_css`.

Authentication:

1. `tailwind.standalone.css`;
2. existing inline authentication styles;
3. template-specific styles from `extra_css`.

`static/css/tailwind.generated.css` is a retained migration artifact and is no
longer generated or loaded. It can be removed in a separate cleanup after the
local Tailwind rollout has remained stable.
