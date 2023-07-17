from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
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

    def get_queryset(self):
        """Retrieve the posts with filters by hashtag, created_at, title, owner"""
        hashtag = self.request.query_params.get("hashtag")
        created_at = self.request.query_params.get("created_at")
        title = self.request.query_params.get("title")
        owner = self.request.query_params.get("owner")
        queryset = self.queryset
        if hashtag:
            queryset = queryset.filter(hashtag__icontains=hashtag)
        if created_at:
            queryset = queryset.filter(created_at__icontains=created_at)
        if title:
            queryset = queryset.filter(title__icontains=title)
        if owner:
            queryset = queryset.filter(owner__icontains=owner)

        return queryset


class MyPostView(viewsets.ViewSet):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def my_posts(self, request):
        posts_owner = request.user.id
        posts = Post.objects.filter(owner_id=posts_owner)
        if posts.exists():
            serializer = self.serializer_class(posts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"message": "No posts"}, status=status.HTTP_200_OK)

    def followings_posts(self, request):
        """ Retrieve posts of users they are following """
        own_profile = get_user_model().objects.get(pk=request.user.id)
        followings = own_profile.following.all()
        for user in followings:
            if user.posts.exists():
                serializer = self.serializer_class(user.posts, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"message": "No posts"}, status=status.HTTP_200_OK)
