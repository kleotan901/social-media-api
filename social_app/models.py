import os
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify


def user_img_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.title)}-{uuid.uuid4()}.{extension}"
    return os.path.join("upload/users", filename)


class User(AbstractUser):
    picture = models.ImageField(null=True, upload_to=user_img_file_path)


class Post(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    title = models.CharField(max_length=255)
    content = models.TextField(max_length=1500)
    created_at = models.DateTimeField(auto_now_add=True)
    liked_by = models.ManyToManyField(User)

    def __str__(self):
        return f"{self.title} {self.owner}"


class Commentary(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="commentaries"
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="commentaries"
    )
    created_time = models.DateTimeField(auto_now=True)
    content = models.TextField(max_length=1500)

    class Meta:
        verbose_name_plural = "Commentaries"

    def __str__(self):
        return f"{self.user} {self.content}"


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
