@echo off
rem Local preview launcher only — overrides .env so runserver serves static
rem files (DEBUG) and does not 301 http->https. Never used in production.
cd /d "%~dp0.."
set "DEBUG=True"
set "SECURE_SSL_REDIRECT=False"
python manage.py runserver 127.0.0.1:8001
