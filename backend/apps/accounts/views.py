from djoser.views import UserViewSet

# Actions anyone can call without logging in; they get the stricter "auth" rate limit.
PUBLIC_ACTIONS = {
    "create",
    "activation",
    "resend_activation",
    "reset_password",
    "reset_password_confirm",
}


class UniFlowUserViewSet(UserViewSet):
    """Djoser's account endpoints under /api/v1/auth/users/, with UniFlow's rate limit."""

    def get_throttles(self):
        if self.action in PUBLIC_ACTIONS:
            self.throttle_scope = "auth"  # 10 requests/minute (REST_FRAMEWORK settings)
        return super().get_throttles()
