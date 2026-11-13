from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views.http_status import page_not_found, unauthorized_access

from . import views
from .views.contact import AdminContactRequestViewSet

app_name = 'core'

router = DefaultRouter()

router.register(r'terms-of-service', views.TermsOfServiceViewSet, basename='terms-of-service')
router.register(r'privacy-policy', views.PrivacyPolicyViewSet, basename='privacy-policy')

urlpatterns = [
    path("public/", include("apps.core.public_urls")),
    path("admin/contact/", AdminContactRequestViewSet.as_view({"get": "list"}), name="admin-contact-list"),
    path("admin/contact/<uuid:pk>/", AdminContactRequestViewSet.as_view({"get": "retrieve", "delete": "destroy"}), name="admin-contact-detail"),

    # Error Pages
    path('401/', unauthorized_access, name='unauthorized_access'),
    path('404/', page_not_found, name='page_not_found'),
]

urlpatterns += router.urls
