# Tailwind v4 visual validation

Validation performed on June 19, 2026 with Chromium at:

- desktop: 1440 × 900;
- mobile: 390 × 844.

Each page was captured twice: once with `tailwind.generated.css` blocked
(current CDN baseline), then with the local candidate enabled. Animations were
disabled for deterministic screenshots.

## Pages and states checked

- home, including desktop navigation hover and the mobile menu;
- catalog;
- product detail, including a selected size;
- cart with an item;
- checkout;
- login, including input focus;
- registration;
- authenticated customer dashboard;
- authenticated Django admin.

All pages returned HTTP 200 and all requested local static/media assets returned
HTTP 200.

## Confirmed incompatibility and fix

Loading an unmodified Tailwind v4 build beside the v3 CDN changed hero gradients
on home and catalog. Tailwind v4 registers internal gradient variables with
typed CSS `@property` rules, while the CDN emits legacy values that those types
reject.

It also doubled some authentication and hover transforms because v4 emits
individual `scale`/`translate`/`rotate` properties while v3 emits a composed
`transform`.

The parity workflow therefore removes the generated `@property` registrations
and individual transform declarations while both versions coexist. With that
compatibility step:

- home/catalog heroes are pixel-identical to the CDN baseline;
- product, cart, checkout, hover, focus and dynamic Alpine states are
  pixel-identical;
- authentication/account transform differences were traced to the individual
  v4 transform properties and removed from the coexistence build;
- admin is unchanged and does not load the storefront candidate stylesheet.

The full browser matrix was completed after removing `@property` registrations.
The final repeat after also removing individual transform declarations could
not be launched because the browser execution quota was reached. The production
build and a generated-CSS inspection confirm that no `@property` registration
or individual `scale`/`translate`/`rotate` declaration remains; a fresh browser
matrix is still required before treating visual parity as final.

One repeat comparison showed movement only in the animated WhatsApp button on
the mobile selected-product capture. The same variation occurred when comparing
two identical candidate runs, so it is animation/capture noise rather than a
CSS difference.

## Safelist

No new safelist entries were required during this validation. Existing Alpine
and Django conditional classes were present in the generated output.

## CDN removal gate

Not ready to remove the CDN yet. Before removal:

1. stop stripping Tailwind's native `@property` output;
2. test the standalone v4 build with the CDN blocked;
3. resolve any genuine v3-to-v4 gradient/reset differences in source CSS;
4. repeat desktop/mobile screenshots and interactive-state checks;
5. update CSP and remove the inline CDN compatibility configurations.
