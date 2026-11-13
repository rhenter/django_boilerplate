from django.db import models
from django.utils.translation import gettext_lazy as _


class Language(models.TextChoices):
    ENGLISH = "en", _("English")
    PORTUGUESE_BRAZIL = "pt-br", _("Portuguese (Brazil)")
    SPANISH = "es", _("Spanish")


DEFAULT_LANGUAGE_LIST = Language.choices


class ContactType(models.TextChoices):
    DEMONSTRATION = "demonstration", _("Demonstration")
    PLANS = "plans", _("Plan questions")
    QUOTE = "quote", _("Quote")
    CUSTOM_PLAN_QUOTE = "custom_plan_quote", _("Custom plan proposal")
    ADDON_QUOTE = "addon_quote", _("Additional service request")
    OTHER = "other", _("Other")


class UF(models.TextChoices):
    AC = "AC", "AC"
    AL = "AL", "AL"
    AP = "AP", "AP"
    AM = "AM", "AM"
    BA = "BA", "BA"
    CE = "CE", "CE"
    DF = "DF", "DF"
    ES = "ES", "ES"
    GO = "GO", "GO"
    MA = "MA", "MA"
    MT = "MT", "MT"
    MS = "MS", "MS"
    MG = "MG", "MG"
    PA = "PA", "PA"
    PB = "PB", "PB"
    PR = "PR", "PR"
    PE = "PE", "PE"
    PI = "PI", "PI"
    RJ = "RJ", "RJ"
    RN = "RN", "RN"
    RS = "RS", "RS"
    RO = "RO", "RO"
    RR = "RR", "RR"
    SC = "SC", "SC"
    SP = "SP", "SP"
    SE = "SE", "SE"
    TO = "TO", "TO"


UF_CHOICES = UF.choices
