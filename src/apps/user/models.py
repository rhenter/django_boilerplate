from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django_models.models import SignalsModel
from django_models.utils import remove_special_characters

from apps.core.constants import Language
from apps.core.models import BaseModel
from .managers import UserSignalsManager
from .utils import register_user_with_onesignal


class User(SignalsModel, AbstractUser):
    cellphone = models.CharField(max_length=20, blank=True, verbose_name=_("Cellphone"))
    must_change_password = models.BooleanField(default=False, verbose_name=_("Must change password"))

    # Notifications
    allow_delivery_notifications = models.BooleanField(
        default=True, verbose_name=_("Allow Delivery Notifications")
    )
    allow_email_notifications = models.BooleanField(default=True, verbose_name=_("Allow Email Notifications"))
    allow_push_notifications = models.BooleanField(default=True, verbose_name=_("Allow Push Notifications"))
    allow_sms_notifications = models.BooleanField(default=True, verbose_name=_("Allow SMS Notifications"))
    allow_whatsapp_notifications = models.BooleanField(default=True, verbose_name=_("Allow WhatsApp Notifications"))

    preferred_language = models.CharField(
        max_length=10,
        blank=True,
        default=Language.PORTUGUESE_BRAZIL,
        choices=Language.choices,
        verbose_name=_('Preferred Language')
    )

    onesignal_id = models.UUIDField(blank=True, null=True, verbose_name=_("OneSignal ID"))
    objects = UserSignalsManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def save(self, *args, **kwargs):
        if self.pk and not self.is_active:
            # Protect platform availability even through Django's user administration.
            from apps.platform_access.models import PlatformMembership, PlatformSession, ensure_other_administrator, lock_access
            from django.utils import timezone
            with transaction.atomic():
                lock_access()
                if PlatformMembership.objects.filter(user_id=self.pk, role='administrator', is_active=True).exists():
                    ensure_other_administrator(self.pk)
                PlatformSession.objects.filter(membership__user_id=self.pk, revoked_at__isnull=True).update(revoked_at=timezone.now())
                return super().save(*args, **kwargs)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name() or self.username

    def _clean_phone(self, value):
        number = remove_special_characters(value.replace(' ', ''))

        if number.startswith('0'):
            number = number[1:]
        return number

    def _register_with_onesignal(self):
        """Register this user with OneSignal for push notifications"""
        result = register_user_with_onesignal(self)
        # Return the raw result for backward compatibility
        return result['result'] if result['success'] else None

    def pre_save(self, save_kwargs):
        self.cellphone = self._clean_phone(self.cellphone)
        self.allow_push_notifications = True


class AccessToken(models.Model):
    """Single-use token used by public access flows.

    Only the digest is persisted; the value sent to the client is never stored.
    """

    PURPOSE_PASSWORD_RESET = "password_reset"
    PURPOSES = ((PURPOSE_PASSWORD_RESET, _("Password reset")),)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="access_tokens")
    purpose = models.CharField(max_length=32, choices=PURPOSES)
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    expires_at = models.DateTimeField(db_index=True)
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=("user", "purpose", "expires_at"))]


class AuditEvent(BaseModel):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_("Actor"))
    account = models.ForeignKey("accounts.Account", null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_events", verbose_name=_("Account"))
    command = models.CharField(max_length=100, verbose_name=_("Command"))
    object_type = models.CharField(max_length=100, blank=True, verbose_name=_("Object type"))
    object_id = models.CharField(max_length=64, blank=True, verbose_name=_("Object ID"))
    before = models.JSONField(null=True, blank=True, verbose_name=_("Before"))
    after = models.JSONField(null=True, blank=True, verbose_name=_("After"))
    reason = models.TextField(blank=True, verbose_name=_("Reason"))
    request_id = models.CharField(max_length=100, blank=True, verbose_name=_("Request ID"))
    correlation_id = models.CharField(max_length=100, blank=True, verbose_name=_("Correlation ID"))

    class Meta:
        verbose_name = _("Audit event")
        verbose_name_plural = _("Audit events")

    def __str__(self):
        return f"{self.command} / {self.object_type} / {self.object_id}"

    def save(self, *args, **kwargs):
        from apps.core.audit_context import current_audit_context, sanitize_snapshot
        context = current_audit_context()
        self.request_id = self.request_id or context.get("request_id", "")
        self.correlation_id = self.correlation_id or context.get("correlation_id", "")
        self.before = sanitize_snapshot(self.before)
        self.after = sanitize_snapshot(self.after)
        return super().save(*args, **kwargs)
