from rest_framework import serializers

from social_app.models import Post, Commentary


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commentary
        fields = ("id", "created_time", "content")


class CommentListSerializer(CommentSerializer):
    class Meta:
        model = Commentary
        fields = ("id", "user", "created_time", "content")


class PostSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(
        slug_field="email", read_only=True
    )
    liked_by = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="email"
    )

    class Meta:
        model = Post
        fields = (
            "id",
            "owner",
            "title",
            "hashtag",
            "content",
            "image",
            "created_at",
            "liked_by",
        )


class PostDetailSerializer(PostSerializer):
    owner = serializers.SlugRelatedField(slug_field="email", read_only=True)
    liked_by = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="email"
    )
    commentaries = CommentListSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "owner",
            "title",
            "hashtag",
            "content",
            "image",
            "created_at",
            "liked_by",
            "commentaries",
        )
