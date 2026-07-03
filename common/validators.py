from datetime import date
from rest_framework.exceptions import ValidationError


def validate_age_for_product(request):
    """
    Проверяет возраст пользователя по birthdate из JWT-токена.
    Используется при создании Product.
    """
    auth = request.auth  # это payload токена (AccessToken) при JWTAuthentication

    birthdate_str = auth.get('birthdate') if auth else None

    if not birthdate_str:
        raise ValidationError("Укажите дату рождения, чтобы создать продукт.")

    birthdate = date.fromisoformat(birthdate_str)
    today = date.today()
    age = today.year - birthdate.year - (
        (today.month, today.day) < (birthdate.month, birthdate.day)
    )

    if age < 18:
        raise ValidationError("Вам должно быть 18 лет, чтобы создать продукт.")