from rest_framework import generics, mixins, viewsets
from rest_framework_simplejwt.authentication import JWTAuthentication

from social_app.models import Post
from social_app.permissions import IsOwnerOrIfAuthenticatedReadOnly
from social_app.serializers import PostSerializer


class PostViewSet(
    viewsets.ModelViewSet,
):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsOwnerOrIfAuthenticatedReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
