from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, mixins, viewsets, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from user.models import User
from user.permissions import IsUserOrIfAuthenticatedReadOnly
from user.serializers import UserSerializer, UserListSerializer


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer


class TokenView(ObtainAuthToken):
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsUserOrIfAuthenticatedReadOnly, IsAuthenticated)

    def get_serializer_class(self):
        if self.action == "list":
            return UserListSerializer
        return UserSerializer

    def get_queryset(self):
        """Retrieve the users with filters"""
        email = self.request.query_params.get("email")
        first_name = self.request.query_params.get("first_name")
        last_name = self.request.query_params.get("last_name")
        queryset = self.queryset
        if email:
            queryset = queryset.filter(email__icontains=email)
        if first_name:
            queryset = queryset.filter(first_name__icontains=first_name)
        if last_name:
            queryset = queryset.filter(last_name__icontains=last_name)
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="email",
                description="Filter by email (ex. ?email=email)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="first_name",
                description="Filter by first_name (ex. ?first_name=name)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="last_name",
                description="Filter by last_name (ex. ?last_name=name)",
                required=False,
                type=str,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(self, request, *args, **kwargs)


class LogoutView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"detail": "Logout successful"})


class UserFollowView(viewsets.ViewSet):
    queryset = get_user_model().objects.all()
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def follow(self, request, pk):
        own_profile = get_user_model().objects.get(pk=request.user.id)
        follow_profile = get_user_model().objects.get(pk=pk)
        following = own_profile.following.all()

        if own_profile != follow_profile:
            if follow_profile not in following:
                own_profile.following.add(follow_profile.id)
        return Response({"message": "now you are following"}, status=status.HTTP_200_OK)

    def unfollow(self, request, pk):
        own_profile = get_user_model().objects.get(pk=request.user.id)
        follow_profile = get_user_model().objects.get(pk=pk)
        following = own_profile.following.all()

        if own_profile != follow_profile:
            if follow_profile in following:
                own_profile.following.remove(follow_profile.id)

        return Response(
            {"message": "You are no longer following this user"},
            status=status.HTTP_200_OK,
        )
