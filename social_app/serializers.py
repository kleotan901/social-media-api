from rest_framework import serializers

from social_app.models import Post


class PostSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(
        slug_field="email", read_only=True
    )
    class Meta:
        model = Post
        fields = ("id", "owner", "title", "content", "image", "created_at")
