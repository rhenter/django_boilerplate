from django.utils import timezone
from django_models.utils import remove_special_characters
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.auth.jwt_tokens import JwtAuthSession
from apps.user.models import UserMetric
from apps.user.serializers import UserProfileSerializer
from django_settings.utils import is_email


class UserMetricsUpdateMixin:

    def update_user_access_metrics(self, user) -> None:
        if not user or user.is_anonymous:
            return
        today_login_metric, created = UserMetric.objects.get_or_create(
            metric='LI',
            metric_date=timezone.localdate(),
        )
        today_login_metric.user.add(user)
        today_login_metric.save()


class UserLoginDRFTokenView(ObtainAuthToken):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data.copy()

        username = data['username'].strip().replace(' ', '')
        if not is_email(username):
            username = remove_special_characters(username)
        data['username'] = username

        serializer = self.serializer_class(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        data = {
            'token': token.key,
            'user': UserProfileSerializer(user).data,
        }
        user.last_login = timezone.now()
        user.save()
        return Response(data)


class UserSetSessionTokenView(UserMetricsUpdateMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        authenticator = JwtAuthSession(request.data)
        data = authenticator.set_session()
        user = authenticator.get_user()
        # TODO: Please only re-enable it this code bellow once the frontend handles HTTP `403 Forbidden`
        #  responses by redirecting the user to the login page when their session has expired.
        # auth_login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
        self.update_user_access_metrics(user)
        return Response(data)
