# Frontend asset audit

Audit completed after the Tailwind v4 local migration.

## Final Tailwind migration state

The active Tailwind CDN and temporary current/standalone switch are gone.
`frontend/tailwind.css` is the only Tailwind source and
`static/css/tailwind.css` is its generated deployable output.

Removed migration-only files:

- `static/css/tailwind.generated.css`: filtered CDN-coexistence build;
- `static/css/tailwind.standalone.css`: temporary candidate name, replaced by
  `static/css/tailwind.css`;
- `frontend/VISUAL_VALIDATION.md` and
  `frontend/STANDALONE_VALIDATION.md`: temporary validation reports whose
  lasting conclusions are consolidated here and in `frontend/README.md`.

## Active static files

- `static/css/tailwind.css`: loaded by storefront and authentication bases.
- `static/css/output.css`: loaded after Tailwind by `templates/base.html`.
- `static/css/premium.css`: loaded after `output.css`; its principal component
  selectors are used by active storefront, account, cart, checkout, catalog,
  login, and registration templates.
- `static/assets/images/logo.png`: storefront header/footer, auth, popup,
  WhatsApp UI, and Django Unfold admin logo/icon.
- `static/assets/images/background1.jpg`: home/page heroes, auth background,
  and product-image fallback.
- `favicon.ico`, `favicon-16x16.png`, `favicon-32x32.png`, and
  `apple-touch-icon.png`: referenced by base templates.

## Retained probable orphans

The following are not referenced by active Django templates, Python settings,
or the current Node scripts:

- `static/css/input.css`: legacy Tailwind v3 `@tailwind` source;
- `static/styles/variables.css`, `components.css`, `layout.css`,
  `responsive.css`, and `animations.css`: an older non-Tailwind design system;
- `static/scripts/currency.js`: old DOM/localStorage currency implementation;
  the active application handles currency through Django sessions and rendered
  prices;
- `favicon-48x48.png`, `android-chrome-192x192.png`, and
  `android-chrome-512x512.png`: valid favicon assets but no manifest or direct
  reference was found;
- `tailwind.config.js`: legacy configuration reference; Tailwind v4 consumes
  theme/source declarations from `frontend/tailwind.css`.

They remain tracked because this task avoids speculative deletion. A future
cleanup may remove them after a manual deployment/browser check confirms there
are no external consumers.

## `output.css` and `premium.css`

`output.css` is still loaded, but its rules are duplicated in
`frontend/tailwind.css`. It is a strong removal candidate, not an immediate
deletion: remove its link in a separate visual parity task, rebuild, compare
storefront/forms, then delete the file if no computed-style difference remains.

`premium.css` is not redundant. It owns active semantic components that are not
expressed solely through Tailwind utilities. Keep it separate to minimize
visual risk.

## Historical `dist/` bundle

`dist/` is a complete Vite-built React 18 single-page application, independent
from Django:

- `dist/index.html`: SPA entry point with `<div id="root">`; references only
  `/assets/index-S9rk_h4Q.js`, `/assets/index-BQ4kSp1B.css`, and an old
  `/scripts/currency.js` path.
- `assets/index-S9rk_h4Q.js`: main minified runtime containing React 18,
  React Router 6, Lucide icons, shared layout, and lazy routes.
- `assets/index-BQ4kSp1B.css`: compiled SPA reset, theme variables, layout,
  cards, auth, animations, and responsive styles.
- `assets/About-*`, `Blog-*`, `Cart-*`, `Checkout-*`, `Contact-*`,
  `Dashboard-*`, `FAQ-*`, `Home-*`, `Login-*`, `NotFound404-*`,
  `ProductDetails-*`, `Register-*`, `Shop-*`, and `Wishlist-*`: lazy route
  chunks imported by the main SPA bundle.
- `assets/background1-*jpg`: Vite-hashed 5184×3456 hero image used by the SPA
  CSS. It differs from Django's optimized `static/assets/images/background1.jpg`.

No Django template, view, setting, URL, static configuration, documentation,
deployment script, or current package manifest references `dist/`. No matching
React/Vite source tree or rebuild command exists. Some SPA component strings
also point to `/assets/images/...`, while the bundle only contains the hashed
background, indicating the historical build may not be fully self-contained.

Git detail: `.gitignore` has the generic Python `dist/` rule, but every current
file under `dist/` is already tracked, so ignore rules do not remove it from
history or future commits.

Decision: keep `dist/` unchanged in this task. Recommended future process:

1. tag or archive the current commit;
2. confirm the production web server and PythonAnywhere configuration do not
   serve the repository `dist/` path;
3. optionally archive the directory outside the active application;
4. remove it from Git in a dedicated reviewed commit.

Deleting `dist/` cannot affect Django based on repository references found, but
an undocumented external server mapping remains the residual risk.

## Repository policy

- `frontend/`: version hand-authored source, safelist, checker, and docs.
- `static/`: version hand-authored assets and the compiled Tailwind file;
  never edit generated `static/css/tailwind.css` manually.
- `staticfiles/`: generated by `collectstatic`, ignored, never edited.
- `node_modules/`: generated by npm, ignored.
- `dist/`: historical tracked artifact despite ignore rules; freeze until its
  dedicated removal.

Other already tracked files that match ignore policy include `db.sqlite3`,
`logs/django.log`, `media/`, and `dist/`. This audit does not alter their
tracking because they may contain local/business data and require separate
repository-policy decisions.
