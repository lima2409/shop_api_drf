from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import ConfirmationCode, CustomUser


class RegisterValidateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_email(self, email):
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует!')
        return email

    def validate_phone_number(self, phone_number):
        if phone_number and not phone_number.startswith('+'):
            raise ValidationError('Номер телефона должен начинаться с "+"')
        return phone_number


class AuthValidateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ConfirmationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        user_id = attrs.get('user_id')
        code = attrs.get('code')

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            raise ValidationError('Пользователь не существует!')

        try:
            confirmation_code = ConfirmationCode.objects.get(user=user)
        except ConfirmationCode.DoesNotExist:
            raise ValidationError('Код подтверждения не найден!')

        if confirmation_code.code != code:
            raise ValidationError('Неверный код подтверждения!')

        return attrs