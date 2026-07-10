from django.urls import path
from users.views import RegistrationAPIView, AuthorizationAPIView, ConfirmUserAPIView
from users.views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import GoogleLoginRedirectAPIView, GoogleLoginCallbackAPIView

urlpatterns = [
    path('registration/', RegistrationAPIView.as_view()),
    path('authorization/', AuthorizationAPIView.as_view()),
    path('confirm/', ConfirmUserAPIView.as_view()),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/google/', GoogleLoginRedirectAPIView.as_view(), name='google_login'),
    path('auth/google/callback/', GoogleLoginCallbackAPIView.as_view(), name='google_callback'),
]