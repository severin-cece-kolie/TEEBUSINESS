"""Email backends for TEEBUSINESS.

Two pieces, composed together:

* ``BrevoApiEmailBackend`` — sends through Brevo's HTTPS API (api.brevo.com).
  This is the reliable option on **PythonAnywhere free accounts**, where raw
  SMTP (Gmail/Brevo SMTP/…) is blocked but allow-listed HTTPS APIs work.

* ``LoggingEmailBackend`` — the backend Django actually uses. It wraps the real
  provider backend (console / smtp / brevo, chosen via ``EMAIL_BACKEND`` env)
  and retries on failure. It never raises on send failure → email problems can't
  cause HTTP 500. (Emails are no longer journaled to the database.)
"""
import json
import logging
import time
from email.utils import parseaddr
from urllib import error as urlerror
from urllib import request as urlrequest

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.utils import timezone
from django.utils.module_loading import import_string

logger = logging.getLogger('accounts')

BREVO_ENDPOINT = 'https://api.brevo.com/v3/smtp/email'


def _html_of(message):
    for content, mimetype in getattr(message, 'alternatives', None) or []:
        if mimetype == 'text/html':
            return content
    return None


class BrevoApiEmailBackend(BaseEmailBackend):
    """Send Django EmailMessages via the Brevo transactional email API."""

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'BREVO_API_KEY', '') or ''
        self.timeout = getattr(settings, 'EMAIL_HTTP_TIMEOUT', 20)

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        if not self.api_key:
            logger.error('BREVO_API_KEY is empty — cannot send via Brevo API.')
            if not self.fail_silently:
                raise RuntimeError('BREVO_API_KEY is not configured.')
            return 0
        sent = 0
        for message in email_messages:
            if self._send_one(message):
                sent += 1
        return sent

    def _send_one(self, message):
        name, addr = parseaddr(message.from_email or settings.DEFAULT_FROM_EMAIL)
        html = _html_of(message)
        payload = {
            'sender': {'email': addr, 'name': name or getattr(settings, 'BUSINESS_NAME', 'TEEBUSINESS')},
            'to': [{'email': e} for e in (message.to or [])],
            'subject': message.subject or '',
            'htmlContent': html or f'<pre style="font-family:inherit">{message.body or ""}</pre>',
        }
        if message.body:
            payload['textContent'] = message.body
        if getattr(message, 'reply_to', None):
            rname, raddr = parseaddr(message.reply_to[0])
            payload['replyTo'] = {'email': raddr, 'name': rname or raddr}
        if message.cc:
            payload['cc'] = [{'email': e} for e in message.cc]
        if message.bcc:
            payload['bcc'] = [{'email': e} for e in message.bcc]

        data = json.dumps(payload).encode('utf-8')
        req = urlrequest.Request(BREVO_ENDPOINT, data=data, method='POST', headers={
            'api-key': self.api_key,
            'content-type': 'application/json',
            'accept': 'application/json',
        })
        try:
            with urlrequest.urlopen(req, timeout=self.timeout) as resp:
                if 200 <= resp.status < 300:
                    return True
                raise RuntimeError(f'Brevo HTTP {resp.status}')
        except urlerror.HTTPError as exc:
            body = exc.read().decode('utf-8', 'replace')[:400] if exc.fp else ''
            raise RuntimeError(f'Brevo HTTP {exc.code}: {body}') from exc
        except Exception as exc:  # URLError, timeout, etc.
            raise RuntimeError(f'Brevo request failed: {exc}') from exc


class LoggingEmailBackend(BaseEmailBackend):
    """Wrap the real provider backend: retry on failure and never raise.

    Real backend is resolved from ``settings.EMAIL_PROVIDER_BACKEND``.
    (Email history is no longer journaled to the database.)
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        path = getattr(settings, 'EMAIL_PROVIDER_BACKEND',
                       'django.core.mail.backends.console.EmailBackend')
        # Guard against wrapping ourselves (would recurse forever).
        if path.endswith('LoggingEmailBackend'):
            path = 'django.core.mail.backends.console.EmailBackend'
        # Underlying backend always fails loudly so we can catch + retry + log.
        self.backend = import_string(path)(fail_silently=False, **kwargs)
        self.max_retries = int(getattr(settings, 'EMAIL_MAX_RETRIES', 2))

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        sent = 0
        for message in email_messages:
            ok, error = self._send_with_retry(message)
            if ok:
                sent += 1
        return sent

    def _send_with_retry(self, message):
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                if self.backend.send_messages([message]):
                    if attempt:
                        logger.info('Email to %s succeeded on retry %s', message.to, attempt)
                    return True, None
                last_error = 'backend returned 0 (no message sent)'
            except Exception as exc:
                last_error = f'{type(exc).__name__}: {exc}'
            if attempt < self.max_retries:
                time.sleep(min(1.5 * (attempt + 1), 4))  # short backoff
        logger.error('Email to %s FAILED after %s attempt(s): %s',
                     message.to, self.max_retries + 1, last_error)
        return False, last_error
