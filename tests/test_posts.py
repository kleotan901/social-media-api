import datetime
import tempfile
from unittest.mock import patch

import pytz
from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from social_app.models import Post
from social_app.serializers import (
    PostSerializer,
    PostDetailSerializer,
)

POST_URL = reverse("social_app:post-list")
FOLLOWING_POSTS_URL = f"{POST_URL}followings_posts/"


def detail_url(post_id):
    return reverse("social_app:post-detail", args=[post_id])


class UnauthorizedUserPostViewSetTest(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            email="user@email.com", password="password"
        )
        Post.objects.create(
            pk=1,
            owner=user,
            title="Sample post 1",
            hashtag="test hashtag 1",
            content="Sample content",
            created_at="2023-05-10",
        )
        self.client = APIClient()

    def test_post_list(self):
        result = self.client.get(POST_URL)
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_post(self):
        url = detail_url(1)
        result = self.client.get(url)

        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthorizedUserPostViewSetTest(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            pk=1, email="user@email.com", password="password"
        )
        user_2 = get_user_model().objects.create_user(
            pk=2, email="user_2@email.com", password="password"
        )
        Post.objects.create(
            pk=1,
            owner=user,
            title="Sample post 1",
            hashtag="test hashtag 1",
            content="Sample content",
            created_at="2023-05-10",
        )
        Post.objects.create(
            pk=2,
            owner=user,
            title="Test post 2",
            hashtag="test hashtag 2",
            content="Some text",
            created_at="2023-01-11",
        )
        Post.objects.create(
            pk=3,
            owner=user_2,
            title="Post 3",
            hashtag="test hashtag 3",
            content="Some content",
            created_at="2023-07-13",
        )
        self.client = APIClient()
        self.client.force_authenticate(user)

    def test_post_list(self):
        result = self.client.get(POST_URL)
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)
        self.assertEqual(posts.count(), 3)

    @patch("social_app.views.create_post.apply_async")
    def test_task_create_post(self, mock_apply_async):
        user = get_user_model().objects.get(pk=1)

        payload = {
            "owner": user.id,
            "title": "Test Post",
            "hashtag": "hash",
            "content": "The test post",
            "created_at": "2023-07-20",
        }
        result = self.client.post(POST_URL, payload)

        created_at_datetime = datetime.datetime.fromisoformat(payload["created_at"])
        utc_timezone = pytz.timezone("UTC")
        created_at_datetime = created_at_datetime.replace(tzinfo=utc_timezone)

        mock_apply_async.assert_called_once_with(
            args=(
                user.id,
                "Test Post",
                "The test post",
                created_at_datetime,
            ),
            eta=created_at_datetime,
        )

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)

    def test_image_url_is_shown_on_post_detail(self):
        post = Post.objects.get(id=1)
        url = detail_url(post.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        result = self.client.get(url)

        self.assertIn("image", result.data)

    def test_image_url_is_shown_on_post_list(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(POST_URL, {"image": ntf}, format="multipart")
        result = self.client.get(POST_URL)

        self.assertIn("image", result.data[0].keys())

    def test_posts_filtered_by_hashtag(self):
        test_post_1 = Post.objects.get(id=1)
        test_post_2 = Post.objects.get(id=2)
        res = self.client.get(POST_URL, {"hashtag": "hashtag 1"})

        serializer_1 = PostSerializer(test_post_1)
        serializer_2 = PostSerializer(test_post_2)

        self.assertIn(serializer_1.data, res.data)
        self.assertNotIn(serializer_2.data, res.data)

    def test_posts_filtered_by_date(self):
        test_post_1 = Post.objects.get(id=1)
        test_post_2 = Post.objects.get(id=2)
        result = self.client.get(POST_URL, {"created_at": "2023-01-11"})

        serializer_1 = PostSerializer(test_post_1)
        serializer_2 = PostSerializer(test_post_2)

        self.assertNotIn(serializer_1.data, result.data)
        self.assertIn(serializer_2.data, result.data)

    def test_posts_filtered_by_title(self):
        test_post_1 = Post.objects.get(id=1)
        test_post_2 = Post.objects.get(id=2)
        result = self.client.get(POST_URL, {"title": "test"})

        serializer_1 = PostSerializer(test_post_1)
        serializer_2 = PostSerializer(test_post_2)

        self.assertNotIn(serializer_1.data, result.data)
        self.assertIn(serializer_2.data, result.data)

    def test_posts_filtered_by_owner(self):
        test_post_1 = Post.objects.get(id=1)
        test_post_2 = Post.objects.get(id=2)
        result = self.client.get(POST_URL, {"email": "user@email"})

        serializer_1 = PostSerializer(test_post_1)
        serializer_2 = PostSerializer(test_post_2)

        self.assertIn(serializer_1.data, result.data)
        self.assertIn(serializer_2.data, result.data)

    def test_retrieve_post(self):
        post = Post.objects.get(id=3)
        url = detail_url(post.id)
        result = self.client.get(url)
        serializer = PostDetailSerializer(post)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)

    def test_update_post_if_owner(self):
        user = get_user_model().objects.get(pk=1)
        post = Post.objects.get(pk=1)
        url = detail_url(post.id)
        payload = {
            "owner": user,
            "title": "updated title",
            "content": "Sample content",
            "created_at": "2023-12-12",
        }
        result = self.client.put(url, payload)
        serializer = PostDetailSerializer(post, payload)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertNotEqual(result.data["title"], post.title)
        self.assertEqual(result.data["content"], post.content)
        self.assertNotEqual(result.data["created_at"], post.created_at)

    def test_update_post_if_not_owner(self):
        post = Post.objects.get(pk=3)
        url = detail_url(post.id)
        result = self.client.put(url)

        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_post_if_owner(self):
        post = Post.objects.get(id=1)
        url = detail_url(post.id)
        result = self.client.delete(url)

        self.assertEqual(result.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_post_if_not_owner(self):
        post = Post.objects.get(id=3)
        url = detail_url(post.id)
        result = self.client.delete(url)

        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    def test_like(self):
        post = Post.objects.get(id=3)
        user = get_user_model().objects.get(pk=1)
        url = detail_url(post.id)
        result = self.client.put(f"{url}like/", {"liked_by": user.id})

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertIn(user, post.liked_by.all())

    def test_unlike(self):
        post = Post.objects.get(id=3)
        user = get_user_model().objects.get(pk=1)
        url = detail_url(post.id)

        post.liked_by.add(user)
        result = self.client.put(f"{url}unlike/")

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertNotIn(user, post.liked_by.all())

    def test_my_posts(self):
        user = get_user_model().objects.get(pk=1)
        my_posts = Post.objects.filter(owner=user.id)
        result = self.client.get(f"{POST_URL}my_posts/")

        serializer = PostSerializer(my_posts, many=True)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, result.data)

    def test_followings_posts(self):
        user = get_user_model().objects.get(pk=1)
        following_user = get_user_model().objects.get(pk=2)
        user.following.add(following_user)
        posts_of_followings = Post.objects.filter(owner=following_user.id)
        result = self.client.get(FOLLOWING_POSTS_URL)

        serializer = PostSerializer(posts_of_followings, many=True)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, result.data)
