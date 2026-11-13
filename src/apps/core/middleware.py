from django.conf import settings
from django.http import JsonResponse
from django.middleware.csrf import CsrfViewMiddleware
from django.utils.cache import patch_vary_headers

from .audit_context import request_audit_ids, reset_audit_context, set_audit_context
from apps.platform_access.routing import is_platform_path


class PlatformBrowserMiddleware:
    """Explicit per-surface origin policy; existing customer CORS stays compatible."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_platform = is_platform_path(request.path)
        is_account_support = request.path.startswith('/v1/support/account/')
        if not (is_platform or is_account_support):
            return self.get_response(request)
        request_id, correlation_id = request_audit_ids(request)
        request.audit_request_id = request_id
        request.audit_correlation_id = correlation_id
        context_token = set_audit_context(request_id=request_id, correlation_id=correlation_id)
        if not is_platform:
            try:
                return self.get_response(request)
            finally:
                reset_audit_context(context_token)
        origin = request.headers.get('Origin')
        allowed = settings.PLATFORM_ALLOWED_ORIGINS
        response = None
        if origin and origin not in allowed:
            response = JsonResponse({'detail': 'Origin is not allowed.'}, status=403)
        elif request.method == 'OPTIONS':
            response = JsonResponse({})
        elif request.method not in ('GET', 'HEAD'):
            # Enforce CSRF explicitly: APIView otherwise exempts its dispatch.
            check = CsrfViewMiddleware(lambda req: None)
            check.process_request(request)
            failure = check.process_view(request, lambda req: None, (), {})
            if failure:
                response = JsonResponse({'detail': 'CSRF verification failed.'}, status=403)
        try:
            if response is None:
                response = self.get_response(request)
        finally:
            reset_audit_context(context_token)
        # Error responses need the same policy so trusted browsers can read/recover.
        for header in tuple(response.headers):
            if header.lower().startswith('access-control-'):
                del response[header]
        if origin in allowed:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, X-CSRFToken'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, DELETE, OPTIONS'
            patch_vary_headers(response, ('Origin',))
        if not response.get('Cache-Control', '').startswith('public,'):
            response['Cache-Control'] = 'no-store'
        return response
