import logging

from django.conf import settings
from django.core.mail import EmailMessage


logger = logging.getLogger(__name__)


def send_admin_email(subject, body, *, reply_to=None):
    recipient = settings.EMAIL_ADMIN.strip()
    if not recipient:
        logger.warning("EMAIL_ADMIN is not configured; administrative email was skipped.")
        return

    message = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
        reply_to=[reply_to] if reply_to else None,
    )
    try:
        message.send(fail_silently=False)
    except Exception:
        logger.exception("Failed to send administrative email to %s", recipient)
