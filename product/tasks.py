from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def process_new_product(product_id):
    """
    Имитация "тяжёлой" обработки нового товара:
    например, генерация превью, индексация для поиска и т.п.
    """
    from product.models import Product

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return f"Товар с id={product_id} не найден"
    product.processed_at = timezone.now()
    product.save(update_fields=['processed_at'])

    return f"Товар '{product.title}' обработан"

@shared_task
def delete_old_cancelled_orders():
    from product.models import Order

    threshold_date = timezone.now() - timedelta(days=30)
    deleted_count, _ = Order.objects.filter(
        status='cancelled',
        created_at__lt=threshold_date
    ).delete()

    return f"Удалено отменённых заказов: {deleted_count}"

@shared_task
def send_order_confirmation_email(user_email, order_id):
    subject = f'Ваш заказ №{order_id} оформлен'
    message = (
        f'Спасибо за заказ! Номер вашего заказа: {order_id}.\n'
        f'Мы уведомим вас, когда заказ будет отправлен.'
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=False,
    )

    return f"Письмо отправлено на {user_email} по заказу {order_id}"