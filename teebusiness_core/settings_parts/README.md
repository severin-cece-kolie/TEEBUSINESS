# Django settings organization

`teebusiness_core.settings` remains the single settings module used by Django,
WSGI, ASGI, management commands, and deployment.

The standard Django configuration stays directly in `settings.py`: secret key,
debug mode, allowed hosts, installed apps, middleware, templates, database,
authentication, internationalization, static/media, security, and logging.

Only specialized configuration is split into these files:

- `base.py`: project paths, `.env` loading, and environment helpers;
- `admin.py`: Unfold and import-export;
- `communications.py`: email providers/backends and optional SMS settings;
- `project.py`: storefront, checkout, business, cache, OTP, and rate limits;

Only `base.py` reads `.env`. Other parts import its helpers and values, which
keeps environment parsing centralized and preserves the existing `.env`
contract. Keep standard Django settings in the main file and add specialized
settings to the smallest relevant part.
