from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.generics import CreateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
import requests
from django.utils import timezone
from django.shortcuts import redirect
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    RegisterValidateSerializer,
    AuthValidateSerializer,
    ConfirmationSerializer
)
from .models import CustomUser
from .redis_client import set_confirmation_code, get_confirmation_code, delete_confirmation_code
import random
import string


class AuthorizationAPIView(CreateAPIView):
    serializer_class = AuthValidateSerializer

    def post(self, request):
        serializer = AuthValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(**serializer.validated_data)

        if user:
            if not user.is_active:
                return Response(
                    status=status.HTTP_401_UNAUTHORIZED,
                    data={'error': 'User account is not activated yet!'}
                )

            token, _ = Token.objects.get_or_create(user=user)
            return Response(data={'key': token.key})

        return Response(
            status=status.HTTP_401_UNAUTHORIZED,
            data={'error': 'User credentials are wrong!'}
        )


class RegistrationAPIView(CreateAPIView):
    serializer_class = RegisterValidateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        with transaction.atomic():
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                phone_number=serializer.validated_data.get('phone_number', ''),
                is_active=False
            )

        code = ''.join(random.choices(string.digits, k=6))
        set_confirmation_code(user.id, code)

        return Response(
            status=status.HTTP_201_CREATED,
            data={
                'user_id': user.id,
                'confirmation_code': code
            }
        )


class ConfirmUserAPIView(CreateAPIView):
    serializer_class = ConfirmationSerializer

    def post(self, request):
        serializer = ConfirmationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data['user_id']
        input_code = serializer.validated_data['code']

        stored_code = get_confirmation_code(user_id)

        if stored_code is None:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'error': 'Код истёк или не найден'}
            )

        if stored_code != input_code:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'error': 'Неверный код подтверждения'}
            )

        with transaction.atomic():
            user = CustomUser.objects.get(id=user_id)
            user.is_active = True
            user.save()

            token, _ = Token.objects.get_or_create(user=user)

        delete_confirmation_code(user_id)

        return Response(
            status=status.HTTP_200_OK,
            data={
                'message': 'User аккаунт успешно активирован',
                'key': token.key
            }
        )
    
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class GoogleLoginRedirectAPIView(APIView):
    def get(self, request):
        google_auth_url = (
            "https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={settings.GOOGLE_CLIENT_ID}"
            f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
            "&response_type=code"
            "&scope=openid email profile"
            "&access_type=offline"
        )
        return redirect(google_auth_url)
    
class GoogleLoginCallbackAPIView(APIView):
    def get(self, request):
        code = request.GET.get('code')
        if not code:
            return Response({'error': 'Код авторизации не получен'}, status=400)

        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                'code': code,
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'redirect_uri': settings.GOOGLE_REDIRECT_URI,
                'grant_type': 'authorization_code',
            }
        )
        token_data = token_response.json()

        if 'access_token' not in token_data:
            return Response({'error': 'Не удалось получить access_token', 'details': token_data}, status=400)

        access_token = token_data['access_token']

        userinfo_response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={'Authorization': f'Bearer {access_token}'}
        )
        userinfo = userinfo_response.json()

        email = userinfo.get('email')
        given_name = userinfo.get('given_name', '')
        family_name = userinfo.get('family_name', '')

        if not email:
            return Response({'error': 'Google не вернул email'}, status=400)

        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'first_name': given_name,
                'last_name': family_name,
                'registration_source': 'google',
                'is_active': True,
            }
        )

        if not created:
            user.first_name = given_name
            user.last_name = family_name

        user.is_active = True
        user.last_login = timezone.now()
        user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'registration_source': user.registration_source,
        })