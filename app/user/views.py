from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from user.serializers import (
    UserSerializer,
    JWTTokenSerializer,
)
from rest_framework_simplejwt.authentication import JWTAuthentication

class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""
    serializer_class = UserSerializer


class CreateTokenView(TokenObtainPairView):
    """Create a new auth token for user."""
    serializer_class = JWTTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user