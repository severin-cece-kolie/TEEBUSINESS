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
  CDN-compatible preview and the native standalone build described below.
- `check-tailwind-classes.mjs`: verifies that Alpine/Django conditional classes
  and the explicit safelist exist in the standalone output.
- `static/css/tailwind.generated.css`: generated output. It is kept separate
  from `output.css` and is loaded before the Tailwind CDN during parity checks.
- `static/css/tailwind.standalone.css`: native Tailwind v4 output with no
  coexistence filtering. It is loaded only in the explicit standalone test
  mode.

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

The standalone output is written from the same raw CLI build before that
filtering. Its source also preserves the Tailwind v3 colors and the few
Preflight defaults used by the current interface.

## Switching modes locally

The current CDN mode remains the default. The switch is enabled only when
Django `DEBUG=True` and is persisted in an HTTP-only cookie for eight hours.

- current CDN stack: `/?tailwind=current`
- standalone Tailwind v4: `/?tailwind=standalone`
- clear the preview cookie: `/?tailwind=reset`

After opening one of these URLs, normal navigation stays in the selected mode.
The `<html>` element exposes `data-tailwind-mode="current"` or
`data-tailwind-mode="standalone"` for inspection.

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

Create both minified outputs:

```bash
npm run build
```

Verify conditional and safelisted classes:

```bash
npm run check:css
```

The standalone mode does not affect Django admin, which uses Unfold's own base
templates and assets. Keep the CDN as the default until the manual
desktop/mobile comparison in `STANDALONE_VALIDATION.md` has been completed.
