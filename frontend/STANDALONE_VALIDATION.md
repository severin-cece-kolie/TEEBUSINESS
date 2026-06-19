# Tailwind v4 standalone migration record

The standalone candidate was accepted as the storefront's canonical Tailwind
build. The temporary current/standalone cookie switch and the Tailwind CDN were
removed after manual parity validation.

## Final CSS order

1. `tailwind.standalone.css`;
2. `output.css`;
3. `premium.css`.

Authentication pages keep their existing inline custom CSS after the selected
Tailwind stylesheet. Django admin is independent and unchanged.

## Corrections already included

The native v4 source preserves current Tailwind v3 behavior for:

- red, orange, amber, green, and gray utility colors used by templates;
- `rounded-sm`, `blur-sm`, and `shadow-sm`;
- default border color;
- form placeholder color;
- pointer cursors on enabled buttons and `[role="button"]`.

These are explicit v3-to-v4 compatibility rules, not page-specific overrides.

All classes listed in `safelist.txt` are present in the standalone build.

## Technical validation

Completed without browser automation:

- `npm run build`;
- `npm run check:css` (28 dynamic/safelisted classes verified);
- `manage.py check`;
- `manage.py makemigrations --check --dry-run`;
- `manage.py collectstatic --dry-run --noinput`;
- HTTP 200 for home, catalog, product detail, cart, login, registration,
  authenticated checkout, authenticated account and admin;
- confirmed that storefront/auth HTML loads no Tailwind CDN or coexistence CSS.

The final visual matrix was accepted manually before CDN removal.

## Manual comparison checklist

Compare at desktop and mobile widths:

- home: hero gradient, product cards, popup, navigation hover, mobile menu;
- catalog: filters, responsive product grid, pagination;
- product detail: thumbnails, selected size, image controls, zoom, sticky CTA;
- cart: quantity controls, messages, summary, empty state;
- checkout: step indicators, shipping/payment selection, inputs and focus;
- login and registration: logo scale, glass card, fields, focus and buttons;
- account: cards, hover lift/shadow, profile forms;
- Alpine states: dropdowns, notifications, FAQ, popup and WhatsApp widget;
- admin: smoke-check only, because it does not load storefront Tailwind.

Pay special attention to typography, line wrapping, borders, placeholder
colors, shadows, gradients, transforms, hover/focus states and breakpoints.

## Cleanup deferred

The unused `static/css/tailwind.generated.css` coexistence artifact and the
historical `dist/` build were intentionally left in place. Their removal should
be handled by a separate evidence-backed cleanup.
