from functools import wraps
from rest_framework import status
from rest_framework.response import Response
from utils.ratelimit.ratelimit_helper import RateLimitHelper

def required_all_params(method='GET', params=tuple()):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(instance, request, *arg, **kwargs):
            if method == 'GET':
                data = request.query_params
            else:
                data = request.data
            missing_params = [
                param
                for param in params
                if param not in data
            ]
            if missing_params:
                return Response({
                    'success': False,
                    'message': f'missing params: {", ".join(missing_params)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            return view_func(instance, request, *arg, **kwargs)
        return _wrapped_view
    return decorator

def required_any_params(method='GET', params=tuple()):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(instance, request, *arg, **kwargs):
            if method == 'GET':
                data = request.query_params
            else:
                data = request.data
            matching_params = [
                param
                for param in params
                if param in data
            ]
            if not matching_params:
                return Response({
                    'success': False,
                    'message': f'All of required params are missing: {", ".join(params)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            return view_func(instance, request, *arg, **kwargs)
        return _wrapped_view
    return decorator

def rate_limit(hms=(120, 10, 3)):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(instance, request, *arg, **kwargs):
            if not RateLimitHelper.check_limit(
                    api_path=request.path,
                    api_name=view_func.__name__,
                    user_id=request.user.id,
                    hms=hms,
            ):
                return Response({
                    'success': False,
                    'message': f'request is over rate limit'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            return view_func(instance, request, *arg, **kwargs)
        return _wrapped_view
    return decorator
