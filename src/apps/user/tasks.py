from celery.utils.log import get_task_logger
from django.apps import apps as django_apps

from django_settings.celery import celery_app as app
from .utils import register_user_with_onesignal
from django_settings.task_utils import task_report


logger = get_task_logger(__name__)


@app.task(name='register_user_with_onesignal')
@task_report(name='register_user_with_onesignal')
def register_user_with_onesignal_task(user_id):
    """Register a user with OneSignal for push notifications"""
    user_model = django_apps.get_model('user', 'User')
    try:
        user = user_model.objects.get(id=user_id)
    except user_model.DoesNotExist:
        logger.error(f"User with ID {user_id} not found for OneSignal registration")
        return {
            'error': f'User with ID {user_id} not found',
            'status': 'failed',
        }

    logger.debug(f"register_user_with_onesignal: User: {user}")

    # Register user with OneSignal using shared utility
    result = register_user_with_onesignal(user)

    return {
        'user': str(user),
        'onesignal_result': result['result'],
        'success': result['success'],
        'error_type': result['error_type'],
        'error_message': result['error_message'],
        'status': 'success' if result['success'] else 'failed'
    }
