import threading

_request_local = threading.local()

from django.conf import settings


class SecurityHeadersMiddleware:
    """Aplica de forma explícita cabeceras de seguridad HTTP (CSP incluidas).

    Refuerza las opciones definidas en settings.py para que las respuestas
    lleven siempre la política de seguridad de contenido, incluso si el
    header no es añadido por otra vía.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        debug = getattr(settings, 'DEBUG', False)

        headers = {
            'X-Content-Type-Options': 'nosniff',
            'Referrer-Policy': 'same-origin',
            'X-Frame-Options': 'SAMEORIGIN' if debug else 'DENY',
        }

        script = getattr(
            settings,
            'CSP_SCRIPT_SRC',
            "'self' 'unsafe-inline'"
        )

        headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            f"script-src {script}; "
            "img-src 'self' data:; "
            "style-src 'self' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
            "connect-src 'self'"
        )

        for key, value in headers.items():
            response.setdefault(key, value)

        return response


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
