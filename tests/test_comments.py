from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from social_app.models import Post, Commentary
from social_app.serializers import (
    CommentSerializer,
    CommentListSerializer,
)

COMMENT_URL = reverse("social_app:commentary-list")


def detail_post_url(post_id):
    return reverse("social_app:post-detail", args=[post_id])


def comment_url(comment_id):
    return reverse("social_app:commentary-detail", args=[comment_id])


class UnauthorizedUserCommentViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_comment_list(self):
        result = self.client.get(COMMENT_URL)
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthorizedUserCommentViewSetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        post_owner = get_user_model().objects.create_user(
            email="post_owner@email.com", password="password"
        )
        comment_owner = get_user_model().objects.create_user(
            email="user_2@email.com", password="password"
        )
        get_user_model().objects.create_user(
            email="user_3@email.com", password="password"
        )
        post = Post.objects.create(
            owner=post_owner,
            title="Sample post 1",
            hashtag="test hashtag 1",
            content="Sample content",
            created_at="2023-05-10",
        )
        Commentary.objects.create(
            user=comment_owner, post=post, content="Comment content"
        )

    def setUp(self):
        self.client = APIClient()
        user_3 = get_user_model().objects.get(pk=3)
        self.client.force_authenticate(user_3)

    def test_comment_list(self):
        result = self.client.get(COMMENT_URL)
        post = Post.objects.get(pk=1)
        comments = Commentary.objects.filter(post=post.id)
        serializer = CommentListSerializer(comments, many=True)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)
        self.assertEqual(comments.count(), 1)

    def test_retrieve_comment(self):
        comment = Commentary.objects.get(id=1)
        url = comment_url(comment.id)
        result = self.client.get(url)
        serializer = CommentSerializer(comment)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)

    def test_create_comment(self):
        post = Post.objects.get(pk=1)
        user_2 = get_user_model().objects.get(pk=2)
        url = detail_post_url(post.id)
        result = self.client.post(
            f"{url}comment/", {"user": user_2.id, "content": "commentary text"}
        )

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)

    def test_update_comment_if_owner(self):
        comment_owner = get_user_model().objects.get(pk=2)
        self.client.force_authenticate(comment_owner)
        comment = Commentary.objects.get(pk=1)
        url = comment_url(comment.id)
        result = self.client.put(
            url, {"user": comment_owner.id, "content": "updated text"}
        )

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertNotEqual(result.data["content"], comment.content)

    def test_update_comment_if_not_owner(self):
        comment = Commentary.objects.get(pk=1)
        url = comment_url(comment.id)
        result = self.client.put(url)

        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_comment_if_owner(self):
        comment_owner = get_user_model().objects.get(pk=2)
        self.client.force_authenticate(comment_owner)
        comment = Commentary.objects.get(pk=1)
        url = comment_url(comment.id)
        result = self.client.delete(url)

        self.assertEqual(result.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_comment_if_not_owner(self):
        comment = Commentary.objects.get(pk=1)
        url = comment_url(comment.id)
        result = self.client.delete(url)

        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)
