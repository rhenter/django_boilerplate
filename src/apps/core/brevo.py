"""Django mail transport using Brevo's transactional HTTPS API."""
import base64
import uuid
from email.mime.base import MIMEBase
from email.utils import parseaddr

import requests
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend


def _address(value):
    name, email = parseaddr(value)
    return {"email": email, **({"name": name} if name else {})}


class BrevoEmailBackend(BaseEmailBackend):
    def __init__(self, *, api_key, timeout=15, **kwargs):
        super().__init__(**kwargs)
        if not api_key:
            raise ImproperlyConfigured("The Brevo HTTPS transport requires an API key.")
        self.api_key = api_key
        self.timeout = timeout or 15

    def _payload(self, message):
        # Run Django's address and header validation before any network request.
        message.message()
        payload = {
            "sender": _address(message.from_email), "subject": message.subject,
            "headers": {"IdempotencyKey": message.extra_headers.setdefault("IdempotencyKey", str(uuid.uuid4()))},
        }
        for field in ("to", "cc", "bcc"):
            addresses = getattr(message, field, None)
            if addresses:
                payload[field] = [_address(value) for value in addresses]
        if message.reply_to:
            payload["replyTo"] = _address(message.reply_to[0])
        payload["htmlContent" if message.content_subtype == "html" else "textContent"] = message.body
        for alternative in getattr(message, "alternatives", ()):
            if alternative.mimetype == "text/html":
                payload["htmlContent"] = alternative.content
        attachments = []
        for attachment in message.attachments:
            if isinstance(attachment, MIMEBase):
                name = attachment.get_filename() or (attachment.get("Content-ID") or "attachment").strip("<>")
                content = attachment.get_payload(decode=True)
            else:
                name, content, mimetype = attachment
            if isinstance(content, str):
                content = content.encode(message.encoding or "utf-8")
            attachments.append({"name": name, "content": base64.b64encode(content).decode("ascii")})
        if attachments:
            payload["attachment"] = attachments
        return payload

    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages or ():
            if not message.recipients():
                continue
            try:
                response = requests.post(
                    "https://api.brevo.com/v3/smtp/email", json=self._payload(message),
                    headers={"api-key": self.api_key, "accept": "application/json"},
                    timeout=self.timeout,
                )
                try:
                    data = response.json()
                except ValueError:
                    data = {}
                if not isinstance(data, dict):
                    data = {}
                duplicate = (response.status_code == 400 and data.get("code") == "duplicate_parameter"
                             and "idempoten" in str(data.get("message", "")).lower())
                if not duplicate and (response.status_code != 201 or not data.get("messageId")):
                    raise RuntimeError(f"Brevo rejected the email request (HTTP {response.status_code}).")
                message.provider_message_id = data.get("messageId", "")
                sent += 1
            except requests.RequestException:
                if not self.fail_silently:
                    raise RuntimeError("Brevo email request failed; delivery requires reconciliation or retry.") from None
            except Exception:
                if not self.fail_silently:
                    raise
        return sent
