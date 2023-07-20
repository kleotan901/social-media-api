from typing import List, Type

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import Serializer, BaseSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication

from social_app.models import Post, Commentary
from social_app.permissions import IsOwnerOrIfAuthenticatedReadOnly
from social_app.serializers import (
    PostSerializer,
    PostDetailSerializer,
    CommentSerializer,
    CommentListSerializer,
)
from social_app.tasks import create_post


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsOwnerOrIfAuthenticatedReadOnly, IsAuthenticated)

    def perform_create(self, serializer: Serializer) -> None:
        owner = self.request.user
        title = serializer.validated_data["title"]
        content = serializer.validated_data["content"]
        created_at = serializer.validated_data.get("created_at", None)

        if created_at:
            create_post.apply_async(
                args=(owner.id, title, content, created_at), eta=created_at
            )

        else:
            serializer.save(owner=owner)

    def get_queryset(self) -> List[Post]:
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

    def get_serializer_class(self) -> Type[BaseSerializer]:
        if self.action == "retrieve":
            return PostDetailSerializer

        if self.action == "comment":
            return CommentSerializer

        return PostSerializer

    @action(
        methods=["PUT"],
        detail=True,
        url_path="like",
        permission_classes=(IsAuthenticated,),
    )
    def like(self, request, pk) -> Response:
        own_profile = get_user_model().objects.get(pk=request.user.id)
        post = get_object_or_404(Post, pk=pk)
        if own_profile not in post.liked_by.all():
            post.liked_by.add(own_profile)
        return Response({"message": "You like this post"}, status=status.HTTP_200_OK)

    @action(
        methods=["PUT"],
        detail=True,
        url_path="unlike",
        permission_classes=(IsAuthenticated,),
    )
    def unlike(self, request, pk) -> Response:
        own_profile = get_user_model().objects.get(pk=request.user.id)
        post = Post.objects.get(pk=pk)
        if own_profile in post.liked_by.all():
            post.liked_by.remove(own_profile)
        return Response({"message": "Marked as dislike"}, status=status.HTTP_200_OK)

    @action(
        methods=["GET", "POST"],
        detail=True,
        url_path="comment",
        serializer_class=CommentSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def comment(self, request, pk=None) -> Response:
        if self.request.method == "GET":
            post = self.get_object()
            comments = post.commentaries.all()
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)

        if self.request.method == "POST":
            post = self.get_object()
            serializer = CommentSerializer(data=request.data)
            if serializer.is_valid():
                content = serializer.data["content"]
                Commentary.objects.create(user=request.user, post=post, content=content)
                return Response(
                    {"message": "Comment added"}, status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["GET"],
        detail=False,
        url_path="my_posts",
        permission_classes=(IsAuthenticated,),
    )
    def my_posts(self, request, pk=None) -> Response:
        posts_owner = request.user.id
        posts = Post.objects.filter(owner_id=posts_owner)
        if posts.exists():
            serializer = self.serializer_class(posts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"message": "No posts"}, status=status.HTTP_200_OK)

    @action(
        methods=["GET"],
        detail=False,
        url_path="followings_posts",
        permission_classes=(IsAuthenticated,),
    )
    def followings_posts(self, request, pk=None) -> Response:
        """Retrieve posts of users to which the current user is subscribed"""
        own_profile = get_user_model().objects.get(pk=request.user.id)
        followings = own_profile.following.all()
        for user in followings:
            if user.posts.exists():
                serializer = self.serializer_class(user.posts, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"message": "No posts"}, status=status.HTTP_200_OK)

    @action(
        methods=["GET"],
        detail=False,
        url_path="my_likes",
        permission_classes=(IsAuthenticated,),
    )
    def my_likes(self, request) -> Response:
        """Posts tagged as like"""
        own_profile = get_user_model().objects.get(pk=request.user.id)
        like_post_list = own_profile.likes.all()
        if like_post_list.exists():
            serializer = self.serializer_class(like_post_list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            {"message": "No posts tagged as like"}, status=status.HTTP_200_OK
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="hashtag",
                description="Filter by hashtag (ex. ?hashtag=post)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="created_at",
                description="Filter by created date (ex. ?created_at=2023-07-20)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="title",
                description="Filter by title (ex. ?title=post)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="owner",
                description="Filter by owner (ex. ?email=email)",
                required=False,
                type=str,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(self, request, *args, **kwargs)


class CommentViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Commentary.objects.all()
    serializer_class = CommentListSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsOwnerOrIfAuthenticatedReadOnly, IsAuthenticated)

    def get_serializer_class(self) -> Type[BaseSerializer]:
        if self.action == "retrieve":
            return CommentSerializer

        return CommentListSerializer
