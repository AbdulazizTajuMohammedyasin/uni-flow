"""Account API addresses, mounted at /api/v1/auth/ (see config/api_v1.py).

POST users/                    register
POST users/activation/         activate with {uid, token} from the email
POST users/resend_activation/  send the activation email again
Login (jwt/...) arrives in M1.6.
"""

from rest_framework.routers import SimpleRouter

from .views import UniFlowUserViewSet

router = SimpleRouter()
router.register("users", UniFlowUserViewSet, basename="user")

urlpatterns = router.urls
