from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers import UserSerializer


class MeView(APIView):
    """
    Returns the authenticated user's profile, as resolved by
    KeycloakJWTAuthentication. The Angular frontend calls this right
    after login to get role + profile info for routing/UI decisions.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
