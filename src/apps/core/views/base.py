import logging

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import SAFE_METHODS, AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import PrivacyPolicy, TermsOfService
from ..serializers import PrivacyPolicySerializer, TermsOfServiceSerializer
from ..viewsets import BaseViewSet

logger = logging.getLogger(__name__)

User = get_user_model()



class HealthCheckView(APIView):
    http_method_names = ['get']
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)


class TermsOfServiceViewSet(BaseViewSet):
    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    serializer_class = TermsOfServiceSerializer
    queryset = TermsOfService.objects.order_by('-version')


class PrivacyPolicyViewSet(BaseViewSet):
    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    serializer_class = PrivacyPolicySerializer
    queryset = PrivacyPolicy.objects.order_by('-version')
