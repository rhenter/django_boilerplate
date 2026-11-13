from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.contenttypes.models import ContentType

from .models import SMTPSettings, PrivacyPolicy, TermsOfService, AuditLogEntry, ContactRequest

admin.site.site_header = f'{settings.APP_NAME} Admin'
admin.site.site_title = settings.APP_NAME
admin.site.enable_nav_sidebar = False



class LegalDocumentAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return ("version", "text", "published_at") if obj else ("published_at",)


@admin.register(TermsOfService)
class TermsOfServiceAdmin(LegalDocumentAdmin):
    model = TermsOfService
    list_display = [
        'code',
        'version',
    ]
    exclude = ['code']


@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(LegalDocumentAdmin):
    model = PrivacyPolicy
    list_display = [
        'code',
        'version',
    ]
    exclude = ['code']


class EmailSettingsForm(forms.ModelForm):
    class Meta:
        model = SMTPSettings
        fields = '__all__'

    def clean_brevo_api_key(self):
        return self.cleaned_data.get('brevo_api_key') or self.instance.brevo_api_key

    def clean(self):
        data = super().clean()
        if data.get('transport') == 'brevo_api' and not data.get('brevo_api_key'):
            self.add_error('brevo_api_key', 'Informe a chave de API da Brevo.')
        if data.get('transport') == 'brevo_api':
            data['port'] = data.get('port') or 587
            data['timeout'] = data.get('timeout') or 15
        return data


@admin.register(SMTPSettings)
class SMTPSettingsAdmin(admin.ModelAdmin):
    form = EmailSettingsForm
    model = SMTPSettings
    list_display = [
        'transport',
        'host',
        'port',
        'username',
        'timeout',
        'use_tls',
        'use_ssl',
        'is_active',
    ]
    exclude = ['code']

    def has_add_permission(self, *args, **kwargs):
        return not SMTPSettings.objects.exists()


class OrderedContentTypeFilter(SimpleListFilter):
    title = 'content type'
    parameter_name = 'content_type'

    def lookups(self, request, model_admin):
        """Return a list of tuples for the filter options, ordered alphabetically by model name"""
        # Get all content types that are referenced in LogEntry
        exclude_models = [
            'adminlogentry',
            'contenttype',
            'session',
            'permission'
        ]

        content_types = ContentType.objects.filter(
            logentry__isnull=False
        ).distinct().order_by('app_label', 'model')

        return [(ct.id, f"{ct.app_label} | {ct.model}") for ct in content_types]

    def queryset(self, request, queryset):
        """Filter the queryset based on the selected content type"""
        if self.value():
            return queryset.filter(content_type=self.value())
        return queryset


@admin.register(AuditLogEntry)
class AuditLogEntryAdmin(admin.ModelAdmin):
    model = AuditLogEntry
    list_display = [
        'action_time',
        'user',
        'content_type',
        'object_repr',
        'action_flag',
        'change_message',
    ]
    list_filter = [
        'action_flag',
        'action_time',
        OrderedContentTypeFilter,
        'user'
    ]
    search_fields = [
        'object_repr',
        'change_message'
    ]
    readonly_fields = [
        'action_time',
        'user',
        'content_type',
        'object_id',
        'object_repr',
        'action_flag',
        'change_message'
    ]
    date_hierarchy = 'action_time'
    ordering = ['-action_time']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "subject", "contact_type", "source", "status", "is_read", "read_by", "read_at", "created_at")
    list_filter = ("status", "is_read")
    search_fields = ("name", "email", "phone", "subject", "contact_type", "message")
    readonly_fields = (
        "code", "created_at", "updated_at", "source", "page_url", "referrer", "user_agent", "ip_address",
        # "is_read", "read_at", "read_by",
    )

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if request.method == "GET":
            contact = self.get_object(request, object_id)
            if contact and not contact.is_read:
                contact.is_read = True
                contact.read_by = request.user
                contact.save(update_fields=("is_read", "read_at", "read_by", "updated_at"))
        return super().change_view(request, object_id, form_url, extra_context)
