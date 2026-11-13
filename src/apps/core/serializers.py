import re
from urllib.parse import urlsplit, urlunsplit

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.serializers import raise_errors_on_nested_writes
from rest_framework.utils import model_meta

from .constants import ContactType
from .models import ContactRequest, PrivacyPolicy, TermsOfService


class ContactRequestSerializer(serializers.ModelSerializer):
    subject = serializers.CharField(required=False, allow_blank=False, max_length=160)
    message = serializers.CharField(required=False, allow_blank=True, max_length=5000)

    contact_type = serializers.ChoiceField(choices=ContactType.choices)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=30)

    class Meta:
        model = ContactRequest
        fields = ("name", "email", "phone", "subject", "contact_type", "message")

    def validate_phone(self, value):
        value = value.strip()
        if not value:
            return ""
        digits = re.sub(r"\D", "", value)
        if not 10 <= len(digits) <= 15:
            raise serializers.ValidationError("Enter a valid phone number with area code.")
        return value

    def validate(self, attrs):
        if self.context.get("require_phone", True) and not attrs.get("phone"):
            raise serializers.ValidationError({"phone": "This field is required."})
        if not attrs.get("subject") and attrs.get("contact_type"):
            attrs["subject"] = str(dict(ContactType.choices)[attrs["contact_type"]])
        if not attrs.get("subject"):
            raise serializers.ValidationError({"subject": "This field is required."})
        return attrs

    @staticmethod
    def _safe_url(value):
        if not value:
            return ""
        parsed = urlsplit(value.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return ""
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path[:450], "", ""))[:500]

    def create(self, validated_data):
        request = self.context["request"]
        referrer = self._safe_url(request.META.get("HTTP_REFERER", ""))
        validated_data.update({
            "source": "website_contact",
            "page_url": referrer,
            "referrer": referrer,
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:512],
            "ip_address": request.META.get("REMOTE_ADDR"),
        })
        return super().create(validated_data)


class ContactRequestAdminSerializer(serializers.ModelSerializer):
    read_by = serializers.SerializerMethodField()
    proposal = serializers.SerializerMethodField()

    def get_read_by(self, obj):
        if obj.read_by is None:
            return None
        return obj.read_by.email or obj.read_by.username

    def get_proposal(self, obj):
        proposal = getattr(obj, "proposal", None)
        if proposal is None:
            return None
        return {
            "id": str(proposal.pk),
            "proposal_type": proposal.proposal_type,
            "status": proposal.status,
            "plan": proposal.plan.name if proposal.plan_id else None,
            "additional_service": proposal.additional_service.name if proposal.additional_service_id else None,
            "account": proposal.account.name if proposal.account_id else None,
            "has_active_plan": proposal.has_active_plan,
            "delivery_volume": proposal.delivery_volume,
            "retention_months": proposal.retention_months,
            "company_count": proposal.company_count,
            "quantity": proposal.quantity,
            "currency": proposal.currency_snapshot,
            "unit_price": proposal.unit_price_snapshot,
            "monthly_price": proposal.monthly_price_snapshot,
            "total_setup_price": proposal.total_setup_price_snapshot,
            "notes": proposal.notes,
        }

    class Meta:
        model = ContactRequest
        fields = (
            "id", "name", "email", "phone", "subject", "contact_type", "message", "status", "is_read", "read_at", "read_by",
            "proposal", "source", "page_url", "referrer", "user_agent", "ip_address", "created_at", "updated_at",
        )
        read_only_fields = fields


class PublicContactResponseSerializer(serializers.Serializer):
    status = serializers.CharField()


class LegalDocumentSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        raise serializers.ValidationError("Published legal documents are immutable. Create a new version.")

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(getattr(exc, "message_dict", exc.messages)) from exc


class TermsOfServiceSerializer(LegalDocumentSerializer):
    class Meta:
        model = TermsOfService
        fields = [
            'id',
            'version',
            'text',
            'published_at',
        ]
        read_only_fields = (
            'id',
            'published_at',
        )


class PrivacyPolicySerializer(LegalDocumentSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = [
            'id',
            'version',
            'text',
            'published_at',
        ]
        read_only_fields = (
            'id',
            'published_at',
        )


class ToggleSerializer(serializers.Serializer):
    value = serializers.BooleanField()


class AuditChangesSerializer(serializers.ModelSerializer):
    fields_changed = []

    def update(self, instance, validated_data):
        raise_errors_on_nested_writes('update', self, validated_data)
        info = model_meta.get_field_info(instance)

        # Simply set each attribute on the instance, and then save it.
        # Note that unlike `.create()` we don't need to treat many-to-many
        # relationships as being a special case. During updates we already
        # have an instance pk for the relationships to be associated with.
        m2m_fields = []
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                if getattr(instance, attr) != value:
                    self.fields_changed.append(attr)
                setattr(instance, attr, value)

        instance.save()

        # Note that many-to-many fields are set after updating instance.
        # Setting m2m fields triggers signals which could potentially change
        # updated instance and we do not want it to collide with .update()
        for attr, value in m2m_fields:
            if getattr(instance, attr) != value:
                self.fields_changed.append(attr)
            field = getattr(instance, attr)
            field.set(value)

        return instance
