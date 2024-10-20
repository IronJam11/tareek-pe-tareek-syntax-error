from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from usersapp.models import User, UserDetails
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from usersapp.serializers import UserSerializer

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password')

        # Authenticate the user
        user = User.objects.filter(email=email).first()
        if user is None:
            raise AuthenticationFailed("User not found")
        if not user.check_password(password):
            raise AuthenticationFailed("Incorrect password!")

        if user is not None :
            # Record login time in UserActivity

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh-token': str(refresh),
                'access-token': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid enrollmentNo or password'}, status=status.HTTP_401_UNAUTHORIZED)
        




from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract the refresh token from the request body
        refresh_token = request.data.get('refresh_token')

        print("refresh token", refresh_token)  # Debugging

        # Validate the refresh token presence
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Blacklist the refresh token using Simple JWT
            refresh = RefreshToken(refresh_token)
            # Call the blacklist method to mark the token as blacklisted
            refresh.blacklist()

            return Response({'message': 'Logged out successfully'}, status=status.HTTP_205_RESET_CONTENT)

        except Exception as e:
            print("Error occurred during token blacklisting:", str(e))
            return Response({'error': 'Invalid or expired refresh token', 'details': str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class Register(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)
    
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view

@api_view(['DELETE'])
def delete_user(request, username):
    try:
        # Fetch the user by username
        user = get_object_or_404(User, username=username)
        
        # Delete the user
        user.delete()
        
        return Response({"message": f"User {username} deleted successfully!"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
 # educational level, income level, 