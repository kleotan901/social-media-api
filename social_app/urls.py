from django.urls import path, include
from rest_framework import routers

from social_app.views import PostViewSet

app_name = "social_app"
router = routers.DefaultRouter()
router.register("posts", PostViewSet)


urlpatterns = [
    path("", include(router.urls)),
]
