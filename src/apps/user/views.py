import logging

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from apps.core.viewsets import BaseViewSet
from .models import User
from .serializers import (
    UserBaseSerializer,
    UserCreateUpdateSerializer,
    UserDetailSerializer, UserPreferenceSerializer, ChangePasswordSerializer
)

logger = logging.getLogger(__name__)


class UserViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserCreateUpdateSerializer
    lookup_field = 'id'
    filterset_fields = ('first_name',)
    search_fields = (
        'first_name',
        'last_name',
        'email',
    )
    ordering_fields = (
        '-date_joined',
        '-name',
        'date_joined',
        'first_name',
    )
    ordering = ('-date_joined',)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        elif self.action == 'list':
            return UserBaseSerializer
        return self.serializer_class

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return queryset
        return queryset.filter(pk=user.pk)

    def get_permissions(self):
        if self.action in {"create", "destroy"}:
            return [IsAdminUser()]
        return super().get_permissions()

    @action(detail=True, methods=['patch'], serializer_class=UserPreferenceSerializer)
    def preferences(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.pk != request.user.pk and not request.user.is_staff:
            return Response({"detail": "You can only change your own preferences."}, status=403)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserDetailSerializer(instance).data)

    @action(detail=False, methods=['post'], url_path='change-password', permission_classes=[IsAuthenticated])
    def change_password(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password changed successfully."})
