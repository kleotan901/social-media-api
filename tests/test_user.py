import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from user.serializers import UserSerializer, UserListSerializer

USER_PROFILES_URL = reverse("user:user-list")
MY_PROFILE_URL = reverse("user:manage")


def detail_url(user_id):
    return reverse("user:user-detail", args=[user_id])


class UnauthorizedUserUserViewSetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = get_user_model().objects.create_user(
            email="user@email.com", password="password"
        )

    def setUp(self):
        self.client = APIClient()

    def test_user_profiles(self):
        result = self.client.get(USER_PROFILES_URL)
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_user_profile(self):
        url = detail_url(1)
        result = self.client.get(url)

        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthorizedUserUserViewSetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        get_user_model().objects.create_user(
            pk=1, email="test@email.com", password="password"
        )
        get_user_model().objects.create_user(
            pk=2,
            email="user_2@email.com",
            password="password",
            first_name="John",
            last_name="Smith",
        )

    def setUp(self):
        self.client = APIClient()
        user = get_user_model().objects.get(pk=1)
        self.client.force_authenticate(user)

    def test_user_profile_list(self):
        user_profiles = get_user_model().objects.all()
        result = self.client.get(USER_PROFILES_URL)

        serializer = UserListSerializer(user_profiles, many=True)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)

    def test_retrieve_user_profile(self):
        user_profile_2 = get_user_model().objects.get(pk=2)
        url = detail_url(user_profile_2.id)
        result = self.client.get(url)

        serializer = UserSerializer(user_profile_2)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)

    def test_update_my_profile(self):
        user = get_user_model().objects.get(pk=1)
        url = detail_url(user.id)
        payload = {
            "email": "test@email.com",
            "password": "new password",
            "first_name": "John",
            "last_name": "Smith",
        }

        result = self.client.put(url, payload)
        serializer = UserSerializer(user, data=payload)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data["email"], serializer.data["email"])
        self.assertNotEqual(result.data["first_name"], serializer.data["first_name"])
        self.assertNotEqual(result.data["last_name"], serializer.data["last_name"])

    def test_image_url_is_shown_on_user_detail(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(MY_PROFILE_URL, {"picture": ntf}, format="multipart")
        result = self.client.get(MY_PROFILE_URL)

        self.assertIn("picture", result.data)

    def test_image_url_is_shown_on_user_list(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(USER_PROFILES_URL, {"picture": ntf}, format="multipart")
        res = self.client.get(USER_PROFILES_URL)

        self.assertIn("picture", res.data[0].keys())

    def test_retrieve_my_profile(self):
        user_profile_1 = get_user_model().objects.get(pk=1)
        result = self.client.get(MY_PROFILE_URL)

        serializer = UserSerializer(user_profile_1)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)

    def test_users_filtered_by_email(self):
        user_1 = get_user_model().objects.get(pk=1)
        user_2 = get_user_model().objects.get(pk=2)
        result = self.client.get(USER_PROFILES_URL, {"email": "user_2@email.com"})

        serializer_1 = UserListSerializer(user_1)
        serializer_2 = UserListSerializer(user_2)

        self.assertNotIn(serializer_1.data, result.data)
        self.assertIn(serializer_2.data, result.data)

    def test_users_filtered_by_first_name(self):
        user_1 = get_user_model().objects.get(pk=1)
        user_2 = get_user_model().objects.get(pk=2)
        result = self.client.get(USER_PROFILES_URL, {"first_name": "John"})

        serializer_1 = UserListSerializer(user_1)
        serializer_2 = UserListSerializer(user_2)

        self.assertNotIn(serializer_1.data, result.data)
        self.assertIn(serializer_2.data, result.data)

    def test_users_filtered_by_last_name(self):
        user_1 = get_user_model().objects.get(pk=1)
        user_2 = get_user_model().objects.get(pk=2)
        result = self.client.get(USER_PROFILES_URL, {"last_name": "Sm"})

        serializer_1 = UserListSerializer(user_1)
        serializer_2 = UserListSerializer(user_2)

        self.assertNotIn(serializer_1.data, result.data)
        self.assertIn(serializer_2.data, result.data)

    def test_follow(self):
        user_1 = get_user_model().objects.get(pk=1)
        user_2 = get_user_model().objects.get(pk=2)
        url = reverse("user:follow", args=[user_2.id])
        result = self.client.post(url, {"following": user_1.id})

        serializer = UserSerializer(user_2)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertIn(user_1.email, serializer.data["followers"])
        self.assertEqual(result.data["message"], "now you are following")

    def test_unfollow(self):
        user_1 = get_user_model().objects.get(pk=1)
        user_2 = get_user_model().objects.get(pk=2)

        user_2.followers.add(user_1)

        url = reverse("user:unfollow", args=[user_2.id])
        result = self.client.post(url, {"following": user_1.id})

        serializer = UserSerializer(user_2)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertNotIn(user_1.email, serializer.data["followers"])
        self.assertEqual(
            result.data["message"], "You are no longer following this user"
        )
