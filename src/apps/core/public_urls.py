from django.urls import path

from .views.contact import PublicContactViewSet, ToggleContactReadView


urlpatterns = [
    path("contact", PublicContactViewSet.as_view({"post": "create"}), name="public-contact"),
    path(
        "contact/<uuid:pk>/toggle-read",
        ToggleContactReadView.as_view(),
        name="public-contact-toggle-read",
    ),
]
