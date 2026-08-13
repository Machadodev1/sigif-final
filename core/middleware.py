import threading

_request_local = threading.local()


class CurrentUserMiddleware:
    """Middleware that stores the current request in thread-local storage.

    Signal handlers can call `get_current_request()` or `get_current_user()` to
    inspect the request (including `request.session`) when user is not an
    authenticated Django user.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            _request_local.request = request
        except Exception:
            _request_local.request = None
        response = self.get_response(request)
        try:
            del _request_local.request
        except Exception:
            pass
        return response


def get_current_request():
    return getattr(_request_local, 'request', None)


def get_current_user():
    req = get_current_request()
    if not req:
        return None
    # prefer authenticated user
    user = getattr(req, 'user', None)
    if user and getattr(user, 'is_authenticated', False):
        return user
    # fallback: check session-stored 'logueado' structure used in older views
    try:
        ses = req.session.get('logueado', {}) if hasattr(req, 'session') else {}
        nombre = ses.get('nombre')
        if nombre:
            class _FakeUser:
                def __init__(self, nombre):
                    self.username = nombre
                    self.is_authenticated = True

            return _FakeUser(nombre)
    except Exception:
        pass
    return None
