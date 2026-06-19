from django.conf import settings


class TailwindPreviewModeMiddleware:
    """Select the local Tailwind preview mode without changing production."""

    cookie_name = "teebusiness_tailwind_mode"
    query_parameter = "tailwind"
    allowed_modes = {"current", "standalone"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        mode = "current"
        requested_mode = None

        if settings.DEBUG:
            cookie_mode = request.COOKIES.get(self.cookie_name)
            if cookie_mode in self.allowed_modes:
                mode = cookie_mode

            requested_mode = request.GET.get(self.query_parameter)
            if requested_mode in self.allowed_modes:
                mode = requested_mode
            elif requested_mode == "reset":
                mode = "current"

        request.tailwind_mode = mode
        response = self.get_response(request)

        if not settings.DEBUG:
            return response

        if requested_mode in self.allowed_modes:
            response.set_cookie(
                self.cookie_name,
                requested_mode,
                max_age=60 * 60 * 8,
                httponly=True,
                samesite="Lax",
            )
        elif requested_mode == "reset":
            response.delete_cookie(self.cookie_name, samesite="Lax")

        return response
