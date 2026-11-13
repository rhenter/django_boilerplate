import logging

logger = logging.getLogger(__name__)


def validate_register_user_with_onesignal(user, result):
    # Parse error messages for better handling
    error_messages = []
    for error in result['errors']:
        if isinstance(error, dict):
            error_messages.append(error.get('title', str(error)))
        else:
            error_messages.append(str(error))

    acceptable_errors = any(
        'already exists' in msg.lower() or 'duplicate' in msg.lower()
        for msg in error_messages
    )

    if acceptable_errors:
        if not user.onesignal_id:
            onesignal_id = result.get('identity', {}).get('onesignal_id') or result.get('id')
            if onesignal_id:
                user.onesignal_id = onesignal_id
                user.save(update_fields=['onesignal_id'])
                logger.info(f'Saved OneSignal ID {onesignal_id} for existing user {user.id}')

        logger.info(f'User {user.id} already registered with OneSignal')
        return {
            'success': True,
            'result': result,
            'error_type': 'acceptable',
            'error_message': '; '.join(error_messages),
            'user_id': user.id
        }

    logger.warning(f'User {user.id} OneSignal registration returned errors: {error_messages}')
    return {
        'success': False,
        'result': result,
        'error_type': 'api_error',
        'error_message': '; '.join(error_messages),
        'user_id': user.id
    }
