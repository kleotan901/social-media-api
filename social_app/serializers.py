from rest_framework import serializers

from social_app.models import Post


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
            "liked_by"
        )
