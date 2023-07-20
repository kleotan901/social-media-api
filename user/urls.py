from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from user.views import (
    CreateUserView,
    ManageUserView,
    LogoutView,
    UserViewSet,
    UserFollowView,
)

app_name = "user"

router = routers.DefaultRouter()
router.register("user_profiles", UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("register/", CreateUserView.as_view(), name="create"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("me/", ManageUserView.as_view(), name="manage"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("follow/<int:pk>/", UserFollowView.as_view({"post": "follow"}), name="follow"),
    path(
        "unfollow/<int:pk>/",
        UserFollowView.as_view({"post": "unfollow"}),
        name="unfollow",
    ),
]
