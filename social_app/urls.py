from django.urls import path, include
from rest_framework import routers

from social_app.views import PostViewSet, MyPostView

app_name = "social_app"
router = routers.DefaultRouter()
router.register("posts", PostViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("my_posts/", MyPostView.as_view({"get": "my_posts"})),
    path("followings_posts/", MyPostView.as_view({"get": "followings_posts"})),
]
