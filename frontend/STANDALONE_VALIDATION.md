# Standalone Tailwind v4 validation

## Modes

Run Django normally, then select a mode in the browser:

- baseline: `http://127.0.0.1:8000/?tailwind=current`
- candidate: `http://127.0.0.1:8000/?tailwind=standalone`
- reset: `http://127.0.0.1:8000/?tailwind=reset`

The selected mode follows normal navigation through a DEBUG-only cookie. Check
the `<html data-tailwind-mode="...">` attribute if the active mode is unclear.

The baseline loads, in order:

1. `tailwind.generated.css`;
2. Tailwind CDN and its inline compatibility configuration;
3. `output.css`;
4. `premium.css`.

The standalone storefront loads:

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
- confirmed that standalone HTML loads no Tailwind CDN or coexistence CSS;
- confirmed that current mode still loads both the coexistence CSS and CDN.

The visual matrix was intentionally left for manual testing.

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

## Decision gate

Current recommendation: do not remove the CDN yet. Accept the manual matrix
above first. If a difference is found, record the page, viewport, element,
baseline behavior and standalone behavior before changing CSS.
