import logging
from typing import Dict, Any, Optional
from apps.core.integrations.push_notification import PushNotification
from apps.core.integrations.push_notification.validation import validate_register_user_with_onesignal

logger = logging.getLogger(__name__)

def register_user_with_onesignal(user) -> Dict[str, Any]:
    """
    Register a user with OneSignal for push notifications.

    This is a shared utility function used by both the management command
    and the Celery task to avoid code duplication.

    Args:
        user: User instance to register

    Returns:
        Dict containing registration result with standardized format:
        {
            'success': bool,
            'result': dict or None,
            'error_type': str or None,
            'error_message': str or None,
            'user_id': int
        }
    """
    try:
        push_notification = PushNotification()
        result = push_notification.register_user(user)

        if result and 'errors' not in result:
            # Extract and save the OneSignal ID if present
            onesignal_id = result.get('identity', {}).get('onesignal_id') or result.get('id')
            if onesignal_id:
                user.onesignal_id = onesignal_id
                user.save(update_fields=['onesignal_id'])
                logger.info(f'Successfully registered user {user.id} with OneSignal ID: {onesignal_id}')
            else:
                logger.info(f'Successfully registered user {user.id} with OneSignal (no ID returned)')

            return {
                'success': True,
                'result': result,
                'error_type': None,
                'error_message': None,
                'user_id': user.id
            }
        elif result and 'errors' in result:
           return validate_register_user_with_onesignal(user, result)
        else:
            logger.error(f'Failed to register user {user.id} with OneSignal - no result returned')
            return {
                'success': False,
                'result': None,
                'error_type': 'no_result',
                'error_message': 'No result returned from OneSignal API',
                'user_id': user.id
            }

    except Exception as e:
        logger.error(f'Exception while registering user {user.id} with OneSignal: {e}')
        return {
            'success': False,
            'result': None,
            'error_type': 'exception',
            'error_message': str(e),
            'user_id': user.id
        }
