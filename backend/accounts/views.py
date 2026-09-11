from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout, password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.middleware.csrf import get_token
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    MeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    SignupSerializer,
)

User = get_user_model()


class CsrfView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'detail': get_token(request)})


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user, backend='accounts.auth_backends.EmailBackend')
        return Response(MeSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response({'detail': 'Invalid email or password.'}, status=status.HTTP_400_BAD_REQUEST)
        login(request, user)
        return Response(MeSerializer(user).data)


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response(MeSerializer(request.user).data)


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data['current_password']):
            return Response({'detail': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        # Keep the session valid after the password hash changes (Django
        # rotates the session hash on password change). Explicit backend
        # since AUTHENTICATION_BACKENDS has more than one configured.
        login(request, request.user, backend='accounts.auth_backends.EmailBackend')
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = User.objects.filter(email__iexact=email).first()
        if user is not None:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f'{settings.FRONTEND_URL}/reset-password/{uid}/{token}'
            send_mail(
                subject='Reset your Rebadata password',
                message=(
                    'We received a request to reset your Rebadata password.\n\n'
                    f'Reset it here: {reset_link}\n\n'
                    'If you did not request this, you can safely ignore this email.'
                ),
                from_email=None,
                recipient_list=[email],
                fail_silently=True,
            )

        # Always 200: don't reveal whether an account exists for this email.
        return Response({'detail': 'If an account exists for this email, a reset link has been sent.'})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            uid = force_str(urlsafe_base64_decode(data['uid']))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            user = None

        if user is None or not default_token_generator.check_token(user, data['token']):
            return Response({'detail': 'This reset link is invalid or has expired.'},
                             status=status.HTTP_400_BAD_REQUEST)

        try:
            password_validation.validate_password(data['new_password'], user=user)
        except Exception as exc:  # noqa: BLE001 - surface validator messages
            messages = getattr(exc, 'messages', [str(exc)])
            return Response({'new_password': messages}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(data['new_password'])
        user.save(update_fields=['password'])
        return Response({'detail': 'Your password has been reset. You can now log in.'})
