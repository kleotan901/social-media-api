from celery import shared_task
from django.contrib.auth import get_user_model

from social_app.models import Post


@shared_task
def create_post(owner_id, title, content, created_at):
    owner = get_user_model().objects.get(id=owner_id)
    post = Post.objects.create(
        owner=owner, title=title, content=content, created_at=created_at
    )

    return post.id
